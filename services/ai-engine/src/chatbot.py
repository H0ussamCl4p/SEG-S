import os
import threading
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Any

load_dotenv()


class RAGChatbot:
    # Bumping the suffix when the embedding model changes forces a fresh
    # collection — the old vectors are incompatible with the new model.
    def __init__(self, index_name: str = "industrial-chatbot-v2"):
        # LLM client is OpenAI-compatible. It targets any such endpoint:
        #   - DeepSeek (cloud):   LLM_API_BASE=https://api.deepseek.com  LLM_MODEL=deepseek-chat  LLM_API_KEY=<key>
        #   - Ollama (local dev): LLM_API_BASE=http://ollama:11434/v1    LLM_MODEL=gemma4:e2b     LLM_API_KEY=ollama
        # OLLAMA_BASE_URL is honored as a fallback for backward compatibility.
        self.llm_base_url = os.getenv("LLM_API_BASE") or os.getenv("OLLAMA_BASE_URL", "https://api.deepseek.com")
        self.llm_model = os.getenv("LLM_MODEL", "deepseek-chat")
        # DEEPSEEK_API_KEY is the conventional name; LLM_API_KEY overrides it. "ollama" is a
        # harmless placeholder so a local Ollama endpoint (which ignores the key) still works.
        self.llm_api_key = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or "ollama"
        # Persist directory is mounted as a volume so the index survives restarts.
        self.persist_dir = os.getenv("CHROMA_PERSIST_DIR", "/app/data/chroma")
        self.default_manuals_dir = os.getenv("DEFAULT_MANUALS_DIR", "/app/data/default_manuals")
        self.index_name = index_name

        os.makedirs(self.persist_dir, exist_ok=True)

        self.embeddings = self._initialize_embeddings()
        self.vector_store = self._initialize_vector_store()
        self.llm = self._initialize_llm()
        self.retriever, self.qa_chain = self._initialize_chain()

        # On a fresh install the Chroma collection is empty. Ingest the bundled
        # public-domain manuals in the background so the API is up immediately;
        # queries before ingestion finishes simply retrieve no context.
        self._maybe_ingest_default_manuals()

    def _initialize_embeddings(self):
        # Multilingual model so non-English questions retrieve relevant English
        # chunks directly, eliminating the LLM translation round-trip.
        return HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    def _initialize_vector_store(self):
        return Chroma(
            collection_name=self.index_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_dir,
        )

    def _initialize_llm(self):
        """Initialize ChatOpenAI against the configured OpenAI-compatible endpoint (DeepSeek in cloud, Ollama locally)."""
        return ChatOpenAI(
            model_name=self.llm_model,
            openai_api_base=self.llm_base_url,
            api_key=self.llm_api_key,
            temperature=0.1,
            max_tokens=1024,
            streaming=True,
        )

    def _initialize_chain(self):
        system_prompt = """
        You are an expert maintenance technician.
        You MUST answer ONLY using the information explicitly present in the provided manual context.

        STRICT RULES:
        - IMPORTANT: You MUST write your final answer in the exact SAME LANGUAGE as the user's original question.
        - Only provide the information requested in the following sections.
        - Do NOT add, infer, or invent any information.
        - If a section is not present in the manual, write "Information not available in the manual" for that section.
        - Do NOT include any extra explanation or steps beyond the requested sections.

        RESPONSE FORMAT (DO NOT CHANGE):
        1. Symptom (ONLY if explicitly stated in the manual)
        2. Possible causes (bullet list, ONLY if explicitly stated in the manual)
        3. Diagnostic procedure (bullet list, ONLY if explicitly stated in the manual)
        4. Maintenance / corrective actions (numbered steps, ONLY if explicitly stated in the manual)
        5. Safety warning (ONLY if explicitly stated in the manual)
        6. Manual reference (section or page if available)

        MANUAL CONTEXT:
        {context}
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

        retriever = self.vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})
        question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
        return retriever, question_answer_chain

    def _maybe_ingest_default_manuals(self):
        try:
            count = self.vector_store._collection.count()
        except Exception as e:
            print(f"⚠️  Could not read Chroma collection count: {e}")
            return

        if count > 0:
            print(f"✓ Chroma collection already has {count} chunks; skipping default manual ingest.")
            return

        if not os.path.isdir(self.default_manuals_dir):
            print(f"⚠️  No default manuals directory at {self.default_manuals_dir}; skipping.")
            return

        pdfs = [f for f in os.listdir(self.default_manuals_dir) if f.lower().endswith(".pdf")]
        if not pdfs:
            print(f"⚠️  No PDFs found in {self.default_manuals_dir}; skipping.")
            return

        print(f"→ Ingesting {len(pdfs)} bundled manual(s) in background: {pdfs}")
        threading.Thread(
            target=self._ingest_default_manuals_worker,
            daemon=True,
        ).start()

    def _ingest_default_manuals_worker(self):
        try:
            self.ingest_data(self.default_manuals_dir, glob_pattern="*.pdf", is_directory=True)
            print("✓ Default manuals ingested.")
        except Exception as e:
            print(f"❌ Background ingest failed: {e}")

    def ingest_data(self, data_path: str, glob_pattern: str = "*.pdf", is_directory: bool = True):
        """Load, split, and add documents to the persistent Chroma collection."""
        if is_directory:
            print(f"Loading documents from directory {data_path} with pattern {glob_pattern}...")
            loader = DirectoryLoader(data_path, glob=glob_pattern, loader_cls=PyPDFLoader)
        else:
            print(f"Loading single document from {data_path}...")
            loader = PyPDFLoader(data_path)

        documents = loader.load()
        print(f"Loaded {len(documents)} documents.")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", ".", " ", ""],
        )
        texts_chunk = text_splitter.split_documents(documents)
        print(f"Created {len(texts_chunk)} chunks.")

        print("Adding to Chroma collection...")
        self.vector_store.add_documents(texts_chunk)
        print("Ingestion complete.")

    def query(self, input_text: str) -> Dict[str, Any]:
        """One-shot RAG query. Multilingual embeddings let us skip the translation pass."""
        try:
            docs = self.retriever.invoke(input_text)
            ans = self.qa_chain.invoke({"input": input_text, "context": docs})
            return {"answer": ans, "context": docs}
        except Exception as e:
            print(f"Error in RAG query: {e}")
            return {"answer": "Error processing request.", "context": []}

    async def stream_query(self, input_text: str):
        """Async generator yielding answer tokens as Gemma produces them."""
        try:
            docs = self.retriever.invoke(input_text)
            async for chunk in self.qa_chain.astream({"input": input_text, "context": docs}):
                if chunk:
                    yield chunk
        except Exception as e:
            print(f"Error in RAG stream_query: {e}")
            yield f"\n[Error: {e}]"


if __name__ == "__main__":
    try:
        chatbot = RAGChatbot()
        response = chatbot.query("The CNC machine motor does not start and the fuses keep blowing.")
        print("Answer:\n", response["answer"])
    except Exception as e:
        print(f"Error: {e}")

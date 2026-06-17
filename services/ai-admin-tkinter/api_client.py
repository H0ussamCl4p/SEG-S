"""
API client for AI Engine communication
Handles all HTTP requests with proper error handling and threading
"""

import requests
import threading
from typing import Callable, Optional, Dict, Any
from config import API_BASE_URL, API_TIMEOUT


class AIEngineClient:
    """Async API client for AI Engine"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        
    def get_model_info(self, callback: Callable, error_callback: Optional[Callable] = None):
        """Fetch model information asynchronously"""
        def fetch():
            try:
                response = requests.get(
                    f"{self.base_url}/api/model-info",
                    timeout=API_TIMEOUT
                )
                response.raise_for_status()
                callback(response.json())
            except Exception as e:
                if error_callback:
                    error_callback(str(e))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def train_model(self, params: Dict[str, Any], callback: Callable, error_callback: Optional[Callable] = None):
        """Train model asynchronously"""
        def train():
            try:
                response = requests.post(
                    f"{self.base_url}/api/train",
                    json=params,
                    timeout=120
                )
                response.raise_for_status()
                callback(response.json())
            except Exception as e:
                if error_callback:
                    error_callback(str(e))
        
        threading.Thread(target=train, daemon=True).start()
    
    def reset_model(self, callback: Callable, error_callback: Optional[Callable] = None):
        """Reset model asynchronously"""
        def reset():
            try:
                response = requests.post(
                    f"{self.base_url}/api/reset-model",
                    timeout=API_TIMEOUT
                )
                response.raise_for_status()
                callback(response.json())
            except Exception as e:
                if error_callback:
                    error_callback(str(e))
        
        threading.Thread(target=reset, daemon=True).start()
    
    def upload_dataset(self, file_path: str, callback: Callable, error_callback: Optional[Callable] = None):
        """Upload CSV/Excel dataset asynchronously"""
        def upload():
            try:
                # Detect MIME type based on file extension
                import os
                file_ext = os.path.splitext(file_path)[1].lower()
                mime_types = {
                    '.csv': 'text/csv',
                    '.xls': 'application/vnd.ms-excel',
                    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                }
                mime_type = mime_types.get(file_ext, 'application/octet-stream')
                
                with open(file_path, 'rb') as f:
                    filename = os.path.basename(file_path)
                    files = {'file': (filename, f, mime_type)}
                    response = requests.post(
                        f"{self.base_url}/api/upload-dataset",
                        files=files,
                        timeout=60
                    )
                    response.raise_for_status()
                    callback(response.json())
            except Exception as e:
                if error_callback:
                    error_callback(str(e))
        
        threading.Thread(target=upload, daemon=True).start()
    
    def check_health(self, callback: Callable, error_callback: Optional[Callable] = None):
        """Check API health"""
        def check():
            try:
                response = requests.get(
                    f"{self.base_url}/health",  # Health might not be under /api, check if needed
                    timeout=5
                )
                response.raise_for_status()
                callback(True)
            except Exception as e:
                if error_callback:
                    error_callback(str(e))
                else:
                    callback(False)
        
        threading.Thread(target=check, daemon=True).start()

    def send_chat_message(self, message: str, callback: Callable, error_callback: Optional[Callable] = None):
        """Send chat message asynchronously"""
        def send():
            try:
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json={"message": message},
                    timeout=60
                )
                response.raise_for_status()
                callback(response.json())
            except Exception as e:
                if error_callback:
                    error_callback(str(e))
        
        threading.Thread(target=send, daemon=True).start()

    def upload_document(self, file_path: str, callback: Callable, error_callback: Optional[Callable] = None):
        """Upload PDF document for chatbot ingestion"""
        def upload():
            try:
                import os
                filename = os.path.basename(file_path)
                with open(file_path, 'rb') as f:
                    files = {'file': (filename, f, 'application/pdf')}
                    # Increase timeout for ingestion
                    response = requests.post(
                        f"{self.base_url}/api/chat/upload",
                        files=files,
                        timeout=300 
                    )
                    response.raise_for_status()
                    callback(response.json())
            except Exception as e:
                self._handle_error(e, error_callback)
        
        threading.Thread(target=upload, daemon=True).start()

    def _handle_error(self, e, error_callback):
        """Extract detailed error message from response if possible"""
        if not error_callback:
            return
            
        msg = str(e)
        # Check if it's an HTTPError with a response
        if isinstance(e, requests.exceptions.HTTPError) and e.response is not None:
            try:
                # Try to get 'detail' from JSON response
                # Only if content-type is json
                content_type = e.response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    error_json = e.response.json()
                    detail = error_json.get('detail')
                    if detail:
                        # Format: "503 Error: Chatbot service not available..."
                        msg = f"{e.response.status_code} Error: {detail}"
            except:
                pass
        
        error_callback(msg)

#!/usr/bin/env python3
"""
AI Admin Dashboard - Modern SaaS-style Tkinter Application
High-performance native GUI with responsive design
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import requests
import threading
import json
from datetime import datetime
import sys
from api_client import AIEngineClient

class ModernScrollableFrame(ttk.Frame):
    """Scrollable frame for responsive layouts"""
    def __init__(self, container, bg='#f8fafc', *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        # Update canvas window width on resize
        self.canvas.bind('<Configure>', self._on_canvas_resize)
    
    def _on_canvas_resize(self, event):
        """Resize scrollable frame to match canvas width"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

class AIAdminDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Admin Dashboard")
        
        # Fully responsive window size
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = int(screen_width * 0.85)
        window_height = int(screen_height * 0.85)
        
        # Center window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(600, 500)
        
        # Make window resizable
        self.root.resizable(True, True)
        
        # Bind resize event to update layout
        self.root.bind('<Configure>', self.on_window_resize)
        
        # Modern color palette (Light SaaS-style)
        self.colors = {
            'bg_dark': '#f8fafc',
            'bg_card': '#ffffff',
            'bg_card_hover': '#f1f5f9',
            'accent': '#6366f1',
            'accent_hover': '#4f46e5',
            'success': '#10b981',
            'warning': '#f59e0b',
            'danger': '#ef4444',
            'text_primary': '#0f172a',
            'text_secondary': '#64748b',
            'border': '#e2e8f0'
        }
        
        self.root.configure(bg=self.colors['bg_dark'])
        
        # API Configuration
        self.api_url = "http://localhost:8000"
        self.client = AIEngineClient(self.api_url)
        
        # Custom fonts
        self.fonts = {
            'title': ('Segoe UI', 32, 'bold'),
            'heading': ('Segoe UI', 18, 'bold'),
            'subheading': ('Segoe UI', 14, 'bold'),
            'body': ('Segoe UI', 11),
            'small': ('Segoe UI', 9),
            'code': ('Consolas', 10)
        }
        
        # Setup styles
        self.setup_styles()
        
        # Create main layout
        self.create_widgets()
        
        # Force initial layout update
        self.root.update_idletasks()
        
        # Load initial data
        self.refresh_model_info()
        
    def setup_styles(self):
        """Configure modern SaaS-style ttk themes"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame styles
        style.configure('TFrame', background=self.colors['bg_dark'])
        style.configure('Card.TFrame', 
                       background=self.colors['bg_card'],
                       relief='flat',
                       borderwidth=0)
        
        # Label styles
        style.configure('Title.TLabel',
                       background=self.colors['bg_dark'],
                       foreground=self.colors['text_primary'],
                       font=self.fonts['title'])
        
        style.configure('Heading.TLabel',
                       background=self.colors['bg_card'],
                       foreground=self.colors['text_primary'],
                       font=self.fonts['heading'])
        
        style.configure('Body.TLabel',
                       background=self.colors['bg_card'],
                       foreground=self.colors['text_secondary'],
                       font=self.fonts['body'])
        
        style.configure('Value.TLabel',
                       background=self.colors['bg_card'],
                       foreground=self.colors['text_primary'],
                       font=self.fonts['subheading'])
        
        style.configure('Status.TLabel',
                       background=self.colors['bg_dark'],
                       foreground=self.colors['text_secondary'],
                       font=self.fonts['small'])
        
        # Button styles - Modern gradient effect
        style.configure('Primary.TButton',
                       background=self.colors['accent'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 12),
                       font=self.fonts['body'])
        
        style.map('Primary.TButton',
                 background=[('active', self.colors['accent_hover']),
                           ('pressed', self.colors['accent_hover'])])
        
        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 12),
                       font=self.fonts['body'])
        
        style.map('Success.TButton',
                 background=[('active', '#059669')])
        
        style.configure('Danger.TButton',
                       background=self.colors['danger'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 12),
                       font=self.fonts['body'])
        
        style.map('Danger.TButton',
                 background=[('active', '#dc2626')])
        
        # Scale styles
        style.configure('Modern.Horizontal.TScale',
                       background=self.colors['bg_card'],
                       troughcolor=self.colors['border'],
                       borderwidth=0,
                       sliderlength=20,
                       sliderrelief='flat')
        
        # Progressbar
        style.configure('Modern.Horizontal.TProgressbar',
                       background=self.colors['accent'],
                       troughcolor=self.colors['border'],
                       borderwidth=0,
                       thickness=6)
        
    def create_widgets(self):
        """Create responsive SaaS-style layout"""
        # Main scrollable container with light theme background
        self.scroll_frame = ModernScrollableFrame(self.root, bg=self.colors['bg_dark'])
        self.scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        main_container = self.scroll_frame.scrollable_frame
        main_container.configure(style='TFrame')
        
        # Store reference for dynamic layout
        self.main_container = main_container
        self.content_frame = None
        
        # Header section
        self.create_header(main_container)
        
        # Create initial layout
        self.create_responsive_layout(main_container)
        
        # Footer
        self.create_footer(main_container)
    
    def on_window_resize(self, event=None):
        """Handle window resize events for responsive layout"""
        if event and event.widget != self.root:
            return
            
        # Get current window size
        width = self.root.winfo_width()
        
        # Determine if we should switch to single column (responsive breakpoint)
        if hasattr(self, 'content_frame') and self.content_frame:
            if width < 900:  # Breakpoint for single column
                self.switch_to_single_column()
            else:
                self.switch_to_two_columns()
    
    def create_responsive_layout(self, parent):
        """Create responsive layout that adapts to window size"""
        # Content grid (responsive 2-column layout)
        if self.content_frame:
            self.content_frame.destroy()
            
        self.content_frame = ttk.Frame(parent)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)
        
        # Determine initial layout based on window size
        width = self.root.winfo_width()
        
        if width < 900:
            self.create_single_column_layout()
        else:
            self.create_two_column_layout()
    
    def create_two_column_layout(self):
        """Create two-column layout for larger screens"""
        if hasattr(self, 'layout_mode') and self.layout_mode == 'two_column':
            return
            
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.layout_mode = 'two_column'
        
        # Left column
        left_column = ttk.Frame(self.content_frame)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.create_model_status_card(left_column)
        self.create_quick_actions_card(left_column)
        self.create_chat_card(left_column)
        
        # Right column
        right_column = ttk.Frame(self.content_frame)
        right_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        self.create_training_card(right_column)
        self.create_dataset_card(right_column)
    
    def create_single_column_layout(self):
        """Create single-column layout for smaller screens"""
        if hasattr(self, 'layout_mode') and self.layout_mode == 'single_column':
            return
            
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.layout_mode = 'single_column'
        
        # Single column
        single_column = ttk.Frame(self.content_frame)
        single_column.pack(fill=tk.BOTH, expand=True)
        
        self.create_model_status_card(single_column)
        self.create_quick_actions_card(single_column)
        self.create_chat_card(single_column)
        self.create_training_card(single_column)
        self.create_dataset_card(single_column)
    
    def switch_to_single_column(self):
        """Switch to single column layout"""
        self.create_single_column_layout()
    
    def switch_to_two_columns(self):
        """Switch to two column layout"""
        self.create_two_column_layout()
        
    def create_header(self, parent):
        """Create modern header with gradient effect"""
        header = ttk.Frame(parent)
        header.pack(fill=tk.X, pady=(0, 30), padx=40)
        
        # Title with icon
        title_frame = ttk.Frame(header)
        title_frame.pack(anchor=tk.W, fill=tk.X)
        
        title = ttk.Label(title_frame, text="🤖 AI Admin", style='Title.TLabel')
        title.pack(side=tk.LEFT, anchor=tk.W)
        
        # Subtitle
        subtitle = ttk.Label(header, 
                           text="Manage your predictive maintenance AI models",
                           font=self.fonts['body'],
                           foreground=self.colors['text_secondary'],
                           background=self.colors['bg_dark'])
        subtitle.pack(anchor=tk.W, pady=(5, 0), fill=tk.X)
        
    def create_model_status_card(self, parent):
        """Modern status card with metrics"""
        card = self.create_card(parent, "📊 Model Status")
        
        # Metrics grid
        metrics = ttk.Frame(card)
        metrics.pack(fill=tk.X, pady=(15, 0))
        
        # Status badge
        self.status_frame = ttk.Frame(metrics, style='Card.TFrame')
        self.status_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 20))
        
        self.status_badge = tk.Label(self.status_frame,
                                     text="● Loading...",
                                     font=self.fonts['body'],
                                     bg=self.colors['bg_card'],
                                     fg=self.colors['warning'],
                                     padx=15,
                                     pady=8)
        self.status_badge.pack()
        
        # Metric cards
        self.create_metric(metrics, "Training Samples", "0", 0, 0)
        self.create_metric(metrics, "Last Trained", "Never", 0, 1)
        self.create_metric(metrics, "N Estimators", "0", 1, 0)
        self.create_metric(metrics, "Contamination", "0.00", 1, 1)
        
    def create_metric(self, parent, label, value, row, col):
        """Create individual metric display"""
        frame = ttk.Frame(parent, style='Card.TFrame')
        frame.grid(row=row, column=col, sticky=tk.EW, padx=10, pady=10)
        parent.columnconfigure(col, weight=1)
        
        # Label
        lbl = ttk.Label(frame, text=label, style='Body.TLabel')
        lbl.pack(anchor=tk.W, pady=(0, 5))
        
        # Value
        val = ttk.Label(frame, text=value, style='Value.TLabel')
        val.pack(anchor=tk.W)
        
        # Store reference
        if label == "Training Samples":
            self.samples_value = val
        elif label == "Last Trained":
            self.trained_value = val
        elif label == "N Estimators":
            self.estimators_value = val
        elif label == "Contamination":
            self.contamination_display = val
            
    def create_quick_actions_card(self, parent):
        """Quick action buttons"""
        card = self.create_card(parent, "⚡ Quick Actions")
        
        btn_frame = ttk.Frame(card)
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        refresh_btn = ttk.Button(btn_frame,
                                text="🔄 Refresh Status",
                                style='Primary.TButton',
                                command=self.refresh_model_info)
        refresh_btn.pack(fill=tk.X, pady=(0, 10))
        
        reset_btn = ttk.Button(btn_frame,
                              text="🗑️ Reset Model",
                              style='Danger.TButton',
                              command=self.reset_model)
        reset_btn.pack(fill=tk.X)
        
    def create_training_card(self, parent):
        """Training configuration card"""
        card = self.create_card(parent, "⚙️ Training Configuration")
        
        # N Estimators
        self.create_slider(card, "N Estimators", 50, 500, 100, 
                          lambda v: self.n_estimators_label.config(text=str(int(float(v)))))
        self.n_estimators_var = self.slider_vars[-1]
        self.n_estimators_label = self.slider_labels[-1]
        
        # Contamination
        self.create_slider(card, "Contamination", 0.01, 0.5, 0.1,
                          lambda v: self.contamination_label.config(text=f"{float(v):.2f}"))
        self.contamination_var = self.slider_vars[-1]
        self.contamination_label = self.slider_labels[-1]
        
        # Random State
        random_frame = ttk.Frame(card, style='Card.TFrame')
        random_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Label(random_frame, text="Random State", style='Body.TLabel').pack(anchor=tk.W)
        
        self.random_state_var = tk.IntVar(value=42)
        random_entry = tk.Entry(random_frame,
                               textvariable=self.random_state_var,
                               font=self.fonts['body'],
                               bg=self.colors['border'],
                               fg=self.colors['text_primary'],
                               relief='flat',
                               insertbackground=self.colors['text_primary'],
                               width=15)
        random_entry.pack(anchor=tk.W, pady=(10, 0), ipady=8, ipadx=10)
        
        # Train button
        train_btn = ttk.Button(card,
                              text="🚀 Train Model",
                              style='Success.TButton',
                              command=self.train_model)
        train_btn.pack(fill=tk.X, pady=(25, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(card,
                                           variable=self.progress_var,
                                           maximum=100,
                                           style='Modern.Horizontal.TProgressbar',
                                           mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(10, 0))
        
    def create_dataset_card(self, parent):
        """Dataset upload card"""
        card = self.create_card(parent, "📁 Dataset Upload")
        
        # File selection
        self.file_path_var = tk.StringVar(value="No file selected")
        
        file_display = tk.Label(card,
                               textvariable=self.file_path_var,
                               font=self.fonts['small'],
                               bg=self.colors['border'],
                               fg=self.colors['text_secondary'],
                               anchor=tk.W,
                               padx=15,
                               pady=12,
                               wraplength=300)
        file_display.pack(fill=tk.X, pady=(15, 15))
        
        # Buttons
        btn_frame = ttk.Frame(card, style='Card.TFrame')
        btn_frame.pack(fill=tk.X)
        
        browse_btn = ttk.Button(btn_frame,
                               text="📂 Browse File",
                               style='Primary.TButton',
                               command=self.browse_file)
        browse_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        upload_btn = ttk.Button(btn_frame,
                               text="⬆️ Upload",
                               style='Success.TButton',
                               command=self.upload_dataset)
        upload_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

    def create_chat_card(self, parent):
        """Chatbot interface card"""
        card = self.create_card(parent, "💬 AI Assistant")
        
        # Chat history
        history_frame = ttk.Frame(card)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.chat_history = tk.Text(history_frame, height=12, width=40, state='disabled', wrap='word',
                                   font=self.fonts['body'], bg=self.colors['bg_dark'], bd=0, padx=10, pady=10)
        self.chat_history.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure tags for styling
        self.chat_history.tag_config("user", foreground=self.colors['accent'], font=self.fonts['subheading'])
        self.chat_history.tag_config("bot", foreground=self.colors['success'], font=self.fonts['subheading'])
        self.chat_history.tag_config("msg", foreground=self.colors['text_primary'])
        
        scrollbar = ttk.Scrollbar(history_frame, command=self.chat_history.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_history['yscrollcommand'] = scrollbar.set
        
        # Input area
        input_frame = ttk.Frame(card)
        input_frame.pack(fill=tk.X)
        
        self.chat_input = ttk.Entry(input_frame, font=self.fonts['body'])
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.chat_input.bind("<Return>", lambda e: self.send_chat_message())
        
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(side=tk.RIGHT)

        upload_btn = ttk.Button(btn_frame, text="📎", width=3, style='Primary.TButton',
                               command=self.upload_chat_document)
        upload_btn.pack(side=tk.LEFT, padx=(5, 5))

        send_btn = ttk.Button(btn_frame, text="Send", style='Primary.TButton',
                             command=self.send_chat_message)
        send_btn.pack(side=tk.LEFT)
        
    def send_chat_message(self):
        """Send message to chatbot"""
        msg = self.chat_input.get().strip()
        if not msg:
            return
            
        self.append_chat_message("You", msg, "user")
        self.chat_input.delete(0, tk.END)
        self.update_status("Sending message...")
        
        def on_success(response):
            answer = response.get('answer', 'No response')
            self.root.after(0, lambda: self.append_chat_message("AI", answer, "bot"))
            self.root.after(0, lambda: self.update_status("✓ Message sent"))
            
        def on_error(error):
            self.root.after(0, lambda: self.append_chat_message("System", f"Error: {error}", "bot"))
            self.root.after(0, lambda: self.update_status("✗ Failed to send message"))
            
        self.client.send_chat_message(msg, on_success, on_error)
        
    def append_chat_message(self, sender, message, tag):
        """Append message to chat history"""
        self.chat_history.configure(state='normal')
        self.chat_history.insert(tk.END, f"{sender}:\n", tag)
        self.chat_history.insert(tk.END, f"{message}\n\n", "msg")
        self.chat_history.configure(state='disabled')
        self.chat_history.see(tk.END)
        
    def upload_chat_document(self):
        """Upload PDF for chatbot"""
        filename = filedialog.askopenfilename(
            title="Select PDF Document",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not filename:
            return
            
        self.update_status("Uploading document...")
        self.append_chat_message("System", f"Uploading {filename}...", "msg")
        
        def on_success(response):
            msg = response.get('message', 'Upload successful')
            self.root.after(0, lambda: self.append_chat_message("System", f"✓ {msg}", "bot"))
            self.root.after(0, lambda: self.update_status("✓ Document uploaded"))
            
        def on_error(error):
            self.root.after(0, lambda: self.append_chat_message("System", f"✗ Upload failed: {error}", "bot"))
            self.root.after(0, lambda: self.update_status("✗ Upload failed"))
            
        self.client.upload_document(filename, on_success, on_error)
        
    def create_card(self, parent, title):
        """Create modern card container"""
        card_container = ttk.Frame(parent, style='TFrame')
        card_container.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        card = tk.Frame(card_container,
                       bg=self.colors['bg_card'],
                       highlightbackground=self.colors['border'],
                       highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Card content with padding
        content = ttk.Frame(card, style='Card.TFrame', padding=25)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(content, text=title, style='Heading.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        return content
        
    def create_slider(self, parent, label, min_val, max_val, default, callback):
        """Create modern slider with label"""
        if not hasattr(self, 'slider_vars'):
            self.slider_vars = []
            self.slider_labels = []
            
        frame = ttk.Frame(parent, style='Card.TFrame')
        frame.pack(fill=tk.X, pady=(15, 0))
        
        # Label and value on same line
        header = ttk.Frame(frame, style='Card.TFrame')
        header.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header, text=label, style='Body.TLabel').pack(side=tk.LEFT)
        
        value_label = ttk.Label(header, 
                               text=str(default if isinstance(default, int) else f"{default:.2f}"),
                               style='Value.TLabel')
        value_label.pack(side=tk.RIGHT)
        self.slider_labels.append(value_label)
        
        # Slider
        var = tk.DoubleVar(value=default)
        self.slider_vars.append(var)
        
        slider = ttk.Scale(frame,
                          from_=min_val,
                          to=max_val,
                          orient=tk.HORIZONTAL,
                          variable=var,
                          style='Modern.Horizontal.TScale',
                          command=callback)
        slider.pack(fill=tk.X)
        
    def create_footer(self, parent):
        """Create footer status bar"""
        footer = ttk.Frame(parent, style='TFrame')
        footer.pack(fill=tk.X, side=tk.BOTTOM, pady=(20, 0), padx=40)
        
        separator = tk.Frame(footer, height=1, bg=self.colors['border'])
        separator.pack(fill=tk.X, pady=(0, 15))
        
        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(footer, 
                          textvariable=self.status_var,
                          style='Status.TLabel')
        status.pack(anchor=tk.W, pady=(0, 20))
        
    def refresh_model_info(self):
        """Fetch and display current model information"""
        def fetch():
            try:
                self.update_status("Fetching model info...")
                response = requests.get(f"{self.api_url}/model-info", timeout=5)
                data = response.json()
                
                self.root.after(0, lambda: self.update_model_display(data))
                self.root.after(0, lambda: self.update_status("✓ Model info updated"))
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"✗ Error: {str(e)}"))
                
        threading.Thread(target=fetch, daemon=True).start()
        
    def update_model_display(self, data):
        """Update model information display"""
        # DEBUG: Print what we received
        print(f"DEBUG update_model_display: {data}")
        
        is_trained = data.get('is_trained', False)
        
        # Update status badge
        if is_trained:
            self.status_badge.config(text="● Model Trained", fg=self.colors['success'])
        else:
            self.status_badge.config(text="● Not Trained", fg=self.colors['warning'])
        
        # Update metrics (API returns 'sample_count')
        samples = data.get('sample_count', data.get('training_samples', 0))
        print(f"DEBUG samples value: {samples}")
        self.samples_value.config(text=f"{samples:,}")
        
        last_trained = data.get('last_trained', 'Never')
        if last_trained and last_trained != 'Never':
            try:
                dt = datetime.fromisoformat(last_trained.replace('Z', '+00:00'))
                last_trained = dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass
        self.trained_value.config(text=last_trained)
        
        # Get parameters from root level (API returns them directly)
        n_est = data.get('n_estimators', 'N/A')
        cont = data.get('contamination', 0)
        print(f"DEBUG n_estimators: {n_est}, contamination: {cont}")
        self.estimators_value.config(text=str(n_est))
        self.contamination_display.config(text=f"{cont:.2f}" if isinstance(cont, (int, float)) else str(cont))
        
    def train_model(self):
        """Train the AI model"""
        def train():
            try:
                self.root.after(0, lambda: self.progress_bar.start(10))
                self.update_status("Training model...")
                
                payload = {
                    'n_estimators': int(self.n_estimators_var.get()),
                    'contamination': float(self.contamination_var.get()),
                    'random_state': int(self.random_state_var.get())
                }
                
                response = requests.post(f"{self.api_url}/train", json=payload, timeout=120)
                result = response.json()
                
                self.root.after(0, lambda: self.progress_bar.stop())
                self.root.after(0, lambda: self.update_status(f"✓ Training complete! Samples: {result.get('training_samples', 0)}"))
                self.root.after(0, self.refresh_model_info)
                
            except Exception as e:
                self.root.after(0, lambda: self.progress_bar.stop())
                self.root.after(0, lambda: self.update_status(f"✗ Training failed: {str(e)}"))
                
        threading.Thread(target=train, daemon=True).start()
        
    def reset_model(self):
        """Reset the AI model"""
        if not messagebox.askyesno("Confirm Reset", "Reset model and delete all training data?"):
            return
            
        def reset():
            try:
                self.update_status("Resetting model...")
                response = requests.post(f"{self.api_url}/reset-model", timeout=10)
                result = response.json()
                
                self.root.after(0, lambda: self.update_status("✓ Model reset successfully"))
                self.root.after(0, self.refresh_model_info)
                
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"✗ Reset failed: {str(e)}"))
                
        threading.Thread(target=reset, daemon=True).start()
        
    def browse_file(self):
        """Open file browser"""
        filename = filedialog.askopenfilename(
            title="Select Dataset File",
            filetypes=[
                ("Data files", "*.csv;*.xls;*.xlsx"),
                ("CSV files", "*.csv"),
                ("Excel files", "*.xls;*.xlsx"),
                ("All files", "*.*")
            ]
        )
        if filename:
            # Show filename only
            display_name = filename.split('/')[-1].split('\\')[-1]
            self.file_path_var.set(display_name)
            self.selected_file = filename
            
    def upload_dataset(self):
        """Upload CSV/Excel file"""
        if not hasattr(self, 'selected_file'):
            messagebox.showwarning("No File", "Please select a file first")
            return
            
        def upload():
            try:
                self.update_status("Uploading dataset...")
                
                # Detect MIME type based on file extension
                import os
                file_ext = os.path.splitext(self.selected_file)[1].lower()
                mime_types = {
                    '.csv': 'text/csv',
                    '.xls': 'application/vnd.ms-excel',
                    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                }
                mime_type = mime_types.get(file_ext, 'application/octet-stream')
                
                print(f"DEBUG: Uploading file: {self.selected_file}")
                print(f"DEBUG: Extension: {file_ext}, MIME: {mime_type}")
                
                with open(self.selected_file, 'rb') as f:
                    filename = os.path.basename(self.selected_file)
                    files = {'file': (filename, f, mime_type)}
                    print(f"DEBUG: Posting to {self.api_url}/upload-dataset")
                    response = requests.post(f"{self.api_url}/upload-dataset", files=files, timeout=60)
                    print(f"DEBUG: Response status: {response.status_code}")
                    print(f"DEBUG: Response text: {response.text[:200]}")
                    response.raise_for_status()
                    result = response.json()
                
                rows = result.get('total_rows', result.get('rows_imported', 0))
                self.root.after(0, lambda: self.update_status(f"✓ Uploaded {rows} rows"))
                self.root.after(0, self.refresh_model_info)
                self.root.after(0, lambda: messagebox.showinfo("Success", f"Dataset uploaded: {rows} rows, {result.get('feature_count', 0)} features"))
                
            except requests.exceptions.HTTPError as e:
                error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                print(f"DEBUG ERROR: {error_msg}")
                self.root.after(0, lambda: self.update_status(f"✗ Upload failed: HTTP {e.response.status_code}"))
                self.root.after(0, lambda: messagebox.showerror("Upload Error", error_msg))
                
        threading.Thread(target=upload, daemon=True).start()
        
    def update_status(self, message):
        """Update status bar"""
        self.status_var.set(message)
    
    def dump_widget_tree(self, widget=None, level=0):
        """Debug function to print widget geometry"""
        if widget is None:
            widget = self.root
            
        indent = '  ' * level
        try:
            info = {
                'mgr': widget.winfo_manager(),
                'x': widget.winfo_x(),
                'y': widget.winfo_y(),
                'w': widget.winfo_width(),
                'h': widget.winfo_height(),
                'class': widget.winfo_class(),
                'name': str(widget).split('.')[-1]
            }
            flags = []
            if info['w'] == 0 or info['h'] == 0: flags.append('ZERO-SIZE')
            if info['x'] < 0 or info['y'] < 0: flags.append('NEG-POS')
            if info['w'] == 1 and info['h'] == 1: flags.append('NOT-MAPPED')
            
            print(f"{indent}{info['name']} [{info['class']}] mgr={info['mgr']} "
                  f"pos=({info['x']},{info['y']}) size=({info['w']}x{info['h']}) "
                  f"{' '.join(flags)}")
        except Exception as e:
            print(f"{indent}{widget}: {e}")

        for child in widget.winfo_children():
            self.dump_widget_tree(child, level+1)


def main():
    root = tk.Tk()
    app = AIAdminDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
    def __init__(self, root):
        self.root = root
        self.root.title("AI Admin Dashboard - IIoT Predictive Maintenance")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1e1e1e')
        
        # API Configuration
        self.api_url = "http://localhost:8000"
        
        # Style configuration
        self.setup_styles()
        
        # Create main layout
        self.create_widgets()
        
        # Load initial data
        self.refresh_model_info()
        
    def setup_styles(self):
        """Configure ttk styles for modern dark theme"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        bg_color = '#1e1e1e'
        fg_color = '#ffffff'
        select_bg = '#0078d4'
        
        style.configure('Title.TLabel', 
                       background=bg_color, 
                       foreground=fg_color, 
                       font=('Segoe UI', 24, 'bold'))
        
        style.configure('Header.TLabel', 
                       background=bg_color, 
                       foreground=fg_color, 
                       font=('Segoe UI', 14, 'bold'))
        
        style.configure('Info.TLabel', 
                       background=bg_color, 
                       foreground='#b0b0b0', 
                       font=('Segoe UI', 10))
        
        style.configure('Value.TLabel', 
                       background=bg_color, 
                       foreground=fg_color, 
                       font=('Segoe UI', 12, 'bold'))
        
        style.configure('Modern.TButton',
                       background=select_bg,
                       foreground=fg_color,
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 10))
        
        style.map('Modern.TButton',
                 background=[('active', '#005a9e')])
        
        style.configure('TFrame', background=bg_color)
        style.configure('Card.TFrame', background='#2d2d2d', relief='raised', borderwidth=2)
        
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        main_container = ttk.Frame(self.root, padding="20")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_container, 
                               text="🤖 AI Model Administration", 
                               style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Top section - Model Status
        self.create_model_status_section(main_container)
        
        # Middle section - Training controls
        self.create_training_section(main_container)
        
        # Bottom section - Dataset upload
        self.create_dataset_section(main_container)
        
        # Status bar
        self.create_status_bar(main_container)
        
    def create_model_status_section(self, parent):
        """Create model status display section"""
        frame = ttk.Frame(parent, style='Card.TFrame', padding="15")
        frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(frame, text="Model Status", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        # Grid for model info
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X)
        
        # Model status
        self.status_label = ttk.Label(info_frame, text="Status: Loading...", style='Info.TLabel')
        self.status_label.grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        
        # Training samples
        self.samples_label = ttk.Label(info_frame, text="Training Samples: -", style='Info.TLabel')
        self.samples_label.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Last trained
        self.trained_label = ttk.Label(info_frame, text="Last Trained: Never", style='Info.TLabel')
        self.trained_label.grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        
        # Model parameters
        self.params_label = ttk.Label(info_frame, text="Parameters: Loading...", style='Info.TLabel')
        self.params_label.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Refresh button
        refresh_btn = ttk.Button(frame, 
                                text="🔄 Refresh", 
                                style='Modern.TButton',
                                command=self.refresh_model_info)
        refresh_btn.pack(anchor=tk.E, pady=(10, 0))
        
    def create_training_section(self, parent):
        """Create model training controls section"""
        frame = ttk.Frame(parent, style='Card.TFrame', padding="15")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        ttk.Label(frame, text="Training Configuration", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        # Training parameters
        params_frame = ttk.Frame(frame)
        params_frame.pack(fill=tk.X, pady=(0, 15))
        
        # N Estimators
        ttk.Label(params_frame, text="N Estimators:", style='Info.TLabel').grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.n_estimators_var = tk.IntVar(value=100)
        n_estimators_scale = ttk.Scale(params_frame, 
                                       from_=50, to=500, 
                                       orient=tk.HORIZONTAL,
                                       variable=self.n_estimators_var,
                                       length=200)
        n_estimators_scale.grid(row=0, column=1, padx=10, pady=5)
        self.n_estimators_label = ttk.Label(params_frame, text="100", style='Value.TLabel')
        self.n_estimators_label.grid(row=0, column=2, padx=10, pady=5)
        n_estimators_scale.configure(command=lambda v: self.n_estimators_label.config(text=str(int(float(v)))))
        
        # Contamination
        ttk.Label(params_frame, text="Contamination:", style='Info.TLabel').grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.contamination_var = tk.DoubleVar(value=0.1)
        contamination_scale = ttk.Scale(params_frame, 
                                       from_=0.01, to=0.5, 
                                       orient=tk.HORIZONTAL,
                                       variable=self.contamination_var,
                                       length=200)
        contamination_scale.grid(row=1, column=1, padx=10, pady=5)
        self.contamination_label = ttk.Label(params_frame, text="0.10", style='Value.TLabel')
        self.contamination_label.grid(row=1, column=2, padx=10, pady=5)
        contamination_scale.configure(command=lambda v: self.contamination_label.config(text=f"{float(v):.2f}"))
        
        # Random State
        ttk.Label(params_frame, text="Random State:", style='Info.TLabel').grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.random_state_var = tk.IntVar(value=42)
        random_state_entry = ttk.Entry(params_frame, textvariable=self.random_state_var, width=10)
        random_state_entry.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Training buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        train_btn = ttk.Button(btn_frame, 
                              text="🚀 Train Model", 
                              style='Modern.TButton',
                              command=self.train_model)
        train_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        reset_btn = ttk.Button(btn_frame, 
                              text="🔄 Reset Model", 
                              style='Modern.TButton',
                              command=self.reset_model)
        reset_btn.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(frame, 
                                           variable=self.progress_var, 
                                           maximum=100,
                                           mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(15, 0))
        
    def create_dataset_section(self, parent):
        """Create dataset upload section"""
        frame = ttk.Frame(parent, style='Card.TFrame', padding="15")
        frame.pack(fill=tk.X)
        
        ttk.Label(frame, text="Dataset Management", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        # File selection
        file_frame = ttk.Frame(frame)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.file_path_var = tk.StringVar(value="No file selected")
        file_label = ttk.Label(file_frame, textvariable=self.file_path_var, style='Info.TLabel')
        file_label.pack(side=tk.LEFT, padx=(0, 10))
        
        browse_btn = ttk.Button(file_frame, 
                               text="📁 Browse CSV", 
                               style='Modern.TButton',
                               command=self.browse_file)
        browse_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        upload_btn = ttk.Button(file_frame, 
                               text="⬆️ Upload Dataset", 
                               style='Modern.TButton',
                               command=self.upload_dataset)
        upload_btn.pack(side=tk.LEFT)
        
    def create_status_bar(self, parent):
        """Create status bar at bottom"""
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(parent, 
                              textvariable=self.status_var, 
                              style='Info.TLabel',
                              relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
    def refresh_model_info(self):
        """Fetch and display current model information"""
        def fetch():
            try:
                self.update_status("Fetching model info...")
                response = requests.get(f"{self.api_url}/model-info", timeout=5)
                data = response.json()
                
                # Update UI in main thread
                self.root.after(0, lambda: self.update_model_display(data))
                self.root.after(0, lambda: self.update_status("Model info updated"))
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"Error: {str(e)}"))
                
        threading.Thread(target=fetch, daemon=True).start()
        
    def update_model_display(self, data):
        """Update model information display"""
        # DEBUG: Print what we received
        print(f"DEBUG update_model_display (second): {data}")
        
        status = "✅ Trained" if data.get('is_trained') else "⚠️ Not Trained"
        self.status_label.config(text=f"Status: {status}")
        
        # Get sample count (API returns 'sample_count')
        samples = data.get('sample_count', data.get('training_samples', 0))
        print(f"DEBUG samples value: {samples}")
        self.samples_label.config(text=f"Training Samples: {samples:,}")
        
        last_trained = data.get('last_trained', 'Never')
        if last_trained and last_trained != 'Never':
            # Format timestamp
            try:
                dt = datetime.fromisoformat(last_trained.replace('Z', '+00:00'))
                last_trained = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        self.trained_label.config(text=f"Last Trained: {last_trained}")
        
        # Get parameters from root level (API returns them directly)
        n_est = data.get('n_estimators', data.get('model_params', {}).get('n_estimators', 'N/A'))
        cont = data.get('contamination', data.get('model_params', {}).get('contamination', 'N/A'))
        params_text = f"n_estimators={n_est}, contamination={cont}"
        self.params_label.config(text=f"Parameters: {params_text}")
        
    def train_model(self):
        """Train the AI model with current parameters"""
        def train():
            try:
                self.root.after(0, lambda: self.progress_bar.start(10))
                self.update_status("Training model...")
                
                payload = {
                    'n_estimators': int(self.n_estimators_var.get()),
                    'contamination': float(self.contamination_var.get()),
                    'random_state': int(self.random_state_var.get())
                }
                
                response = requests.post(f"{self.api_url}/train", 
                                       json=payload, 
                                       timeout=120)
                result = response.json()
                
                self.root.after(0, lambda: self.progress_bar.stop())
                self.root.after(0, lambda: self.update_status(f"✅ Training complete! Samples: {result.get('training_samples', 0)}"))
                self.root.after(0, self.refresh_model_info)
                self.root.after(0, lambda: messagebox.showinfo("Success", "Model trained successfully!"))
                
            except Exception as e:
                self.root.after(0, lambda: self.progress_bar.stop())
                self.root.after(0, lambda: self.update_status(f"❌ Training failed: {str(e)}"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Training failed: {str(e)}"))
                
        threading.Thread(target=train, daemon=True).start()
        
    def reset_model(self):
        """Reset the AI model"""
        if not messagebox.askyesno("Confirm Reset", "Are you sure you want to reset the model? This will delete all training data."):
            return
            
        def reset():
            try:
                self.update_status("Resetting model...")
                response = requests.post(f"{self.api_url}/reset-model", timeout=10)
                result = response.json()
                
                self.root.after(0, lambda: self.update_status("✅ Model reset successfully"))
                self.root.after(0, self.refresh_model_info)
                self.root.after(0, lambda: messagebox.showinfo("Success", result.get('message', 'Model reset!')))
                
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"❌ Reset failed: {str(e)}"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Reset failed: {str(e)}"))
                
        threading.Thread(target=reset, daemon=True).start()
        
    def browse_file(self):
        """Open file browser to select dataset file"""
        filename = filedialog.askopenfilename(
            title="Select Dataset File",
            filetypes=[
                ("Data files", "*.csv;*.xls;*.xlsx"),
                ("CSV files", "*.csv"),
                ("Excel files", "*.xls;*.xlsx"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.file_path_var.set(filename)
            
    def upload_dataset(self):
        """Upload selected CSV/Excel file to AI engine"""
        file_path = self.file_path_var.get()
        if file_path == "No file selected" or not file_path:
            messagebox.showwarning("No File", "Please select a file first")
            return
            
        def upload():
            try:
                self.update_status("Uploading dataset...")
                
                # Detect MIME type based on file extension
                import os
                file_ext = os.path.splitext(file_path)[1].lower()
                mime_types = {
                    '.csv': 'text/csv',
                    '.xls': 'application/vnd.ms-excel',
                    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                }
                mime_type = mime_types.get(file_ext, 'application/octet-stream')
                
                print(f"DEBUG: Uploading file: {file_path}")
                print(f"DEBUG: Extension: {file_ext}, MIME: {mime_type}")
                
                with open(file_path, 'rb') as f:
                    filename = os.path.basename(file_path)
                    files = {'file': (filename, f, mime_type)}
                    print(f"DEBUG: Posting to {self.api_url}/upload-dataset")
                    response = requests.post(f"{self.api_url}/upload-dataset", 
                                           files=files, 
                                           timeout=60)
                    print(f"DEBUG: Response status: {response.status_code}")
                    print(f"DEBUG: Response text: {response.text[:200]}")
                    response.raise_for_status()
                    result = response.json()
                
                rows = result.get('total_rows', result.get('rows_imported', 0))
                features = result.get('feature_count', 0)
                self.root.after(0, lambda: self.update_status(f"✅ Dataset uploaded: {rows} rows, {features} features"))
                self.root.after(0, self.refresh_model_info)
                self.root.after(0, lambda: messagebox.showinfo("Success", f"Uploaded {rows} rows with {features} features successfully!"))
                
            except requests.exceptions.HTTPError as e:
                error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                print(f"DEBUG ERROR: {error_msg}")
                self.root.after(0, lambda: self.update_status(f"❌ Upload failed: HTTP {e.response.status_code}"))
                self.root.after(0, lambda: messagebox.showerror("Upload Error", error_msg))
                
        threading.Thread(target=upload, daemon=True).start()
        
    def update_status(self, message):
        """Update status bar message"""
        self.status_var.set(message)


def main():
    root = tk.Tk()
    app = AIAdminDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()

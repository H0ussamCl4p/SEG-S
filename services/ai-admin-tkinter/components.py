"""
UI Components - Sections of the dashboard
Modular components for better organization
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from config import COLORS, FONTS, PROGRESS_BAR_INTERVAL
from widgets import Card, MetricDisplay, StatusBadge, ModernSlider


class ModelStatusSection:
    """Model status display with metrics"""
    
    def __init__(self, parent):
        self.card = Card(parent, "📊 Model Status")
        
        # Metrics container
        metrics = ttk.Frame(self.card.content, style='Card.TFrame')
        metrics.pack(fill=tk.X, pady=(15, 0))
        
        # Status badge
        status_frame = ttk.Frame(metrics, style='Card.TFrame')
        status_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 20))
        
        self.status_badge = StatusBadge(status_frame)
        self.status_badge.pack()
        
        # Metrics grid
        self.samples = MetricDisplay(metrics, "Training Samples", "0")
        self.samples.grid(row=1, column=0, sticky=tk.EW, padx=10, pady=10)
        
        self.last_trained = MetricDisplay(metrics, "Last Trained", "Never")
        self.last_trained.grid(row=1, column=1, sticky=tk.EW, padx=10, pady=10)
        
        self.n_estimators = MetricDisplay(metrics, "N Estimators", "0")
        self.n_estimators.grid(row=2, column=0, sticky=tk.EW, padx=10, pady=10)
        
        self.contamination = MetricDisplay(metrics, "Contamination", "0.00")
        self.contamination.grid(row=2, column=1, sticky=tk.EW, padx=10, pady=10)
        
        metrics.columnconfigure(0, weight=1)
        metrics.columnconfigure(1, weight=1)
    
    def update_status(self, data: dict):
        """Update all metrics from API data"""
        is_trained = data.get('is_trained', False)
        self.status_badge.set_status(is_trained)
        
        # API returns 'sample_count', not 'training_samples'
        samples = data.get('sample_count', data.get('training_samples', 0))
        self.samples.set_value(f"{samples:,}")
        
        last_trained = data.get('last_trained', 'Never')
        if last_trained and last_trained != 'Never':
            try:
                dt = datetime.fromisoformat(last_trained.replace('Z', '+00:00'))
                last_trained = dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass
        self.last_trained.set_value(last_trained)
        
        # API returns parameters at root level, not in model_params
        n_est = data.get('n_estimators', 'N/A')
        cont = data.get('contamination', 0)
        self.n_estimators.set_value(str(n_est))
        self.contamination.set_value(f"{cont:.2f}" if isinstance(cont, (int, float)) else "0.00")


class QuickActionsSection:
    """Quick action buttons"""
    
    def __init__(self, parent, refresh_callback, reset_callback):
        self.card = Card(parent, "⚡ Quick Actions")
        
        btn_frame = ttk.Frame(self.card.content, style='Card.TFrame')
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(
            btn_frame,
            text="🔄 Refresh Status",
            style='Primary.TButton',
            command=refresh_callback
        ).pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(
            btn_frame,
            text="🗑️ Reset Model",
            style='Danger.TButton',
            command=reset_callback
        ).pack(fill=tk.X)


class TrainingConfigSection:
    """Training parameter configuration"""
    
    def __init__(self, parent, train_callback):
        self.card = Card(parent, "⚙️ Training Configuration")
        
        # N Estimators slider
        self.n_estimators = ModernSlider(
            self.card.content,
            "N Estimators",
            50, 500, 100,
            is_int=True
        )
        self.n_estimators.pack(fill=tk.X, pady=(15, 0))
        
        # Contamination slider
        self.contamination = ModernSlider(
            self.card.content,
            "Contamination",
            0.01, 0.5, 0.1,
            is_int=False
        )
        self.contamination.pack(fill=tk.X, pady=(20, 0))
        
        # Random State input
        random_frame = ttk.Frame(self.card.content, style='Card.TFrame')
        random_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Label(random_frame, text="Random State", style='Body.TLabel').pack(anchor=tk.W)
        
        self.random_state = tk.IntVar(value=42)
        random_entry = tk.Entry(
            random_frame,
            textvariable=self.random_state,
            font=FONTS['body'],
            bg=COLORS['border'],
            fg=COLORS['text_primary'],
            relief='flat',
            insertbackground=COLORS['text_primary'],
            width=15
        )
        random_entry.pack(anchor=tk.W, pady=(10, 0), ipady=8, ipadx=10)
        
        # Train button
        ttk.Button(
            self.card.content,
            text="🚀 Train Model",
            style='Success.TButton',
            command=train_callback
        ).pack(fill=tk.X, pady=(25, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.card.content,
            variable=self.progress_var,
            maximum=100,
            style='Modern.Horizontal.TProgressbar',
            mode='indeterminate'
        )
        self.progress_bar.pack(fill=tk.X, pady=(10, 0))
    
    def get_params(self) -> dict:
        """Get training parameters"""
        return {
            'n_estimators': int(self.n_estimators.get_value()),
            'contamination': float(self.contamination.get_value()),
            'random_state': int(self.random_state.get())
        }
    
    def start_progress(self):
        """Start progress animation"""
        self.progress_bar.start(PROGRESS_BAR_INTERVAL)
    
    def stop_progress(self):
        """Stop progress animation"""
        self.progress_bar.stop()


class DatasetUploadSection:
    """Dataset file upload"""
    
    def __init__(self, parent, upload_callback):
        self.card = Card(parent, "📁 Dataset Upload")
        self.upload_callback = upload_callback
        self.selected_file = None
        
        # File path display
        self.file_path_var = tk.StringVar(value="No file selected")
        
        file_display = tk.Label(
            self.card.content,
            textvariable=self.file_path_var,
            font=FONTS['small'],
            bg=COLORS['border'],
            fg=COLORS['text_secondary'],
            anchor=tk.W,
            padx=15,
            pady=12,
            wraplength=300
        )
        file_display.pack(fill=tk.X, pady=(15, 15))
        
        # Buttons
        btn_frame = ttk.Frame(self.card.content, style='Card.TFrame')
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(
            btn_frame,
            text="📂 Browse File",
            style='Primary.TButton',
            command=self.browse_file
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(
            btn_frame,
            text="⬆️ Upload",
            style='Success.TButton',
            command=self.upload_file
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
    
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
            display_name = filename.split('/')[-1].split('\\')[-1]
            self.file_path_var.set(display_name)
            self.selected_file = filename
    
    def upload_file(self):
        """Trigger upload callback"""
        if not self.selected_file:
            messagebox.showwarning("No File", "Please select a CSV file first")
            return
        self.upload_callback(self.selected_file)


class KnowledgeBaseSection:
    """Knowledge Base Management Section"""
    
    def __init__(self, parent, upload_callback):
        self.card = Card(parent, "📚 Knowledge Base")
        self.upload_callback = upload_callback
        
        # Info text
        info_frame = ttk.Frame(self.card.content, style='Card.TFrame')
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(
            info_frame,
            text="Upload technical manuals (PDF) to train the AI Assistant.",
            font=FONTS['body'],
            wraplength=300
        ).pack(anchor=tk.W)
        
        # Status area
        self.status_text = tk.Text(
            self.card.content,
            height=6,
            width=40,
            state='disabled',
            font=FONTS['small'],
            bg=COLORS['bg_dark'],
            bd=0,
            padx=10,
            pady=10
        )
        self.status_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Upload button
        ttk.Button(
            self.card.content, 
            text="📄 Upload Manual (PDF)", 
            style='Primary.TButton',
            command=self.upload_document
        ).pack(fill=tk.X)
        
    def upload_document(self):
        """Handle upload button"""
        filename = filedialog.askopenfilename(
            title="Select PDF Document",
            filetypes=[("PDF files", "*.pdf")]
        )
        if filename:
            self.upload_callback(filename)

    def log_message(self, message):
        """Append message to status log"""
        self.status_text.configure(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.status_text.configure(state='disabled')

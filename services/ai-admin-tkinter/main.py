#!/usr/bin/env python3
"""
AI Admin Dashboard - Modern SaaS-style Tkinter Application
Clean, modular architecture with high performance
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import (
    WINDOW_SCALE, MIN_WIDTH, MIN_HEIGHT, RESPONSIVE_BREAKPOINT,
    COLORS, FONTS
)
from styles import AppStyle
from widgets import ModernScrollableFrame
from components import (
    ModelStatusSection,
    QuickActionsSection,
    TrainingConfigSection,
    TrainingConfigSection,
    DatasetUploadSection,
    KnowledgeBaseSection
)
from api_client import AIEngineClient


class AIAdminDashboard:
    """Main application class"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("AI Admin Dashboard")
        
        # Initialize API client
        self.api = AIEngineClient()
        
        # Configure window
        self._setup_window()
        
        # Apply styles
        AppStyle()
        
        # Build UI
        self._create_layout()
        
        # Load initial data
        self.root.after(100, self.refresh_model_info)
    
    def _setup_window(self):
        """Configure window size and behavior"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = int(screen_width * WINDOW_SCALE)
        window_height = int(screen_height * WINDOW_SCALE)
        
        # Center window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.resizable(True, True)
        self.root.configure(bg=COLORS['bg_dark'])
        
        # Bind resize for responsive layout
        self.root.bind('<Configure>', self._on_window_resize)
    
    def _create_layout(self):
        """Build main UI layout"""
        # Scrollable container
        self.scroll_frame = ModernScrollableFrame(self.root, bg=COLORS['bg_dark'])
        self.scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        main_container = self.scroll_frame.scrollable_frame
        main_container.configure(style='TFrame')
        
        # Header
        self._create_header(main_container)
        
        # Content area
        self.content_frame = ttk.Frame(main_container)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)
        
        # Initial layout
        self.layout_mode = None
        self._create_responsive_layout()
        
        # Footer
        self._create_footer(main_container)
        
        # Force initial layout
        self.root.update_idletasks()
    
    def _create_header(self, parent):
        """Create header section"""
        header = ttk.Frame(parent)
        header.pack(fill=tk.X, pady=(0, 30), padx=40)
        
        title_frame = ttk.Frame(header)
        title_frame.pack(anchor=tk.W, fill=tk.X)
        
        ttk.Label(
            title_frame,
            text="🤖 AI Admin",
            style='Title.TLabel'
        ).pack(side=tk.LEFT, anchor=tk.W)
        
        ttk.Label(
            header,
            text="Manage your predictive maintenance AI models",
            font=FONTS['body'],
            foreground=COLORS['text_secondary'],
            background=COLORS['bg_dark']
        ).pack(anchor=tk.W, pady=(5, 0), fill=tk.X)
    
    def _create_footer(self, parent):
        """Create footer status bar"""
        footer = ttk.Frame(parent, style='TFrame')
        footer.pack(fill=tk.X, side=tk.BOTTOM, pady=(20, 0), padx=40)
        
        separator = tk.Frame(footer, height=1, bg=COLORS['border'])
        separator.pack(fill=tk.X, pady=(0, 15))
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(
            footer,
            textvariable=self.status_var,
            style='Status.TLabel'
        ).pack(anchor=tk.W, pady=(0, 20))
    
    def _create_responsive_layout(self):
        """Create responsive column layout"""
        # Clear existing
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        width = self.root.winfo_width()
        
        if width < RESPONSIVE_BREAKPOINT:
            self._create_single_column()
        else:
            self._create_two_columns()
    
    def _create_two_columns(self):
        """Two-column layout for larger screens"""
        if self.layout_mode == 'two_column':
            return
        self.layout_mode = 'two_column'
        
        # Clear
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Left column
        left = ttk.Frame(self.content_frame)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.model_status = ModelStatusSection(left)
        self.model_status.card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.quick_actions = QuickActionsSection(
            left,
            self.refresh_model_info,
            self.reset_model
        )
        self.quick_actions.card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.quick_actions.card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.kb_section = KnowledgeBaseSection(
            left, 
            self._upload_kb_doc
        )
        self.kb_section.card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Right column
        right = ttk.Frame(self.content_frame)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        self.training_config = TrainingConfigSection(right, self.train_model)
        self.training_config.card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.dataset_upload = DatasetUploadSection(right, self.upload_dataset)
        self.dataset_upload.card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
    
    def _create_single_column(self):
        """Single-column layout for smaller screens"""
        if self.layout_mode == 'single_column':
            return
        self.layout_mode = 'single_column'
        
        # Clear
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Single column
        column = ttk.Frame(self.content_frame)
        column.pack(fill=tk.BOTH, expand=True)
        
        self.model_status = ModelStatusSection(column)
        self.model_status.card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.quick_actions = QuickActionsSection(
            column,
            self.refresh_model_info,
            self.reset_model
        )
        self.quick_actions.card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.quick_actions.card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.kb_section = KnowledgeBaseSection(
            column, 
            self._upload_kb_doc
        )
        self.kb_section.card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.training_config = TrainingConfigSection(column, self.train_model)
        self.training_config.card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.dataset_upload = DatasetUploadSection(column, self.upload_dataset)
        self.dataset_upload.card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
    
    def _on_window_resize(self, event=None):
        """Handle window resize for responsive layout"""
        if event and event.widget != self.root:
            return
        
        width = self.root.winfo_width()
        
        if width < RESPONSIVE_BREAKPOINT and self.layout_mode != 'single_column':
            self._create_single_column()
        elif width >= RESPONSIVE_BREAKPOINT and self.layout_mode != 'two_column':
            self._create_two_columns()
    
    # API Interaction Methods
    
    def refresh_model_info(self):
        """Fetch and display model information"""
        self._update_status("Fetching model info...")
        
        def on_success(data):
            self.root.after(0, lambda: self.model_status.update_status(data))
            self.root.after(0, lambda: self._update_status("✓ Model info updated"))
        
        def on_error(error):
            self.root.after(0, lambda: self._update_status(f"✗ Error: {error}"))
        
        self.api.get_model_info(on_success, on_error)
    
    def train_model(self):
        """Train the AI model"""
        params = self.training_config.get_params()
        
        self.training_config.start_progress()
        self._update_status("Training model...")
        
        def on_success(result):
            self.root.after(0, lambda: self.training_config.stop_progress())
            samples = result.get('training_samples', 0)
            self.root.after(0, lambda: self._update_status(f"✓ Training complete! Samples: {samples}"))
            self.root.after(0, self.refresh_model_info)
        
        def on_error(error):
            self.root.after(0, lambda: self.training_config.stop_progress())
            self.root.after(0, lambda: self._update_status(f"✗ Training failed: {error}"))
        
        self.api.train_model(params, on_success, on_error)
    
    def reset_model(self):
        """Reset the AI model"""
        if not messagebox.askyesno("Confirm Reset", "Reset model and delete all training data?"):
            return
        
        self._update_status("Resetting model...")
        
        def on_success(result):
            self.root.after(0, lambda: self._update_status("✓ Model reset successfully"))
            self.root.after(0, self.refresh_model_info)
        
        def on_error(error):
            self.root.after(0, lambda: self._update_status(f"✗ Reset failed: {error}"))
        
        self.api.reset_model(on_success, on_error)
    
    def upload_dataset(self, file_path: str):
        """Upload CSV dataset"""
        self._update_status("Uploading dataset...")
        
        def on_success(result):
            rows = result.get('rows_imported', 0)
            self.root.after(0, lambda: self._update_status(f"✓ Uploaded {rows} rows"))
            self.root.after(0, self.refresh_model_info)
        
        def on_error(error):
            self.root.after(0, lambda: self._update_status(f"✗ Upload failed: {error}"))
        
        self.api.upload_dataset(file_path, on_success, on_error)
    
        self.api.upload_dataset(file_path, on_success, on_error)
    
    def _upload_kb_doc(self, file_path: str):
        """Upload document for knowledge base"""
        self._update_status(f"Uploading {file_path}...")
        self.kb_section.log_message(f"Uploading {file_path}...")
        
        def on_success(response):
            msg = response.get('message', 'Upload successful')
            self.root.after(0, lambda: self.kb_section.log_message(f"✓ {msg}"))
            self.root.after(0, lambda: self._update_status("✓ Document uploaded"))
        
        def on_error(error):
            self.root.after(0, lambda: self.kb_section.log_message(f"✗ Upload failed: {error}"))
            self.root.after(0, lambda: self._update_status(f"✗ Upload failed: {error}"))
            
        self.api.upload_document(file_path, on_success, on_error)

    def _update_status(self, message: str):
        """Update footer status message"""
        self.status_var.set(message)


def main():
    """Application entry point"""
    root = tk.Tk()
    app = AIAdminDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()

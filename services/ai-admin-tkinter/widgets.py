"""
Custom widgets and components
Reusable UI elements for consistent design
"""

import tkinter as tk
from tkinter import ttk
from config import COLORS, SCROLL_SPEED


class ModernScrollableFrame(ttk.Frame):
    """High-performance scrollable frame with proper resizing"""
    
    def __init__(self, container, bg=COLORS['bg_dark'], *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        # Create canvas with proper background
        self.canvas = tk.Canvas(
            self,
            bg=bg,
            highlightthickness=0,
            bd=0
        )
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )
        
        # Scrollable frame
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Configure scroll region on content change
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Create window in canvas
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw"
        )
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel scrolling
        self.canvas.bind_all(
            "<MouseWheel>",
            lambda e: self.canvas.yview_scroll(int(-1*(e.delta/SCROLL_SPEED)), "units")
        )
        
        # Responsive width adjustment
        self.canvas.bind('<Configure>', self._on_canvas_resize)
    
    def _on_canvas_resize(self, event):
        """Adjust scrollable frame width to match canvas"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)


class Card(tk.Frame):
    """Modern card component with border and padding"""
    
    def __init__(self, parent, title: str = "", **kwargs):
        # Outer container for border effect
        super().__init__(
            parent,
            bg=COLORS['bg_card'],
            highlightbackground=COLORS['border'],
            highlightthickness=1
        )
        
        # Inner content frame with padding
        self.content = ttk.Frame(self, style='Card.TFrame', padding=25)
        self.content.pack(fill=tk.BOTH, expand=True)
        
        # Optional title
        if title:
            ttk.Label(
                self.content,
                text=title,
                style='Heading.TLabel'
            ).pack(anchor=tk.W, pady=(0, 10))
    
    def add_widget(self, widget):
        """Add widget to card content"""
        widget.pack(in_=self.content)
        return widget


class MetricDisplay(ttk.Frame):
    """Metric card showing label and value"""
    
    def __init__(self, parent, label: str, initial_value: str = "0"):
        super().__init__(parent, style='Card.TFrame')
        
        # Label
        ttk.Label(
            self,
            text=label,
            style='Body.TLabel'
        ).pack(anchor=tk.W, pady=(0, 5))
        
        # Value
        self.value_label = ttk.Label(
            self,
            text=initial_value,
            style='Value.TLabel'
        )
        self.value_label.pack(anchor=tk.W)
    
    def set_value(self, value: str):
        """Update metric value"""
        self.value_label.config(text=value)


class StatusBadge(tk.Label):
    """Status indicator with color-coded badges"""
    
    def __init__(self, parent):
        super().__init__(
            parent,
            text="● Loading...",
            bg=COLORS['bg_card'],
            fg=COLORS['warning'],
            font=('Segoe UI', 11),
            padx=15,
            pady=8
        )
    
    def set_status(self, trained: bool):
        """Update status badge"""
        if trained:
            self.config(text="● Model Trained", fg=COLORS['success'])
        else:
            self.config(text="● Not Trained", fg=COLORS['warning'])


class ModernSlider(ttk.Frame):
    """Slider with label and real-time value display"""
    
    def __init__(self, parent, label: str, min_val: float, max_val: float, 
                 default: float, is_int: bool = False):
        super().__init__(parent, style='Card.TFrame')
        
        self.is_int = is_int
        
        # Header with label and value
        header = ttk.Frame(self, style='Card.TFrame')
        header.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header, text=label, style='Body.TLabel').pack(side=tk.LEFT)
        
        self.value_label = ttk.Label(
            header,
            text=str(int(default)) if is_int else f"{default:.2f}",
            style='Value.TLabel'
        )
        self.value_label.pack(side=tk.RIGHT)
        
        # Slider
        self.var = tk.DoubleVar(value=default)
        slider = ttk.Scale(
            self,
            from_=min_val,
            to=max_val,
            orient=tk.HORIZONTAL,
            variable=self.var,
            style='Modern.Horizontal.TScale',
            command=self._on_change
        )
        slider.pack(fill=tk.X)
    
    def _on_change(self, value):
        """Update value display on slider change"""
        val = float(value)
        if self.is_int:
            self.value_label.config(text=str(int(val)))
        else:
            self.value_label.config(text=f"{val:.2f}")
    
    def get_value(self):
        """Get current slider value"""
        val = self.var.get()
        return int(val) if self.is_int else val

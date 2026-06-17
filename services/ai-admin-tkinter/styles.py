"""
Styling configuration for ttk widgets
Centralized theme management
"""

from tkinter import ttk
from config import COLORS, FONTS


class AppStyle:
    """Configure modern SaaS-style ttk themes"""
    
    def __init__(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self._configure_frames()
        self._configure_labels()
        self._configure_buttons()
        self._configure_scales()
        self._configure_progressbar()
    
    def _configure_frames(self):
        """Configure frame styles"""
        self.style.configure(
            'TFrame',
            background=COLORS['bg_dark']
        )
        
        self.style.configure(
            'Card.TFrame',
            background=COLORS['bg_card'],
            relief='flat',
            borderwidth=0
        )
    
    def _configure_labels(self):
        """Configure label styles"""
        self.style.configure(
            'Title.TLabel',
            background=COLORS['bg_dark'],
            foreground=COLORS['text_primary'],
            font=FONTS['title']
        )
        
        self.style.configure(
            'Heading.TLabel',
            background=COLORS['bg_card'],
            foreground=COLORS['text_primary'],
            font=FONTS['heading']
        )
        
        self.style.configure(
            'Body.TLabel',
            background=COLORS['bg_card'],
            foreground=COLORS['text_secondary'],
            font=FONTS['body']
        )
        
        self.style.configure(
            'Value.TLabel',
            background=COLORS['bg_card'],
            foreground=COLORS['text_primary'],
            font=FONTS['subheading']
        )
        
        self.style.configure(
            'Status.TLabel',
            background=COLORS['bg_dark'],
            foreground=COLORS['text_secondary'],
            font=FONTS['small']
        )
    
    def _configure_buttons(self):
        """Configure button styles"""
        # Primary button
        self.style.configure(
            'Primary.TButton',
            background=COLORS['accent'],
            foreground=COLORS['text_primary'],
            borderwidth=0,
            focuscolor='none',
            padding=(20, 12),
            font=FONTS['body']
        )
        
        self.style.map(
            'Primary.TButton',
            background=[
                ('active', COLORS['accent_hover']),
                ('pressed', COLORS['accent_hover'])
            ]
        )
        
        # Success button
        self.style.configure(
            'Success.TButton',
            background=COLORS['success'],
            foreground=COLORS['text_primary'],
            borderwidth=0,
            focuscolor='none',
            padding=(20, 12),
            font=FONTS['body']
        )
        
        self.style.map(
            'Success.TButton',
            background=[('active', '#059669')]
        )
        
        # Danger button
        self.style.configure(
            'Danger.TButton',
            background=COLORS['danger'],
            foreground=COLORS['text_primary'],
            borderwidth=0,
            focuscolor='none',
            padding=(20, 12),
            font=FONTS['body']
        )
        
        self.style.map(
            'Danger.TButton',
            background=[('active', '#dc2626')]
        )
    
    def _configure_scales(self):
        """Configure slider styles"""
        self.style.configure(
            'Modern.Horizontal.TScale',
            background=COLORS['bg_card'],
            troughcolor=COLORS['border'],
            borderwidth=0,
            sliderlength=20,
            sliderrelief='flat'
        )
    
    def _configure_progressbar(self):
        """Configure progressbar style"""
        self.style.configure(
            'Modern.Horizontal.TProgressbar',
            background=COLORS['accent'],
            troughcolor=COLORS['border'],
            borderwidth=0,
            thickness=6
        )

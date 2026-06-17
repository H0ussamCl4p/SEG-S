"""
Configuration settings for AI Admin Dashboard
"""

# API Configuration
API_BASE_URL = "http://localhost:8000"
API_TIMEOUT = 30

# Window Configuration
WINDOW_SCALE = 0.85
MIN_WIDTH = 600
MIN_HEIGHT = 500
RESPONSIVE_BREAKPOINT = 900

# Color Palette - Light SaaS Theme
COLORS = {
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

# Typography
FONTS = {
    'title': ('Segoe UI', 32, 'bold'),
    'heading': ('Segoe UI', 18, 'bold'),
    'subheading': ('Segoe UI', 14, 'bold'),
    'body': ('Segoe UI', 11),
    'small': ('Segoe UI', 9),
    'code': ('Consolas', 10)
}

# Animation & Performance
UPDATE_INTERVAL = 50  # ms for smooth animations
SCROLL_SPEED = 120  # Mouse wheel scroll units
PROGRESS_BAR_INTERVAL = 10  # ms for progress animation

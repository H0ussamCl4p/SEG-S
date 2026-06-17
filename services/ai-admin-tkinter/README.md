# AI Admin Dashboard - Tkinter Version

High-performance native GUI for AI model management using Python Tkinter.

## Features

- 🚀 **Native Performance** - Tkinter runs as native OS GUI (no browser overhead)
- 📊 **Real-time Model Status** - Live updates of model training status
- ⚙️ **Training Controls** - Configure and train models with sliders
- 📁 **Dataset Upload** - Browse and upload CSV training data
- 🎨 **Modern Dark Theme** - Professional dark UI
- 🔄 **Async Operations** - Non-blocking API calls with threading

## Installation

```powershell
# Navigate to directory
cd services/ai-admin-tkinter

# Install dependencies
pip install -r requirements.txt
```

## Usage

```powershell
# Run the application
python app.py
```

The dashboard will connect to `http://localhost:8000` by default.

## Requirements

- Python 3.10+
- Tkinter (included with Python on Windows)
- Running AI Engine on port 8000

## Advantages over Next.js

1. **Instant Startup** - No build process, launches in <1 second
2. **Lower Memory** - ~50MB vs 200MB+ for browser-based dashboard
3. **Native Feel** - OS-native UI components and behavior
4. **No Dependencies** - Tkinter included with Python, only needs `requests`
5. **Faster Development** - Single Python file vs complex Next.js project
6. **Better for Desktop** - Direct OS integration, no browser required

## Screenshots

The dashboard includes:
- Model status card with training metrics
- Interactive parameter sliders
- File browser for dataset upload
- Progress indicators for async operations
- Status bar with real-time updates

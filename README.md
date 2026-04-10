# Ts2Mp4 — Video Container Converter

A standalone Windows desktop application that converts `.ts` video files to `.mp4` format via FFmpeg remuxing (`-c copy`). No re-encoding — fast, lossless container conversion.

## Features

- 🎯 **Drag-and-Drop Import**: Drag `.ts` files from Windows Explorer directly onto the application
- 📂 **File Dialog Import**: Click "Add Files" to browse and select `.ts` files
- ⚡ **Batch Conversion**: Convert multiple files sequentially with error-and-continue
- 📊 **Real-time Progress**: Per-file and overall progress tracking with responsive GUI
- 📁 **Custom Output Directory**: Choose where to save converted files
- 🔄 **Conflict Resolution**: Overwrite, skip, or auto-rename when output files exist
- 🗑️ **Auto-Delete Source**: Optionally delete source `.ts` files after successful conversion
- ❌ **Cancel Support**: Cancel running conversion at any time with cleanup
- 📋 **Logging**: Automatic error and conversion summary logging
- 🖥️ **Standalone EXE**: Packaged as a Windows executable with PyInstaller

## Prerequisites

- **Python 3.10+** installed and on PATH
- **FFmpeg** binary (`ffmpeg.exe` and `ffprobe.exe`) — [Download](https://ffmpeg.org/download.html)
- **Git** for version control

## Quick Start

### 1. Clone and setup

```powershell
git clone <repo-url>
cd Ts2Mp4
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 2. Verify FFmpeg

```powershell
ffmpeg -version
ffprobe -version
```

If FFmpeg is not on PATH, place binaries in a `ffmpeg/` folder at the project root.

### 3. Run the application

```powershell
python src/main.py
```

## Development

### Run tests

```powershell
# All tests
.venv\Scripts\pytest.exe

# Unit tests only
.venv\Scripts\pytest.exe tests/unit/

# With coverage
.venv\Scripts\pytest.exe --cov=src --cov-report=html
```

### Lint and format

```powershell
.venv\Scripts\ruff.exe check src/ tests/
.venv\Scripts\ruff.exe format src/ tests/
.venv\Scripts\mypy.exe src/
```

### Build executable

```powershell
.venv\Scripts\pyinstaller.exe --onedir --windowed --name Ts2Mp4 --icon assets/icon.ico src/main.py

# Bundle FFmpeg
New-Item -ItemType Directory -Path "dist/Ts2Mp4/ffmpeg" -Force
Copy-Item "ffmpeg/ffmpeg.exe" "dist/Ts2Mp4/ffmpeg/"
Copy-Item "ffmpeg/ffprobe.exe" "dist/Ts2Mp4/ffmpeg/"
```

## Project Structure

```
src/
├── main.py                  # Entry point
├── app.py                   # QApplication setup, FFmpeg check
├── ui/                      # GUI widgets
│   ├── main_window.py       # Main application window
│   ├── file_list_widget.py  # File queue table
│   ├── drop_zone.py         # Drag-and-drop area
│   ├── progress_widget.py   # Progress bar widget
│   └── dialogs.py           # Settings, conflict, summary dialogs
├── core/                    # Business logic
│   ├── converter.py         # FFmpeg subprocess wrapper
│   ├── queue_manager.py     # Batch queue management
│   ├── file_validator.py    # .ts file validation
│   └── progress_parser.py   # FFmpeg progress parsing
├── models/                  # Data models
│   ├── conversion_job.py    # ConversionJob + status enum
│   └── app_settings.py      # Application settings
├── workers/                 # Background threads
│   └── conversion_worker.py # QThread FFmpeg worker
└── utils/                   # Utilities
    ├── logger.py            # Rotating file logger
    └── paths.py             # Path resolution

tests/
├── unit/                    # Unit tests (no external deps)
├── integration/             # Integration tests (needs FFmpeg)
└── conftest.py              # Shared fixtures
```

## Key Commands

| Task | Command |
|------|---------|
| Run app | `python src/main.py` |
| Run tests | `.venv\Scripts\pytest.exe` |
| Lint | `.venv\Scripts\ruff.exe check src/ tests/` |
| Format | `.venv\Scripts\ruff.exe format src/ tests/` |
| Type check | `.venv\Scripts\mypy.exe src/` |
| Build exe | See Build section above |

## License

MIT

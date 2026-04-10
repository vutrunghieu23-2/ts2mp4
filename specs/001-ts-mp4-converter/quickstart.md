# Quickstart: Ts2Mp4 Video Container Converter

**Branch**: `001-ts-mp4-converter` | **Date**: 2026-03-16

## Prerequisites

- **Python 3.10+** installed and available on PATH
- **FFmpeg** binary (`ffmpeg.exe` and `ffprobe.exe`) — download from [ffmpeg.org](https://ffmpeg.org/download.html)
- **Git** for version control

## Setup

### 1. Clone and enter project

```powershell
git clone <repo-url>
cd Ts2Mp4
git checkout 001-ts-mp4-converter
```

### 2. Create virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -e ".[dev]"
```

This installs:
- **PySide6** — Qt 6 GUI framework
- **pytest** — Test runner
- **pytest-qt** — Qt testing utilities
- **ruff** — Linter and formatter
- **mypy** — Type checker
- **pyinstaller** — Packaging tool

### 4. Verify FFmpeg

```powershell
ffmpeg -version
ffprobe -version
```

If FFmpeg is not on PATH, place `ffmpeg.exe` and `ffprobe.exe` in a `ffmpeg/` directory at the project root.

## Development

### Run the application

```powershell
python src/main.py
```

### Run tests

```powershell
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests (requires FFmpeg)
pytest tests/integration/

# With coverage report
pytest --cov=src --cov-report=html
```

### Lint and format

```powershell
# Check lint
ruff check src/ tests/

# Auto-fix lint issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/

# Type checking
mypy src/
```

## Build

### Create standalone executable

```powershell
pyinstaller --onedir --windowed --name Ts2Mp4 src/main.py
```

### Bundle with FFmpeg

After building, copy FFmpeg binaries into the output:

```powershell
New-Item -ItemType Directory -Path "dist/Ts2Mp4/ffmpeg" -Force
Copy-Item "ffmpeg/ffmpeg.exe" "dist/Ts2Mp4/ffmpeg/"
Copy-Item "ffmpeg/ffprobe.exe" "dist/Ts2Mp4/ffmpeg/"
```

### Test the build

```powershell
.\dist\Ts2Mp4\Ts2Mp4.exe
```

## Project Layout

```text
src/
├── main.py                  # Entry point
├── app.py                   # QApplication setup
├── ui/                      # GUI widgets
├── core/                    # Business logic (testable independently)
├── models/                  # Data models
├── workers/                 # QThread workers
└── utils/                   # Utilities (logger, paths)

tests/
├── unit/                    # Unit tests (no external deps)
├── integration/             # Integration tests (needs FFmpeg)
└── conftest.py              # Shared fixtures
```

## Key Commands Reference

| Task | Command |
|------|---------|
| Run app | `python src/main.py` |
| Run all tests | `pytest` |
| Run unit tests | `pytest tests/unit/` |
| Lint check | `ruff check src/ tests/` |
| Format code | `ruff format src/ tests/` |
| Type check | `mypy src/` |
| Build exe | `pyinstaller --onedir --windowed --name Ts2Mp4 src/main.py` |

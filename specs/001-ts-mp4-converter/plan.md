# Implementation Plan: Ts2Mp4 Video Container Converter

**Branch**: `001-ts-mp4-converter` | **Date**: 2026-03-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-ts-mp4-converter/spec.md`

## Summary

Build a standalone Windows desktop application using **Python 3.10+ / PySide6** that converts `.ts` video files to `.mp4` format via **FFmpeg remuxing** (`-c copy`). The application provides a GUI with drag-and-drop file import, button-based import, batch queue management, real-time progress tracking, a cancel button, configurable conflict resolution, optional source file auto-deletion, conversion logging, and automatic stripping of incompatible streams. The app is packaged as a standalone `.exe` via PyInstaller (`--onedir`).

## Technical Context

**Language/Version**: Python 3.10+ (required for modern type hints and PySide6 compatibility)  
**Primary Dependencies**: PySide6 (Qt 6 GUI), subprocess (FFmpeg invocation)  
**Storage**: QSettings or JSON config file in user's app data directory (session/persistent settings)  
**Testing**: pytest + pytest-qt (min 80% coverage on non-GUI business logic)  
**Target Platform**: Windows 10/11 x64 only  
**Project Type**: Desktop application (standalone .exe)  
**Performance Goals**: Conversion speed > 100 MB/s (disk I/O bound), GUI response < 100ms, startup < 3s  
**Constraints**: Memory < 100MB during conversion, package size < 50MB (excl. FFmpeg), remux-only (no re-encoding)  
**Scale/Scope**: Handles 100+ file queues, files > 10GB, single concurrent user

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|:------:|-------|
| I. Remux-Only Conversion | ✅ PASS | FFmpeg `-c copy` only. Auto-strip incompatible streams (teletext, DVB subs) is stream selection, not re-encoding. Primary video/audio incompatibility → error, never re-encode. |
| II. Responsive GUI Architecture | ✅ PASS | PySide6 mandated. All FFmpeg operations on QThread worker. UI updates via Qt signals. Drag-drop/buttons respond < 100ms. |
| III. Defensive Error Handling | ✅ PASS | 30 FRs covering: invalid files rejected at import, FFmpeg errors captured via return code + stderr, disk/permission/exists checks, single file failure doesn't halt queue, cancel + cleanup. |
| IV. Test-Driven Quality | ✅ PASS | pytest + pytest-qt. Unit tests for: file validation, queue management, FFmpeg command construction, progress parsing, path resolution. Integration tests with real FFmpeg. 80% coverage target. |
| V. Minimal Footprint | ✅ PASS | Startup < 3s, memory < 100MB, package < 50MB. Dependencies justified: only PySide6 + stdlib. FFmpeg bundled alongside (not embedded). PyInstaller `--onedir`. |

**Technical Constraints Compliance:**
- Python 3.10+ ✅
- PySide6 (Qt 6) only ✅
- FFmpeg via subprocess ✅
- PyInstaller `--onedir` mode ✅
- Windows 10/11 x64 ✅
- QThread for workers ✅
- QSettings/JSON for config ✅

**Development Workflow Compliance:**
- Feature branches from `main` ✅
- Conventional Commits ✅
- ruff linting + formatting ✅
- Type hints + mypy ✅
- Docstrings on all public APIs ✅

**Gate Result: ALL PASS — proceed to Phase 0.**

## Project Structure

### Documentation (this feature)

```text
specs/001-ts-mp4-converter/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (UI contracts)
├── checklists/          # Quality checklists
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── main.py                    # Application entry point
├── app.py                     # QApplication setup, FFmpeg check
├── ui/
│   ├── __init__.py
│   ├── main_window.py         # MainWindow: layout, toolbar, status bar
│   ├── file_list_widget.py    # QTableWidget-based file queue display
│   ├── drop_zone.py           # Drag-and-drop overlay/area
│   ├── progress_widget.py     # Per-file + overall progress indicators
│   └── dialogs.py             # Settings dialog, conflict policy dialog, about
├── core/
│   ├── __init__.py
│   ├── converter.py           # FFmpegConverter: subprocess wrapper, stream filtering
│   ├── queue_manager.py       # ConversionQueueManager: sequential processing, cancel
│   ├── file_validator.py      # Validate .ts extension, detect duplicates
│   └── progress_parser.py     # Parse FFmpeg stderr/progress output
├── models/
│   ├── __init__.py
│   ├── conversion_job.py      # ConversionJob dataclass with status enum
│   └── app_settings.py        # AppSettings: output dir, conflict policy, auto-delete
├── workers/
│   ├── __init__.py
│   └── conversion_worker.py   # QThread-based worker for FFmpeg execution
└── utils/
    ├── __init__.py
    ├── logger.py              # File logging setup (next to .exe)
    └── paths.py               # Path resolution, FFmpeg binary location

tests/
├── unit/
│   ├── test_converter.py      # FFmpeg command construction, stream selection
│   ├── test_queue_manager.py  # Queue operations, cancel, error handling
│   ├── test_file_validator.py # .ts validation, duplicate detection
│   ├── test_progress_parser.py# Progress output parsing
│   ├── test_conversion_job.py # Status transitions, data model
│   └── test_app_settings.py   # Settings serialization, defaults
├── integration/
│   └── test_conversion_e2e.py # End-to-end conversion with real FFmpeg
├── conftest.py                # Shared fixtures, tmpdir helpers
└── sample_files/              # Small .ts test files for integration tests

pyproject.toml                 # Project metadata, dependencies, ruff/mypy config
README.md                      # Installation, usage, build instructions
```

**Structure Decision**: Single project layout with clear separation between UI (`src/ui/`), business logic (`src/core/`), data models (`src/models/`), Qt workers (`src/workers/`), and utilities (`src/utils/`). This separation enables testing business logic independently from the GUI, satisfying Constitution Principle IV.

## Complexity Tracking

> No constitution violations detected. No justifications required.

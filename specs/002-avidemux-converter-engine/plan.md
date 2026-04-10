# Implementation Plan: Avidemux Converter Engine

**Branch**: `002-avidemux-converter-engine` | **Date**: 2026-03-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-avidemux-converter-engine/spec.md`

## Summary

Add Avidemux CLI (`avidemux_cli.exe`) as an alternative converter engine alongside FFmpeg for `.ts` to `.mp4` remuxing. Introduce a converter engine selector in the Settings dialog (default: Avidemux), implement a common converter protocol, create the `AvidemuxConverter` class, and update the worker to use the selected engine. Avidemux CLI is invoked with `--video-codec copy --audio-codec copy --output-format mp4` for stream copy conversion.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: PySide6 (Qt 6), subprocess (stdlib)
**Storage**: JSON settings file at `%APPDATA%/Ts2Mp4/settings.json`
**Testing**: pytest, pytest-qt
**Target Platform**: Windows 10/11 x64
**Project Type**: Desktop application
**Performance Goals**: Remuxing speed limited by disk I/O only (stream copy)
**Constraints**: <100MB memory, <3s startup, no re-encoding
**Scale/Scope**: Single user, batch processing 100+ files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Remux-Only Conversion | ✅ PASS | Avidemux uses `--video-codec copy --audio-codec copy` (stream copy). No re-encoding. |
| II. Responsive GUI Architecture | ✅ PASS | Avidemux subprocess runs on existing QThread worker. No main thread blocking. |
| III. Defensive Error Handling | ✅ PASS | Missing binary detected before conversion. Process failures caught via return codes. Error details displayed to user. |
| IV. Test-Driven Quality | ✅ PASS | Unit tests for new converter, updated settings tests. Integration tests with sample files. |
| V. Minimal Footprint | ✅ PASS | No new dependencies added. Avidemux binary bundled in `avidemux/` directory (same pattern as FFmpeg). |

**Constitution Violation**: Principle I states "The application MUST convert .ts files to .mp4 exclusively via FFmpeg." This needs amendment to include Avidemux as a permitted conversion tool.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Constitution I mentions "exclusively via FFmpeg" | Avidemux solves FFmpeg's failure on corrupt .ts files | Keeping FFmpeg-only means certain files cannot be converted at all |

## Project Structure

### Documentation (this feature)

```text
specs/002-avidemux-converter-engine/
├── plan.md              # This file
├── research.md          # Phase 0 output - Avidemux CLI syntax, patterns
├── data-model.md        # Phase 1 output - updated entities, protocol
├── quickstart.md        # Phase 1 output - dev setup guide
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── main.py
├── app.py
├── core/
│   ├── __init__.py
│   ├── converter.py           # FFmpegConverter + ConverterProtocol
│   ├── avidemux_converter.py  # NEW: AvidemuxConverter
│   ├── converter_factory.py   # NEW: Factory function
│   ├── queue_manager.py
│   ├── file_validator.py
│   └── progress_parser.py
├── models/
│   ├── __init__.py
│   ├── conversion_job.py
│   └── app_settings.py        # UPDATED: +ConverterEngine enum, +converter_engine field
├── workers/
│   ├── __init__.py
│   └── conversion_worker.py   # UPDATED: Use converter factory
├── ui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── file_list_widget.py
│   ├── drop_zone.py
│   ├── progress_widget.py
│   └── dialogs.py             # UPDATED: +Converter Engine dropdown
└── utils/
    ├── __init__.py
    ├── logger.py
    └── paths.py               # UPDATED: +resolve_avidemux_path()

tests/
├── unit/
│   ├── test_avidemux_converter.py  # NEW
│   ├── test_converter_factory.py   # NEW
│   ├── test_app_settings.py        # UPDATED
│   └── test_converter.py           # Existing (FFmpeg)
└── integration/
    └── test_conversion_e2e.py      # UPDATED: Test both engines
```

**Structure Decision**: Extend existing `src/` structure. New files: `avidemux_converter.py` and `converter_factory.py` in `src/core/`. All other changes are modifications to existing files.

## Implementation Phases

### Phase 1: Settings & Model Layer

**Goal**: Add `ConverterEngine` enum and settings field, ensure persistence and backward compatibility.

**Files**:
- `src/models/app_settings.py` — Add `ConverterEngine` enum, add `converter_engine` field to `AppSettings`, update `to_dict()`, `from_dict()`
- `tests/unit/test_app_settings.py` — Test new field serialization, deserialization, migration (missing key defaults to avidemux)

### Phase 2: Converter Protocol & Factory

**Goal**: Create a common converter interface and factory function.

**Files**:
- `src/core/converter.py` — Add `ConverterProtocol` (Protocol class with `convert()`, `get_process()`, `is_available()` methods). Ensure `FFmpegConverter` conforms.
- `src/core/converter_factory.py` — Factory function `create_converter(engine: ConverterEngine) -> ConverterProtocol`
- `tests/unit/test_converter_factory.py` — Test factory returns correct implementation

### Phase 3: Avidemux Converter Implementation

**Goal**: Implement `AvidemuxConverter` that invokes `avidemux_cli.exe` for remuxing.

**Files**:
- `src/utils/paths.py` — Add `resolve_avidemux_path()` following same pattern as `resolve_ffmpeg_path()`
- `src/core/avidemux_converter.py` — `AvidemuxConverter` class:
  - `build_command()`: Construct `avidemux_cli.exe --load <input> --video-codec copy --audio-codec copy --output-format mp4 --save <output>`
  - `convert()`: Run subprocess, yield output lines, return success/failure
  - `get_process()`: Return current subprocess for cancellation
  - `is_available()`: Check if binary exists
- `tests/unit/test_avidemux_converter.py` — Unit tests for command construction, path resolution, error handling

### Phase 4: Worker Integration

**Goal**: Update `ConversionWorker` to use the selected converter engine.

**Files**:
- `src/workers/conversion_worker.py` — Replace hardcoded `FFmpegConverter()` with factory call based on `settings.converter_engine`. Handle indeterminate progress (`-1.0`) when converter doesn't provide progress output.
- `src/ui/progress_widget.py` — Ensure indeterminate progress bar mode works with `-1.0` value

### Phase 5: Settings UI

**Goal**: Add converter engine dropdown to Settings dialog.

**Files**:
- `src/ui/dialogs.py` — Add `QComboBox` for Converter Engine in `SettingsDialog._setup_ui()`, update `get_settings()` to include the selection
- Ensure dropdown uses `ConverterEngine` enum values

### Phase 6: Testing & Polish

**Goal**: End-to-end testing, edge cases, and final polish.

**Files**:
- `tests/integration/test_conversion_e2e.py` — Add test cases for Avidemux engine (if binary available)
- Manual testing: Missing binary error message, engine switching, batch conversion

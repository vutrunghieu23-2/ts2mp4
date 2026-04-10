# Quickstart: Avidemux Converter Engine

## Prerequisites

- Python 3.10+
- PySide6 installed (`pip install -e .`)
- Avidemux CLI binary placed at `avidemux/avidemux_cli.exe` (relative to project root)
- FFmpeg binary placed at `ffmpeg/ffmpeg.exe` (existing, for FFmpeg engine)

## Key Files to Edit

| File | Change |
|------|--------|
| `src/models/app_settings.py` | Add `ConverterEngine` enum and `converter_engine` field |
| `src/core/converter.py` | Extract `ConverterProtocol`, keep `FFmpegConverter` |
| `src/core/avidemux_converter.py` | **NEW** — `AvidemuxConverter` class |
| `src/utils/paths.py` | Add `resolve_avidemux_path()` |
| `src/workers/conversion_worker.py` | Use `ConverterProtocol` via factory |
| `src/ui/dialogs.py` | Add converter engine dropdown to `SettingsDialog` |
| `tests/unit/test_avidemux_converter.py` | **NEW** — Unit tests |
| `tests/unit/test_app_settings.py` | Update for new field |

## Running

```powershell
# Run app
python -m src.main

# Run tests
pytest tests/ -v

# Run specific test
pytest tests/unit/test_avidemux_converter.py -v
```

## Verifying the Feature

1. Launch the app: `python -m src.main`
2. Open Settings (gear icon or menu)
3. Check "Converter Engine" dropdown — should default to "Avidemux"
4. Add a `.ts` file and click Start
5. Verify conversion completes with indeterminate progress bar
6. Switch to FFmpeg, convert same file — verify FFmpeg behavior unchanged

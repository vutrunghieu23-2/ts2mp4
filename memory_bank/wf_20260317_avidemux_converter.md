# Workflow: Avidemux Converter Engine Implementation (2026-03-17)

## Files Modified

### New Files
- `src/core/avidemux_converter.py` — AvidemuxConverter class (stream copy remuxing)
- `src/core/converter_factory.py` — Factory function to select converter by engine
- `tests/unit/test_avidemux_converter.py` — Unit tests cho AvidemuxConverter 
- `tests/unit/test_converter_factory.py` — Unit tests cho converter factory

### Modified Files
- `src/models/app_settings.py` — Thêm ConverterEngine enum + converter_engine field
- `src/core/converter.py` — Thêm ConverterProtocol + is_available() cho FFmpegConverter
- `src/utils/paths.py` — Thêm resolve_avidemux_path()
- `src/ui/dialogs.py` — Thêm Converter Engine dropdown trong SettingsDialog
- `src/workers/conversion_worker.py` — Dùng factory thay FFmpegConverter, indeterminate progress
- `tests/unit/test_app_settings.py` — Thêm tests cho ConverterEngine

## Thứ tự thực hiện

1. **Settings & Model** (T001-T005): Enum, field, path resolution, tests
2. **Converter Protocol** (T006-T012): Protocol, FFmpeg conform, AvidemuxConverter, factory, tests
3. **Settings UI** (T013-T016): Dropdown trong SettingsDialog
4. **Worker Integration** (T017-T021): Factory trong worker, indeterminate progress
5. **Regression** (T022-T023): Verify FFmpeg unchanged
6. **Error Handling** (T024-T026): Missing binary error
7. **Polish** (T027-T031): Tests, linting

## Kết quả

- 102 tests pass, 3 skipped, 0 failures
- Tất cả task hoàn thành trừ T031 (manual E2E test)

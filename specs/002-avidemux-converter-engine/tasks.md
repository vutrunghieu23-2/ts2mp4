# Tasks: Avidemux Converter Engine

**Input**: Design documents from `/specs/002-avidemux-converter-engine/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: Included — Constitution IV requires test-driven quality.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add foundational model/enum types and path utilities needed by all user stories

- [x] T001 Add `ConverterEngine` enum (values: AVIDEMUX, FFMPEG) to `src/models/app_settings.py`
- [x] T002 Add `converter_engine` field (default: `ConverterEngine.AVIDEMUX`) to `AppSettings` dataclass in `src/models/app_settings.py`, update `to_dict()` and `from_dict()` with backward-compatible deserialization
- [x] T003 [P] Add `resolve_avidemux_path()` function to `src/utils/paths.py` following same search pattern as `resolve_ffmpeg_path()` (bundled `avidemux/avidemux_cli.exe` → system PATH fallback)
- [x] T004 [P] Write unit tests for `ConverterEngine` enum serialization/deserialization and `converter_engine` field migration (missing key defaults to avidemux) in `tests/unit/test_app_settings.py`
- [x] T005 [P] Write unit tests for `resolve_avidemux_path()` in `tests/unit/test_paths.py`

**Checkpoint**: Settings model and path utilities ready. All subsequent phases can use `ConverterEngine` and `resolve_avidemux_path()`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the converter abstraction layer that enables both engines to be used interchangeably

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Add `ConverterProtocol` (Protocol class with `convert()`, `get_process()`, `is_available()` methods) to `src/core/converter.py`
- [x] T007 Ensure existing `FFmpegConverter` in `src/core/converter.py` conforms to `ConverterProtocol` by adding `is_available()` method that checks `self._ffmpeg_path is not None`
- [x] T008 Create `src/core/avidemux_converter.py` with `AvidemuxConverter` class implementing `ConverterProtocol`:
  - `__init__()`: Resolve avidemux path via `resolve_avidemux_path()`
  - `build_command(job)`: Construct `avidemux_cli.exe --load <input> --video-codec copy --audio-codec copy --output-format mp4 --save <output>`
  - `convert(job)`: Run subprocess, yield stdout/stderr lines, return success/failure based on return code and output file existence
  - `get_process()`: Return currently running subprocess
  - `is_available()`: Check if avidemux binary exists
- [x] T009 Create `src/core/converter_factory.py` with factory function `create_converter(engine: ConverterEngine) -> ConverterProtocol` that returns `AvidemuxConverter()` or `FFmpegConverter()` based on engine value
- [x] T010 [P] Write unit tests for `AvidemuxConverter.build_command()` in `tests/unit/test_avidemux_converter.py` — verify correct command-line arguments for a given ConversionJob
- [x] T011 [P] Write unit tests for `AvidemuxConverter.is_available()` in `tests/unit/test_avidemux_converter.py` — test with mocked path (found/not found)
- [x] T012 [P] Write unit tests for `create_converter()` factory in `tests/unit/test_converter_factory.py` — verify returns correct converter type for each engine value

**Checkpoint**: Converter abstraction ready. Both `FFmpegConverter` and `AvidemuxConverter` implement `ConverterProtocol`. Factory function selects the right one.

---

## Phase 3: User Story 1 - Select Converter Engine in Settings (Priority: P1) 🎯 MVP

**Goal**: Users can select between Avidemux and FFmpeg engines in the Settings dialog, with the selection persisted across restarts.

**Independent Test**: Open Settings → verify "Converter Engine" dropdown exists → change selection → close and reopen app → verify selection persisted.

### Implementation for User Story 1

- [x] T013 [US1] Add "Converter Engine" `QGroupBox` with `QComboBox` dropdown (items: "Avidemux (default)", "FFmpeg") to `SettingsDialog._setup_ui()` in `src/ui/dialogs.py`, positioned before the conflict policy group
- [x] T014 [US1] Update `SettingsDialog.get_settings()` in `src/ui/dialogs.py` to include the selected `ConverterEngine` value from the dropdown
- [x] T015 [US1] Update `SettingsDialog.__init__()` in `src/ui/dialogs.py` to set the dropdown's current index based on `self._settings.converter_engine`
- [x] T016 [P] [US1] Write unit test in `tests/unit/test_dialogs.py` verifying the Settings dialog shows "Avidemux" as default selection and correctly returns the selected engine via `get_settings()`

**Checkpoint**: Settings dialog has converter engine dropdown. Default is Avidemux. Selection is persisted via existing `AppSettings.save()`/`load()` mechanism.

---

## Phase 4: User Story 2 - Convert Files Using Avidemux Engine (Priority: P1)

**Goal**: When Avidemux engine is selected, the system uses `avidemux_cli.exe` for conversion with indeterminate progress.

**Independent Test**: Set engine to Avidemux → add `.ts` file → click Start → verify `.mp4` output produced → verify indeterminate progress bar shown during conversion.

### Implementation for User Story 2

- [x] T017 [US2] Update `ConversionWorker.__init__()` in `src/workers/conversion_worker.py` to use `create_converter(settings.converter_engine)` instead of hardcoded `FFmpegConverter()`
- [x] T018 [US2] Update `ConversionWorker.run()` in `src/workers/conversion_worker.py` to emit `progress_updated(job_id, -1.0)` for indeterminate progress when using Avidemux engine (check `settings.converter_engine == ConverterEngine.AVIDEMUX`)
- [x] T019 [US2] Update `ConversionWorker.run()` error message in `src/workers/conversion_worker.py` to use generic "Conversion failed" instead of "FFmpeg conversion failed" (line ~157)
- [x] T020 [US2] Ensure `src/ui/progress_widget.py` handles `-1.0` progress value by showing indeterminate/pulsing progress bar (verify existing implementation or add support)
- [x] T021 [US2] Update `ConversionWorker.cancel()` in `src/workers/conversion_worker.py` to use `self._converter.get_process()` (currently references `self._converter` which is already correct for the protocol)

**Checkpoint**: Avidemux engine fully functional for single and batch conversions with indeterminate progress display.

---

## Phase 5: User Story 3 - Convert Files Using FFmpeg Engine (Priority: P2)

**Goal**: When FFmpeg engine is selected, all existing FFmpeg behavior (two-pass, error tolerance) is preserved with zero regressions.

**Independent Test**: Set engine to FFmpeg → convert `.ts` file → verify same behavior as before (two-pass, retry on corrupt audio).

### Implementation for User Story 3

- [x] T022 [US3] Verify `FFmpegConverter` still works correctly after `ConverterProtocol` addition — run existing tests in `tests/unit/test_converter.py` and ensure all pass
- [x] T023 [US3] Update any test in `tests/unit/test_converter.py` that may need adjustment due to new `is_available()` method on `FFmpegConverter`

**Checkpoint**: FFmpeg engine behavior is identical to before. No regressions.

---

## Phase 6: User Story 4 - Avidemux Binary Not Found (Priority: P2)

**Goal**: When Avidemux is selected but the binary is missing, a clear error message is shown with resolution guidance.

**Independent Test**: Remove/rename `avidemux_cli.exe` → set engine to Avidemux → start conversion → verify error message with clear instructions.

### Implementation for User Story 4

- [x] T024 [US4] Ensure `AvidemuxConverter.convert()` in `src/core/avidemux_converter.py` raises `FileNotFoundError` with message "Avidemux CLI binary not found. Please place avidemux_cli.exe in the avidemux/ directory or switch to FFmpeg engine in Settings." when binary is missing
- [x] T025 [US4] Verify `ConversionWorker` in `src/workers/conversion_worker.py` catches `FileNotFoundError` and emits `file_failed` signal with the error message (existing handler at line ~163 should already work)
- [x] T026 [P] [US4] Write unit test in `tests/unit/test_avidemux_converter.py` verifying `AvidemuxConverter.convert()` raises `FileNotFoundError` with descriptive message when binary path is None

**Checkpoint**: Missing binary scenario handled gracefully with actionable error message.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements across all user stories

- [x] T027 [P] Update `src/app.py` startup check — if selected engine binary is missing, show a warning dialog at startup (not just at conversion time) suggesting to check Settings
- [x] T028 [P] Update `README.md` with Avidemux setup instructions: where to place `avidemux_cli.exe`, how to switch engines in Settings
- [x] T029 Run full test suite `pytest tests/ -v` and verify all tests pass
- [x] T030 Run `ruff check src/ tests/` and fix any linting issues
- [ ] T031 Manual end-to-end test: install fresh → verify Avidemux default → convert file → switch to FFmpeg → convert same file → verify both outputs playable

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001, T002, T003) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 — Settings UI needs `ConverterEngine` enum
- **User Story 2 (Phase 4)**: Depends on Phase 2 + Phase 3 — Worker needs converter factory and settings
- **User Story 3 (Phase 5)**: Depends on Phase 2 — Verify FFmpeg backward compat
- **User Story 4 (Phase 6)**: Depends on Phase 2 — Error handling for missing binary
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 (needs settings to be accessible to select engine)
- **User Story 3 (P2)**: Can start after Phase 2 — Independent regression test
- **User Story 4 (P2)**: Can start after Phase 2 — Independent error handling

### Within Each User Story

- Models/Enums before services/converters
- Converters before worker integration
- Worker integration before UI
- Core implementation before tests (except where TDD specified)

### Parallel Opportunities

- T003, T004, T005 can all run in parallel (different files)
- T010, T011, T012 can all run in parallel (different test files)
- T013-T015 (UI) can run while T010-T012 (tests) are being written
- US3 and US4 can run in parallel after Phase 2

---

## Parallel Example: Phase 2

```bash
# After T006-T009 complete, launch tests in parallel:
Task T010: "Unit test AvidemuxConverter.build_command() in tests/unit/test_avidemux_converter.py"
Task T011: "Unit test AvidemuxConverter.is_available() in tests/unit/test_avidemux_converter.py"
Task T012: "Unit test create_converter() in tests/unit/test_converter_factory.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T012)
3. Complete Phase 3: User Story 1 — Settings UI (T013-T016)
4. Complete Phase 4: User Story 2 — Avidemux conversion (T017-T021)
5. **STOP and VALIDATE**: Test Avidemux conversion end-to-end
6. Deploy if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Settings) → Test independently → Can select engine
3. Add US2 (Avidemux convert) → Test independently → Core feature works (MVP!)
4. Add US3 (FFmpeg compat) → Test independently → No regressions confirmed
5. Add US4 (Error handling) → Test independently → Graceful binary-not-found
6. Polish → Production ready

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Constitution Principle I needs amendment to include Avidemux (tracked in plan.md Complexity Tracking)
- Avidemux CLI command: `avidemux_cli.exe --load <input> --video-codec copy --audio-codec copy --output-format mp4 --save <output>`
- Progress for Avidemux: indeterminate (-1.0 signal)
- No auto-fallback between engines (clarification decision)

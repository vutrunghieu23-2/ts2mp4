# Tasks: Ts2Mp4 Video Container Converter

**Input**: Design documents from `/specs/001-ts-mp4-converter/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included — Constitution Principle IV mandates test-driven quality with 80% coverage on non-GUI business logic.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependency management, and development tooling

- [x] T001 Create project directory structure per plan.md: `src/`, `src/ui/`, `src/core/`, `src/models/`, `src/workers/`, `src/utils/`, `tests/`, `tests/unit/`, `tests/integration/`, `tests/sample_files/`
- [x] T002 Create `pyproject.toml` with project metadata, dependencies (PySide6), dev dependencies (pytest, pytest-qt, ruff, mypy, pyinstaller), and tool configs (ruff line-length=100, mypy strict)
- [x] T003 Create Python virtual environment and install all dependencies via `pip install -e ".[dev]"`
- [x] T004 [P] Create `src/__init__.py`, `src/ui/__init__.py`, `src/core/__init__.py`, `src/models/__init__.py`, `src/workers/__init__.py`, `src/utils/__init__.py` package init files
- [x] T005 [P] Create `.gitignore` with Python, PySide6, PyInstaller, and virtual environment exclusions
- [x] T006 [P] Create `tests/conftest.py` with shared pytest fixtures (tmp_path helpers, sample .ts file fixture)
- [x] T007 Create a small valid `.ts` sample file in `tests/sample_files/sample.ts` for integration testing (can use FFmpeg to generate a 2-second test file)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models, utilities, and infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T008 Implement `ConversionStatus` enum in `src/models/conversion_job.py` with values: PENDING, CONVERTING, COMPLETE, ERROR, CANCELLED, SKIPPED per data-model.md
- [x] T009 Implement `ConversionJob` dataclass in `src/models/conversion_job.py` with all fields per data-model.md: id (UUID), source_path, output_path, status, progress, error_message, file_size, duration, created_at, completed_at
- [x] T010 [P] Implement `ConflictPolicy` enum in `src/models/app_settings.py` with values: ASK, OVERWRITE_ALL, SKIP_ALL, RENAME_ALL
- [x] T011 [P] Implement `AppSettings` dataclass in `src/models/app_settings.py` with fields: output_directory, conflict_policy, auto_delete_source, window_geometry, last_import_directory. Add load/save methods using JSON file at `%APPDATA%/Ts2Mp4/settings.json`
- [x] T012 [P] Implement `FileValidator` in `src/core/file_validator.py` with methods: `validate_ts_file(path) -> bool` (checks .ts extension and file exists), `filter_valid_files(paths) -> tuple[list[Path], list[Path]]` (returns valid and rejected paths), `is_duplicate(path, existing_paths) -> bool`
- [x] T013 [P] Implement `setup_logger()` in `src/utils/logger.py` using Python logging module with RotatingFileHandler (5MB max, 3 backups), log file at `<app_dir>/ts2mp4.log`, format `[%(asctime)s] %(levelname)s: %(message)s`
- [x] T014 [P] Implement `resolve_ffmpeg_path()` and `resolve_output_path(source, settings)` in `src/utils/paths.py` per research.md R5 (check bundled → PATH → error) and data-model.md output path resolution rules
- [x] T015 Write unit tests in `tests/unit/test_conversion_job.py`: test ConversionJob creation, status transitions, UUID uniqueness, output path computation
- [x] T016 [P] Write unit tests in `tests/unit/test_file_validator.py`: test .ts validation, non-.ts rejection, duplicate detection, mixed file filtering
- [x] T017 [P] Write unit tests in `tests/unit/test_app_settings.py`: test default values, JSON serialization/deserialization, load from nonexistent file returns defaults

**Checkpoint**: Foundation ready — all data models, validators, logging, and path utilities are implemented and tested. User story implementation can now begin.

---

## Phase 3: User Story 1 — Drag-and-Drop File Import (Priority: P1) 🎯 MVP

**Goal**: Users can drag `.ts` files from Windows Explorer onto the application window to add them to the conversion queue. Non-`.ts` files are rejected, duplicates are detected.

**Independent Test**: Launch the app, drag one or more `.ts` files onto the window, verify they appear in the queue with correct name, path, and "Pending" status.

### Tests for User Story 1

- [x] T018 [P] [US1] Write unit test in `tests/unit/test_drop_zone.py`: test that `files_dropped` signal is emitted with valid paths, non-.ts files filtered, duplicates rejected

### Implementation for User Story 1

- [x] T019 [US1] Create application entry point `src/main.py` and `src/app.py` with QApplication setup, FFmpeg availability check at startup (show error dialog if not found), and logger initialization
- [x] T020 [US1] Implement `MainWindow` skeleton in `src/ui/main_window.py` with toolbar (Add Files, Remove, Clear All, Settings buttons), output directory bar, file queue area, action buttons (Start, Cancel), and status bar per ui-contracts.md layout
- [x] T021 [US1] Implement `DropZone` widget in `src/ui/drop_zone.py` with `dragEnterEvent`/`dropEvent` handlers per research.md R2, emit `files_dropped(list[str])` signal, show placeholder text when queue is empty
- [x] T022 [US1] Implement `FileListWidget` (QTableWidget) in `src/ui/file_list_widget.py` with columns: #, File Name, Source Path, Status, Progress per ui-contracts.md. Support adding ConversionJob rows, updating status/progress per row
- [x] T023 [US1] Wire DropZone signals to MainWindow: on `files_dropped`, validate via FileValidator, create ConversionJob for each valid file, add to FileListWidget, show rejected files in status bar notification
- [x] T024 [US1] Verify drag-and-drop end-to-end: launch app, drag `.ts` files, confirm queue displays correctly with Pending status

**Checkpoint**: At this point, the application launches with a GUI, accepts drag-and-drop `.ts` files, validates them, shows the queue. User Story 1 is independently testable.

---

## Phase 4: User Story 2 — Single File Conversion (Priority: P1)

**Goal**: Users can convert a single `.ts` file to `.mp4` via remuxing by clicking "Start". The output preserves original quality and saves to the source directory.

**Independent Test**: Add one `.ts` file, click Start, verify `.mp4` output exists with same base name and identical audio/video streams.

### Tests for User Story 2

- [x] T025 [P] [US2] Write unit test in `tests/unit/test_converter.py`: test FFmpeg command construction with `-map 0:v -map 0:a -c copy -f mp4 -movflags +faststart`, test stream selection flags
- [x] T026 [P] [US2] Write unit test in `tests/unit/test_progress_parser.py`: test parsing `time=HH:MM:SS.ms` from FFmpeg stderr, test percentage calculation given known duration
- [x] T027 [P] [US2] Write integration test in `tests/integration/test_conversion_e2e.py`: test actual conversion of `tests/sample_files/sample.ts` to `.mp4` using real FFmpeg, verify output exists and is playable

### Implementation for User Story 2

- [x] T028 [US2] Implement `FFmpegConverter` in `src/core/converter.py` with method `convert(job: ConversionJob) -> bool`: construct FFmpeg command per research.md R1 (`-map 0:v -map 0:a -c copy -f mp4 -movflags +faststart`), run via `subprocess.Popen`, capture stderr, return success/failure
- [x] T029 [US2] Implement `ProgressParser` in `src/core/progress_parser.py`: method `probe_duration(path) -> float` using ffprobe, method `parse_progress(stderr_line, total_duration) -> float|None` extracting `time=` per research.md R4
- [x] T030 [US2] Implement `ConversionWorker` (QThread) in `src/workers/conversion_worker.py` per research.md R3: signals for `file_started`, `progress_updated`, `file_completed`, `file_failed`, `batch_completed`. Single-file execution using FFmpegConverter + ProgressParser
- [x] T031 [US2] Implement `ProgressWidget` in `src/ui/progress_widget.py`: per-file progress bar in the FileListWidget table, indeterminate mode for fast files (< 2 seconds)
- [x] T032 [US2] Wire "Start Conversion" button in MainWindow: disable controls during conversion, create ConversionWorker with queue jobs, connect signals to update FileListWidget status/progress, re-enable controls on completion
- [x] T033 [US2] Add logging: log each conversion start/end/error with file path, file size, and duration to `ts2mp4.log` via logger per FR-029

**Checkpoint**: At this point, single file conversion works end-to-end: add file → click Start → file converts to .mp4 with progress → status shows Complete. User Story 2 is independently testable.

---

## Phase 5: User Story 3 — File Import via Button (Priority: P1)

**Goal**: Users can click "Add Files" to open a file dialog filtered to `.ts` files and add selected files to the existing queue.

**Independent Test**: Click "Add Files", select `.ts` files from dialog, verify they appear in the queue appended to existing files.

### Implementation for User Story 3

- [x] T034 [US3] Implement "Add Files" button handler in MainWindow: open `QFileDialog.getOpenFileNames` with filter `TS Video Files (*.ts)`, pass selected paths through FileValidator, add valid files to FileListWidget, update `last_import_directory` in AppSettings
- [x] T035 [US3] Store and restore `last_import_directory` so file dialog opens in the user's last used folder

**Checkpoint**: Users now have two ways to add files: drag-and-drop (US1) and button import (US3). Both work independently.

---

## Phase 6: User Story 4 — Batch Conversion with Sequential Processing (Priority: P1)

**Goal**: Users can convert multiple files in one operation. Files process sequentially, failures don't halt the queue, and a summary is shown at the end.

**Independent Test**: Queue 5+ files (including one invalid), click Start, verify all valid files convert while invalid is marked Error, and summary dialog appears.

### Tests for User Story 4

- [x] T036 [P] [US4] Write unit test in `tests/unit/test_queue_manager.py`: test sequential processing order, test error-and-continue behavior (one file fails, rest proceed), test batch summary generation (total, completed, failed counts)

### Implementation for User Story 4

- [x] T037 [US4] Implement `ConversionQueueManager` in `src/core/queue_manager.py`: methods `add(path)`, `remove(job_id)`, `clear()`, `get_jobs()`, `get_summary() -> QueueSummary`. Enforce no modification while running (FR-014)
- [x] T038 [US4] Extend `ConversionWorker` to process multiple jobs sequentially: iterate through jobs list, emit `file_started`/`file_completed`/`file_failed` for each, continue on error (FR-007), emit `batch_completed(QueueSummary)` when done
- [x] T039 [US4] Implement batch summary dialog in `src/ui/dialogs.py`: show total, completed (✅), failed (❌), skipped (⏭️) counts per ui-contracts.md. Include "View Log" button that opens `ts2mp4.log`
- [x] T040 [US4] Update status bar with overall progress during batch: "X of Y files complete" per FR-017
- [x] T041 [US4] Log batch session summary to `ts2mp4.log`: timestamp, total files, success count, failure count, individual error details per FR-029

**Checkpoint**: Full batch conversion works: multiple files process sequentially, errors are skipped, summary dialog shows results. User Story 4 is independently testable.

---

## Phase 7: User Story 5 — Output Directory Selection (Priority: P2)

**Goal**: Users can choose a custom output directory via folder picker. Default is same directory as source file.

**Independent Test**: Select custom output directory, convert a file, verify output appears in chosen directory.

### Implementation for User Story 5

- [x] T042 [US5] Implement output directory bar in MainWindow: display current output path (default: "Same as source file"), "Browse..." button opens `QFileDialog.getExistingDirectory`, validate writable directory, update AppSettings
- [x] T043 [US5] Update output path resolution in `src/utils/paths.py` `resolve_output_path()` to respect custom output directory from AppSettings. When custom dir is set, all outputs go there; when not set, output goes to source file's directory
- [x] T044 [US5] Persist output directory in AppSettings JSON so it is remembered across sessions

**Checkpoint**: Users can control where output files are saved. User Story 5 works independently on top of any previous stories.

---

## Phase 8: User Story 6 — Queue Management Before Conversion (Priority: P2)

**Goal**: Users can remove individual files or clear the entire queue before starting conversion. Queue modification is locked during active conversion.

**Independent Test**: Add files, remove some, clear all, re-add, then verify final queue state before converting.

### Implementation for User Story 6

- [x] T045 [US6] Implement "Remove" button handler in MainWindow: remove selected row(s) from FileListWidget and ConversionQueueManager. Only enabled when queue is not running and file(s) are selected
- [x] T046 [US6] Implement "Clear All" button handler in MainWindow: clear all files from FileListWidget and ConversionQueueManager. Only enabled when queue is not running and queue is non-empty
- [x] T047 [US6] Implement right-click context menu on FileListWidget: "Remove" (only when not running), "Open Containing Folder" (opens source directory in Windows Explorer) per ui-contracts.md
- [x] T048 [US6] Implement UI state locking during conversion: disable Add Files, Remove, Clear All, drag-drop when ConversionWorker is running (FR-014). Re-enable on completion/cancellation

**Checkpoint**: Full queue management works before conversion. Users can curate their file list. Queue is locked during conversion. User Story 6 is independently testable.

---

## Phase 9: User Story 7 — Conversion Progress Visibility (Priority: P2)

**Goal**: Users see real-time progress (per-file and overall), error details for failed files, and the GUI remains perfectly responsive throughout conversion.

**Independent Test**: Start batch conversion with large files, verify progress updates in real-time, error details visible, GUI scrollable/resizable during conversion.

### Implementation for User Story 7

- [x] T049 [US7] Enhance `ProgressWidget` in `src/ui/progress_widget.py`: show percentage-based progress bar for large files (> 100MB), indeterminate spinning indicator for small files (< 100MB), update from `progress_updated` signal
- [x] T050 [US7] Implement error detail display: show error tooltip on hover over "Error" status rows in FileListWidget, include specific FFmpeg error message from `file_failed` signal
- [x] T051 [US7] Implement overall progress in status bar: "X of Y complete | Z errors | Elapsed: mm:ss" updated in real-time via `file_completed`/`file_failed` signals
- [x] T052 [US7] Verify GUI responsiveness: ensure MainWindow remains scrollable, resizable, and interactive during active batch conversion by testing with 10+ file queue

**Checkpoint**: Users have full visibility into conversion progress and errors. GUI remains responsive. User Story 7 is independently testable.

---

## Phase 10: User Story 8 — File Preview (Priority: P3)

**Goal**: Users can preview a `.ts` file by double-clicking it in the queue, opening it in the system default media player without blocking conversion.

**Independent Test**: Double-click a queued file, verify it opens in default media player without affecting any running conversion.

### Implementation for User Story 8

- [x] T053 [US8] Implement double-click handler on FileListWidget: on row double-click, open `source_path` with `os.startfile()` (Windows) or `QDesktopServices.openUrl()` to launch system default media player
- [x] T054 [US8] Add "Preview" option to right-click context menu in FileListWidget per ui-contracts.md

**Checkpoint**: File preview works independently. User Story 8 is independently testable.

---

## Phase 11: Cancel, Conflict Policy, and Source File Deletion (Cross-Story Features)

**Purpose**: Implement the three clarification-driven features that enhance the core conversion workflow

### Cancel Functionality (from Clarification Q1)

- [x] T055 Implement cancel behavior in `ConversionWorker`: `cancel()` method sets `_cancelled = True`, terminates active FFmpeg subprocess via `process.terminate()`, cleans up partial output file per FR-026
- [x] T056 Wire "Cancel" button in MainWindow: only enabled during active conversion, calls `worker.cancel()`, on `batch_cancelled` signal show summary with completed/cancelled/pending counts, re-enable all controls
- [x] T057 Write unit test in `tests/unit/test_queue_manager.py`: test cancel behavior — verify partial output cleanup, verify remaining jobs stay PENDING, verify cancellation summary

### Batch Conflict Policy (from Clarification Q2)

- [x] T058 Implement pre-batch conflict detection in `ConversionQueueManager`: scan output paths for existing files before starting, return list of conflicts
- [x] T059 Implement conflict policy dialog in `src/ui/dialogs.py` per ui-contracts.md: radio buttons for Overwrite All / Skip All / Auto-rename All, "Remember this choice" checkbox, Continue/Cancel buttons
- [x] T060 Implement auto-rename logic in `src/utils/paths.py`: `resolve_conflict_path(path) -> Path` appends `_1`, `_2`, etc. until unique filename found
- [x] T061 Apply conflict policy in ConversionWorker before each file: OVERWRITE_ALL → proceed, SKIP_ALL → mark SKIPPED and skip, RENAME_ALL → use resolve_conflict_path, ASK → prompt (single-file mode only)

### Source File Auto-Delete (from Clarification Q3)

- [x] T062 Add auto-delete logic after batch completion in ConversionWorker: if `settings.auto_delete_source` is True, delete source `.ts` files only for jobs with status COMPLETE. Log deletions to log file per FR-028
- [x] T063 Implement Settings dialog in `src/ui/dialogs.py` with "Auto-delete source files after successful conversion" checkbox and "Default conflict policy" dropdown per ui-contracts.md

### Incompatible Stream Handling (from Clarification Q5)

- [x] T064 Implement stream-aware FFmpeg command in `FFmpegConverter`: use `-map 0:v -map 0:a` to select only video/audio streams, log excluded stream types (teletext, DVB subs) per FR-030

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Final quality improvements, packaging, and documentation

- [x] T065 [P] Implement exit confirmation dialog in `src/ui/main_window.py`: override `closeEvent`, show warning dialog per ui-contracts.md if conversion is active, clean up on confirmed exit per FR-022
- [x] T066 [P] Implement notification system in MainWindow status bar: timed messages for file rejection, duplicate detection, successful add, source file deletion per ui-contracts.md notification contracts
- [ ] T067 [P] Add application icon: create or obtain a `.ico` file at `assets/icon.ico`, set as window icon and PyInstaller icon
- [ ] T068 Run `ruff check src/ tests/` and `ruff format src/ tests/` to ensure all code passes linting and formatting
- [ ] T069 Run `mypy src/` to verify type hint coverage on all public functions and methods
- [ ] T070 Run full test suite `pytest --cov=src --cov-report=html` and verify ≥80% coverage on `src/core/` and `src/models/` modules
- [x] T071 Create `README.md` with installation instructions, usage guide, build instructions, and FFmpeg setup per quickstart.md
- [ ] T072 Create PyInstaller spec and build executable: `pyinstaller --onedir --windowed --name Ts2Mp4 --icon assets/icon.ico src/main.py`, then bundle FFmpeg binaries into `dist/Ts2Mp4/ffmpeg/`
- [ ] T073 Test standalone `.exe` on clean Windows 10/11 machine: verify startup, drag-drop, conversion, settings persistence, log file creation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2. Creates the GUI skeleton all other stories build on
- **US2 (Phase 4)**: Depends on Phase 3 (needs MainWindow + FileListWidget)
- **US3 (Phase 5)**: Depends on Phase 3 (needs MainWindow + FileListWidget)
- **US4 (Phase 6)**: Depends on Phase 4 (needs ConversionWorker)
- **US5 (Phase 7)**: Depends on Phase 2 (path utilities). Can parallel with US3/US4
- **US6 (Phase 8)**: Depends on Phase 3 (needs FileListWidget)
- **US7 (Phase 9)**: Depends on Phase 4 (needs ConversionWorker + progress signals)
- **US8 (Phase 10)**: Depends on Phase 3 (needs FileListWidget)
- **Cross-Story (Phase 11)**: Depends on Phase 6 (needs full conversion pipeline)
- **Polish (Phase 12)**: Depends on all previous phases

### User Story Dependencies

- **US1 (Drag-Drop Import)**: Foundation only — *entry point for all other stories*
- **US2 (Single Conversion)**: US1 (needs GUI to trigger conversion)
- **US3 (Button Import)**: US1 (needs MainWindow, shares FileListWidget)
- **US4 (Batch Conversion)**: US2 (extends single conversion to batch)
- **US5 (Output Directory)**: Foundation only (path utilities)
- **US6 (Queue Management)**: US1 (needs FileListWidget with queue)
- **US7 (Progress Visibility)**: US2 (needs conversion worker + progress signals)
- **US8 (File Preview)**: US1 (needs FileListWidget)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before UI integration
- Core implementation before cross-cutting concerns

### Parallel Opportunities

- Phase 1: T004, T005, T006 can all run in parallel
- Phase 2: T010, T011, T012, T013, T14 can run in parallel (different files)
- Phase 2: T015, T016, T017 (test tasks) can run in parallel
- US5, US6, US8 can potentially run in parallel after Phase 3 (different files, minimal overlap)
- Phase 11 conflict/cancel/delete tasks are sequential (shared ConversionWorker)
- Phase 12: T065, T066, T067 can run in parallel

---

## Parallel Example: User Story 2

```text
# Launch all tests for US2 together:
Task: T025 "Unit test for converter in tests/unit/test_converter.py"
Task: T026 "Unit test for progress parser in tests/unit/test_progress_parser.py"
Task: T027 "Integration test for e2e conversion in tests/integration/test_conversion_e2e.py"

# Then implement models/services in parallel:
Task: T028 "FFmpegConverter in src/core/converter.py"
Task: T029 "ProgressParser in src/core/progress_parser.py"

# Then sequential: Worker → UI → Wiring
Task: T030 "ConversionWorker in src/workers/conversion_worker.py"
Task: T031 "ProgressWidget in src/ui/progress_widget.py"
Task: T032 "Wire Start button in MainWindow"
Task: T033 "Add logging"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (Drag-Drop Import)
4. Complete Phase 4: User Story 2 (Single Conversion)
5. **STOP and VALIDATE**: Test end-to-end: drag file → click Start → .mp4 created
6. This is a usable MVP that delivers core value

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Drag-Drop) → GUI skeleton visible
3. Add US2 (Single Conversion) → **MVP!** Core value delivered
4. Add US3 (Button Import) → Alternative import method
5. Add US4 (Batch) → Power user feature
6. Add US5 (Output Dir) → Workflow customization
7. Add US6 (Queue Mgmt) → Full queue control
8. Add US7 (Progress) → Professional UX polish
9. Add US8 (Preview) → Nice-to-have
10. Add Phase 11 (Cancel/Conflict/Delete) → Production-ready features
11. Polish + Package → Distributable `.exe`

### Key Principle

Each story adds value without breaking previous stories. Stop at any checkpoint to validate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Constitution mandates tests before implementation when feasible (Principle IV)
- Commit after each task or logical group using Conventional Commits format
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

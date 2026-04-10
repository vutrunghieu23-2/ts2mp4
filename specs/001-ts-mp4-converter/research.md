# Research: Ts2Mp4 Video Container Converter

**Branch**: `001-ts-mp4-converter` | **Date**: 2026-03-16

## R1: FFmpeg Stream Selection for Incompatible Stream Filtering

**Decision**: Use `-map 0:v -map 0:a -c copy` to explicitly select only video and audio streams during remux, excluding teletext, DVB subtitles, and other incompatible stream types.

**Rationale**: The default `ffmpeg -i input.ts -c copy output.mp4` attempts to copy ALL streams, which fails when the `.ts` contains streams incompatible with the MP4 container (e.g., DVB teletext, DVB subtitles). By explicitly mapping only video (`0:v`) and audio (`0:a`) streams, we ensure a clean remux while discarding unsupported data streams. This is still remuxing (no re-encoding), fully compliant with Constitution Principle I.

**Alternatives considered**:
- `-map 0` (map all streams): Rejected — fails on incompatible streams
- `-map 0:v -map 0:a -map 0:s?` (include subtitles optionally): Rejected — MP4 subtitle support is limited and inconsistent
- Probing streams first with `ffprobe` then selecting compatible ones: Over-engineered for MVP; the simple `-map 0:v -map 0:a` covers 99% of cases

**FFmpeg command template**:
```
ffmpeg -i input.ts -map 0:v -map 0:a -c copy -f mp4 -movflags +faststart output.mp4
```

**Notes**:
- Added `-movflags +faststart` to move the moov atom to the beginning of the file, enabling progressive playback (web/streaming friendly)
- If a `.ts` file has multiple audio tracks, all audio tracks will be included in the output
- If the `.ts` has no valid video or audio streams, FFmpeg will return a non-zero exit code, which we catch as an error

---

## R2: PySide6 Drag-and-Drop Implementation

**Decision**: Implement drag-and-drop by subclassing the main window or a dedicated drop zone widget, overriding `dragEnterEvent` and `dropEvent` to accept file URLs.

**Rationale**: PySide6/Qt provides robust native drag-and-drop support on Windows. The `QDragEnterEvent` and `QDropEvent` handlers receive `QMimeData` with file URLs that can be validated and filtered. This is the standard Qt pattern and works reliably with Windows Explorer.

**Alternatives considered**:
- Using a third-party drag-drop library: Rejected — Qt's built-in support is sufficient and well-documented
- Using `QFileSystemWatcher` with a watched folder: Different use case — doesn't provide drag-drop UX

**Implementation pattern**:
```python
class DropZone(QWidget):
    files_dropped = Signal(list)  # Emits list of valid .ts file paths

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        paths = [url.toLocalFile() for url in event.mimeData().urls()]
        self.files_dropped.emit(paths)
```

---

## R3: QThread Worker Pattern for FFmpeg Subprocess

**Decision**: Use a `QThread`-based worker class that runs FFmpeg via `subprocess.Popen` and emits Qt signals for progress, completion, and error events.

**Rationale**: Constitution Principle II mandates QThread for worker threads (no mixing Python `threading` with Qt's event loop). The `subprocess.Popen` model allows reading FFmpeg's stderr in real-time for progress parsing. Qt signals ensure thread-safe communication between the worker and the GUI.

**Alternatives considered**:
- `threading.Thread` + queue: Rejected by constitution — must not mix with Qt event loop
- `asyncio` + `QEventLoop`: Over-complex, poor PySide6 async support
- `QProcess`: Viable alternative but `subprocess.Popen` provides more control over stderr parsing and process management

**Implementation pattern**:
```python
class ConversionWorker(QThread):
    progress = Signal(str, float)       # (file_path, percentage)
    file_completed = Signal(str)         # file_path
    file_failed = Signal(str, str)       # (file_path, error_message)
    batch_completed = Signal(int, int)   # (success_count, fail_count)

    def __init__(self, jobs: list[ConversionJob], settings: AppSettings):
        super().__init__()
        self._jobs = jobs
        self._settings = settings
        self._cancelled = False

    def cancel(self):
        self._cancelled = True
        # Kill the running FFmpeg subprocess if active
        if self._process:
            self._process.terminate()

    def run(self):
        for job in self._jobs:
            if self._cancelled:
                break
            # Execute FFmpeg and emit signals...
```

**Cancel behavior**: Setting `_cancelled = True` + terminating the active subprocess ensures immediate abort. The worker thread checks `_cancelled` between file processing iterations and exits the loop.

---

## R4: FFmpeg Progress Parsing

**Decision**: Parse FFmpeg's stderr output for `time=HH:MM:SS.ms` patterns to calculate conversion percentage based on known total duration obtained via `ffprobe`.

**Rationale**: FFmpeg writes progress information to stderr during execution. For remuxing, files process extremely fast (often < 1 second for small files), so progress tracking is most meaningful for large files (> 100MB). We first probe the file duration with `ffprobe`, then track the `time=` output during conversion.

**Alternatives considered**:
- `-progress pipe:1` flag: Provides structured progress output but adds complexity for parsing key=value pairs
- `--stats_period` flag: Useful for controlling update frequency but still requires stderr parsing
- No progress at all (indeterminate spinner): Rejected — spec requires progress indicator (FR-018)

**Implementation approach**:
1. Pre-probe: `ffprobe -v quiet -print_format json -show_format input.ts` → extract `duration`
2. During conversion: Read FFmpeg stderr line by line, extract `time=` values
3. Calculate: `progress = current_time / total_duration * 100`
4. For very fast conversions (< 2 seconds), use indeterminate progress indicator instead

**ffprobe command**:
```
ffprobe -v quiet -print_format json -show_format -show_streams input.ts
```

---

## R5: PyInstaller PySide6 Packaging

**Decision**: Use PyInstaller in `--onedir` mode with explicit PySide6 hooks and bundle FFmpeg binary alongside the output directory.

**Rationale**: Constitution mandates `--onedir` mode (Principle V). PyInstaller has mature support for PySide6 via its hooks system. FFmpeg binary is placed alongside the packaged app directory (not inside the frozen bundle) to keep size manageable and allow user-side FFmpeg updates.

**Alternatives considered**:
- `--onefile` mode: Rejected by constitution — slow startup, Windows Defender false positives
- cx_Freeze: Less mature PySide6 support
- Nuitka: Good performance but longer build times and more complex setup

**Build command**:
```
pyinstaller --onedir --windowed --name Ts2Mp4 --icon assets/icon.ico src/main.py
```

**FFmpeg bundling strategy**:
```text
dist/
├── Ts2Mp4/
│   ├── Ts2Mp4.exe
│   ├── _internal/         # PyInstaller internals + PySide6 DLLs
│   ├── ffmpeg/
│   │   ├── ffmpeg.exe
│   │   └── ffprobe.exe
│   └── ts2mp4.log         # Application log file (auto-created)
```

**FFmpeg path resolution**: At runtime, look for FFmpeg in this order:
1. `<app_dir>/ffmpeg/ffmpeg.exe` (bundled)
2. System PATH as fallback
3. If neither found → error dialog with instructions

---

## R6: Application Logging Strategy

**Decision**: Use Python's `logging` module with a `RotatingFileHandler` writing to a log file next to the application executable.

**Rationale**: Spec requires FR-029 (auto-log errors + conversion summary). Python's built-in `logging` is lightweight and well-suited. `RotatingFileHandler` prevents unbounded log growth.

**Configuration**:
- Log file: `<app_dir>/ts2mp4.log`
- Max file size: 5 MB
- Backup count: 3 (keeps `ts2mp4.log`, `ts2mp4.log.1`, `ts2mp4.log.2`, `ts2mp4.log.3`)
- Log level: INFO for conversion summaries, ERROR for failures
- Format: `[%(asctime)s] %(levelname)s: %(message)s`

---

## R7: File Conflict Resolution Policy

**Decision**: Present a conflict policy dialog before batch start when any existing outputs are detected. For single-file mode, prompt individually.

**Rationale**: Spec clarification Q2 mandates a pre-batch policy selection. The system scans the output directory for existing `.mp4` files matching the queue before starting. If conflicts exist, a dialog presents three options: Overwrite All, Skip All, Auto-rename All.

**Auto-rename strategy**: Append `_1`, `_2`, etc. to the base filename until a non-existing path is found:
- `video.ts` → `video.mp4` (exists) → `video_1.mp4` → `video_2.mp4` ...

---

**All NEEDS CLARIFICATION items resolved. Phase 0 complete.**

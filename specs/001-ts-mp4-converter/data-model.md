# Data Model: Ts2Mp4 Video Container Converter

**Branch**: `001-ts-mp4-converter` | **Date**: 2026-03-16

## Entities

### ConversionStatus (Enum)

Represents the lifecycle state of a conversion job.

| Value | Description | Transitions From | Transitions To |
|-------|-------------|------------------|----------------|
| `PENDING` | File queued, awaiting processing | (initial state) | `CONVERTING`, `SKIPPED` |
| `CONVERTING` | FFmpeg subprocess actively running | `PENDING` | `COMPLETE`, `ERROR`, `CANCELLED` |
| `COMPLETE` | Conversion finished successfully | `CONVERTING` | (terminal state) |
| `ERROR` | Conversion failed with error details | `CONVERTING` | (terminal state) |
| `CANCELLED` | User cancelled during conversion | `CONVERTING` | (terminal state) |
| `SKIPPED` | Skipped due to conflict policy (file already exists) | `PENDING` | (terminal state) |

**State Transition Diagram**:

```
                    ┌──────────┐
                    │ PENDING  │
                    └────┬─────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          │          ▼
        ┌──────────┐     │    ┌──────────┐
        │CONVERTING│     │    │ SKIPPED  │
        └────┬─────┘     │    └──────────┘
             │           │
    ┌────────┼────────┐
    │        │        │
    ▼        ▼        ▼
┌────────┐┌─────┐┌─────────┐
│COMPLETE││ERROR││CANCELLED│
└────────┘└─────┘└─────────┘
```

---

### ConversionJob

Represents a single file conversion task in the queue.

| Field | Type | Required | Description | Validation |
|-------|------|:--------:|-------------|------------|
| `id` | `str` (UUID) | ✅ | Unique identifier for the job | Auto-generated, immutable |
| `source_path` | `Path` | ✅ | Absolute path to the source `.ts` file | Must exist, must end with `.ts` |
| `output_path` | `Path` | ✅ | Computed absolute path for the output `.mp4` file | Derived from source_path + settings |
| `status` | `ConversionStatus` | ✅ | Current lifecycle state | Must follow valid transitions |
| `progress` | `float` | ✅ | Conversion progress percentage (0.0 – 100.0) | Only meaningful when status = CONVERTING |
| `error_message` | `str \| None` | ❌ | Human-readable error description | Set when status = ERROR, None otherwise |
| `file_size` | `int` | ✅ | Source file size in bytes | Populated at import time |
| `duration` | `float \| None` | ❌ | Source file duration in seconds (from ffprobe) | Populated before conversion, None if probe fails |
| `created_at` | `datetime` | ✅ | Timestamp when job was added to queue | Auto-set at creation |
| `completed_at` | `datetime \| None` | ❌ | Timestamp when job reached terminal state | Set when status changes to COMPLETE/ERROR/CANCELLED/SKIPPED |

**Identity & Uniqueness**: Jobs are uniquely identified by `id` (UUID). Duplicate detection at import time uses `source_path` — no two jobs may have the same `source_path` in the queue simultaneously.

**Output path resolution**:
- If custom output directory is set: `<custom_dir>/<source_basename>.mp4`
- If no custom directory (default): `<source_dir>/<source_basename>.mp4`
- If auto-rename conflict policy: append `_1`, `_2`, etc. until unique

---

### ConversionQueue

An ordered collection of ConversionJob instances managing batch execution.

| Field | Type | Description |
|-------|------|-------------|
| `jobs` | `list[ConversionJob]` | Ordered list of conversion jobs |
| `is_running` | `bool` | Whether a batch conversion is currently in progress |
| `current_index` | `int \| None` | Index of the currently processing job (None when not running) |

**Operations**:
- `add(source_path: Path) -> ConversionJob`: Validate and add a new job. Raises if duplicate or invalid.
- `remove(job_id: str) -> None`: Remove a pending job. Raises if queue is running.
- `clear() -> None`: Remove all jobs. Raises if queue is running.
- `start() -> None`: Begin sequential processing from first PENDING job.
- `cancel() -> None`: Abort current conversion, stop processing.
- `get_summary() -> QueueSummary`: Return counts by status.

**Aggregate computed properties**:
- `total_count: int` — Total number of jobs
- `completed_count: int` — Jobs with status COMPLETE
- `failed_count: int` — Jobs with status ERROR
- `cancelled_count: int` — Jobs with status CANCELLED
- `skipped_count: int` — Jobs with status SKIPPED
- `pending_count: int` — Jobs with status PENDING
- `overall_progress: str` — e.g., "3 of 10 complete"

---

### QueueSummary

Immutable summary snapshot of queue state after batch completion.

| Field | Type | Description |
|-------|------|-------------|
| `total` | `int` | Total jobs in the batch |
| `completed` | `int` | Successfully converted |
| `failed` | `int` | Failed with errors |
| `cancelled` | `int` | Cancelled by user |
| `skipped` | `int` | Skipped due to conflict policy |

---

### ConflictPolicy (Enum)

Pre-batch policy for handling existing output files.

| Value | Description |
|-------|-------------|
| `ASK` | Prompt user for each file (single-file mode only) |
| `OVERWRITE_ALL` | Overwrite all existing output files |
| `SKIP_ALL` | Skip files that already have output |
| `RENAME_ALL` | Auto-rename output files with suffix `_1`, `_2`, etc. |

---

### AppSettings

Application settings for the current session.

| Field | Type | Default | Persistent | Description |
|-------|------|---------|:----------:|-------------|
| `output_directory` | `Path \| None` | `None` (same as source) | ✅ | Custom output directory |
| `conflict_policy` | `ConflictPolicy` | `ASK` | ✅ | Default file conflict resolution |
| `auto_delete_source` | `bool` | `False` | ✅ | Delete source `.ts` files after successful conversion |
| `window_geometry` | `QByteArray \| None` | `None` | ✅ | Window position and size |
| `last_import_directory` | `Path \| None` | `None` | ✅ | Last used directory in file import dialog |

**Persistence**: Settings are stored via `QSettings` (Windows Registry) or a JSON file in `%APPDATA%/Ts2Mp4/settings.json`. Loaded at startup, saved on change.

**Note**: Constitution specifies "QSettings or JSON config file in user's app data directory." For simplicity and portability, we'll use a JSON file in `%APPDATA%/Ts2Mp4/`.

# UI Contracts: Ts2Mp4 Video Container Converter

**Branch**: `001-ts-mp4-converter` | **Date**: 2026-03-16

This document defines the user-facing interface contracts for the Ts2Mp4 desktop application.

---

## Main Window Layout

```text
┌─────────────────────────────────────────────────────────────────┐
│  Ts2Mp4 — Video Container Converter                        [—][□][✕] │
├─────────────────────────────────────────────────────────────────┤
│  ┌─── Toolbar ──────────────────────────────────────────────┐  │
│  │ [📂 Add Files] [🗑️ Remove] [🧹 Clear All] │ [⚙️ Settings] │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─── Output Directory ────────────────────────────────────┐  │
│  │ 📁 Output: Same as source file      [Browse...]         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─── File Queue ──────────────────────────────────────────┐  │
│  │ # │ File Name       │ Source Path        │ Status    │ ▓ │  │
│  │───┼─────────────────┼────────────────────┼───────────┼───│  │
│  │ 1 │ video1.ts       │ D:\Videos\         │ ✅ Complete│   │  │
│  │ 2 │ recording.ts    │ D:\Recordings\     │ ⏳ 45%    │ ▓▓│  │
│  │ 3 │ capture.ts      │ C:\Users\...\      │ ⏸ Pending │   │  │
│  │ 4 │ broken.ts       │ D:\Videos\         │ ❌ Error   │   │  │
│  │                                                         │  │
│  │          ┌─────────────────────────────────────┐        │  │
│  │          │  Drag and drop .ts files here       │        │  │
│  │          │  or click "Add Files"               │        │  │
│  │          └─────────────────────────────────────┘        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─── Actions ─────────────────────────────────────────────┐  │
│  │ [▶️ Start Conversion]                    [❌ Cancel]      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─── Status Bar ──────────────────────────────────────────┐  │
│  │ 2 of 4 files complete │ 1 error │ Ready                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Widget Behaviors

### Toolbar Buttons

| Button | ID | Enabled When | Action |
|--------|----|:------------:|--------|
| Add Files | `btn_add_files` | Queue NOT running | Opens file dialog filtered to `*.ts` |
| Remove | `btn_remove` | Queue NOT running AND file(s) selected | Removes selected files from queue |
| Clear All | `btn_clear_all` | Queue NOT running AND queue not empty | Removes all files from queue |
| Settings | `btn_settings` | Always | Opens settings dialog |

### Action Buttons

| Button | ID | Enabled When | Action |
|--------|----|:------------:|--------|
| Start Conversion | `btn_start` | Queue NOT running AND queue has ≥1 PENDING file | Starts batch conversion |
| Cancel | `btn_cancel` | Queue IS running | Immediately aborts current file + stops queue |

### File Queue Table

| Column | ID | Content | Sortable |
|--------|----|---------|:--------:|
| # | `col_index` | Row number | No |
| File Name | `col_filename` | Source file base name | Yes |
| Source Path | `col_source_path` | Parent directory of source file | Yes |
| Status | `col_status` | Status text + icon | Yes |
| Progress | `col_progress` | Progress bar (visible during CONVERTING) | No |

**Drag-and-Drop Behavior**:
- Drop zone covers the entire file queue area
- When queue is empty, a placeholder message is shown: "Drag and drop .ts files here or click 'Add Files'"
- Visual feedback (highlight/border change) when files are dragged over the drop zone
- Only `.ts` files accepted; others rejected with notification

**Double-Click Behavior**:
- Double-clicking a file in the queue opens it in the system default media player (preview)

**Context Menu (Right-Click)**:
- "Preview" → Opens in default media player
- "Remove" → Removes file from queue (only when not running)
- "Open Containing Folder" → Opens source file's directory in Windows Explorer

---

## Dialogs

### Settings Dialog

| Setting | Control | ID | Default |
|---------|---------|-----|---------|
| Auto-delete source files | Checkbox | `chk_auto_delete` | Unchecked (OFF) |
| Default conflict policy | Dropdown | `cmb_conflict_policy` | "Ask each time" |

### Conflict Policy Dialog (Pre-Batch)

Shown before batch start if any output files already exist.

```text
┌─── File Conflict Detected ─────────────────────────┐
│                                                      │
│  ⚠️ X output files already exist.                    │
│                                                      │
│  Choose how to handle existing files:                │
│                                                      │
│  ○ Overwrite all existing files                      │
│  ○ Skip files that already exist                     │
│  ○ Auto-rename (add _1, _2, etc.)                   │
│                                                      │
│  ☐ Remember this choice for future conversions       │
│                                                      │
│                    [Cancel]  [Continue]               │
└──────────────────────────────────────────────────────┘
```

### Batch Summary Dialog

Shown after batch conversion completes.

```text
┌─── Conversion Complete ────────────────────────────┐
│                                                      │
│  ✅ Batch conversion finished                        │
│                                                      │
│  Total files:     10                                 │
│  ✅ Completed:     7                                 │
│  ❌ Failed:        2                                 │
│  ⏭️ Skipped:       1                                 │
│                                                      │
│  [View Log]              [OK]                        │
└──────────────────────────────────────────────────────┘
```

### Exit Confirmation Dialog

Shown when user tries to close during active conversion.

```text
┌─── Conversion in Progress ─────────────────────────┐
│                                                      │
│  ⚠️ A conversion is currently running.              │
│                                                      │
│  If you close now:                                   │
│  • The current file conversion will be aborted       │
│  • Partial output files will be deleted              │
│  • Remaining files will not be processed             │
│                                                      │
│                    [Cancel]  [Close Anyway]           │
└──────────────────────────────────────────────────────┘
```

---

## Signal/Slot Contracts (Qt)

### ConversionWorker → MainWindow

| Signal | Parameters | UI Update |
|--------|-----------|-----------|
| `file_started` | `(job_id: str)` | Set row status to "Converting", show progress bar |
| `progress_updated` | `(job_id: str, percent: float)` | Update progress bar value |
| `file_completed` | `(job_id: str)` | Set row status to "Complete" ✅, update overall counter |
| `file_failed` | `(job_id: str, error: str)` | Set row status to "Error" ❌, show error tooltip |
| `file_skipped` | `(job_id: str)` | Set row status to "Skipped" ⏭️ |
| `batch_completed` | `(summary: QueueSummary)` | Show batch summary dialog, re-enable controls |
| `batch_cancelled` | `(summary: QueueSummary)` | Show summary, re-enable controls |

### MainWindow → ConversionWorker

| Action | Method | Effect |
|--------|--------|--------|
| Start Conversion | `worker.start()` | Begin processing queue |
| Cancel | `worker.cancel()` | Abort current file, stop queue |

---

## Notification Contracts

| Event | Type | Display | Duration |
|-------|------|---------|----------|
| Non-.ts file rejected | Warning | Status bar message | 5 seconds |
| Duplicate file detected | Info | Status bar message | 3 seconds |
| Files added successfully | Success | Status bar message | 3 seconds |
| Invalid output directory | Error | Modal dialog | Until dismissed |
| FFmpeg not found | Critical | Modal dialog at startup | Until dismissed |
| Source files deleted | Info | Status bar message | 5 seconds |

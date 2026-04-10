# Feature Specification: Ts2Mp4 Video Container Converter

**Feature Branch**: `001-ts-mp4-converter`  
**Created**: 2026-03-16  
**Status**: Draft  
**Input**: User description: "Standalone Windows desktop application that converts .ts video files to .mp4 format using FFmpeg remuxing with a GUI supporting drag-and-drop, batch processing, queue management, and progress tracking"

## Clarifications

### Session 2026-03-16

- Q: Should the application provide a Cancel/Stop button during batch conversion, and what should its behavior be? → A: Provide a "Cancel" button that immediately aborts the current file (partial output is cleaned up) and stops the queue.
- Q: When converting batch files and output .mp4 already exists, how should the system handle it? → A: Allow user to select a conflict policy once before batch starts (Overwrite all / Skip all / Auto-rename all).
- Q: After successful conversion, what should happen to the original .ts source file? → A: Provide a setting option to auto-delete source files after successful conversion (default: OFF / keep originals).
- Q: Should the application log activity and errors to a file for diagnostics? → A: Auto-log to file (errors + conversion summary per session), stored next to the application executable.
- Q: When a .ts file contains both compatible (video/audio) and incompatible streams (teletext, DVB subtitles), how should the system handle it? → A: Auto-strip incompatible streams and only remux video + primary audio into .mp4.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Drag-and-Drop File Import (Priority: P1)

A user has several `.ts` video files from a TV recording or screen capture session. They launch the Ts2Mp4 application and drag the files directly from Windows Explorer onto the application window. The files immediately appear in a queue list showing file name, path, and a "Pending" status. The user sees visual confirmation that the files were accepted.

**Why this priority**: Drag-and-drop is the primary method most users will use to add files. It enables the fastest possible workflow — the user can go from opening the app to having files queued in a single gesture. Without this, the app loses its core usability differentiator.

**Independent Test**: Can be fully tested by launching the app, dragging one or more `.ts` files onto the window, and verifying they appear in the queue with correct metadata. Delivers immediate value as the entry point to all conversion workflows.

**Acceptance Scenarios**:

1. **Given** the application is open with an empty queue, **When** a user drags 1 `.ts` file onto the window, **Then** the file appears in the queue with its name, source path, and status "Pending"
2. **Given** the application is open with an empty queue, **When** a user drags 5 `.ts` files onto the window, **Then** all 5 files appear in the queue with correct names and "Pending" status
3. **Given** the application is open, **When** a user drags a non-`.ts` file (e.g., `.mp4`, `.txt`) onto the window, **Then** the file is rejected with a clear message indicating only `.ts` files are accepted
4. **Given** the queue already contains `video1.ts`, **When** the user drags `video1.ts` onto the window again, **Then** the duplicate is detected and not added, with a notification to the user
5. **Given** the application is open, **When** a user drags a mix of `.ts` and non-`.ts` files, **Then** only the `.ts` files are added and a message lists the rejected files

---

### User Story 2 - Single File Conversion (Priority: P1)

A user has one `.ts` file they want to convert to `.mp4`. After adding the file to the queue (via drag-and-drop or file dialog), they click the "Start" button. The file is converted using remuxing (container change only, no re-encoding), preserving the original video and audio quality. The output `.mp4` file is saved in the same directory as the source file with the same base name.

**Why this priority**: This is the core value proposition of the application — converting a `.ts` file to `.mp4`. Without this capability, the application has no purpose. It demonstrates the fundamental remuxing workflow end-to-end.

**Independent Test**: Can be fully tested by adding one `.ts` file, clicking Start, and verifying that a `.mp4` file with identical audio/video streams appears in the source directory. Delivers the complete core value of the application.

**Acceptance Scenarios**:

1. **Given** a queue with one `.ts` file, **When** the user clicks "Start", **Then** the file status changes to "Converting" and upon completion changes to "Complete"
2. **Given** a completed conversion, **When** the user checks the output directory, **Then** an `.mp4` file exists with the same base name as the source `.ts` file
3. **Given** a completed conversion, **When** the output `.mp4` is inspected, **Then** the video/audio streams are bit-identical to the source (no quality loss)
4. **Given** no custom output directory is set, **When** a file is converted, **Then** the output is saved in the same directory as the source file

---

### User Story 3 - File Import via Button (Priority: P1)

A user prefers to use a traditional file browser rather than drag-and-drop. They click an "Add Files" button which opens a file dialog filtered to show only `.ts` files. The user selects one or more files, and they are added to the existing queue (not replacing any existing queued files).

**Why this priority**: This provides an essential alternative file import method for users who are not comfortable with drag-and-drop, or who need to navigate deep folder structures. It ensures accessibility for all user types and completes the file input story.

**Independent Test**: Can be fully tested by clicking the "Add Files" button, selecting `.ts` files from the dialog, and verifying they appear in the queue. Delivers an alternative import pathway to User Story 1.

**Acceptance Scenarios**:

1. **Given** the application is open, **When** the user clicks "Add Files", **Then** a file dialog opens filtered to show `.ts` files
2. **Given** the file dialog is open, **When** the user selects multiple `.ts` files and confirms, **Then** all selected files are added to the queue
3. **Given** the queue already contains 3 files, **When** the user adds 2 more files via the button, **Then** the queue now contains all 5 files (existing files are not replaced)

---

### User Story 4 - Batch Conversion with Sequential Processing (Priority: P1)

A user has 10+ `.ts` files from a week of TV recordings. After adding all files to the queue, they click "Start" once. The application processes each file sequentially — one at a time — converting each from `.ts` to `.mp4`. Each file in the queue shows its current status (Pending → Converting → Complete or Error). If one file fails (e.g., corrupted), the queue continues processing the remaining files. After all files are processed, a summary is displayed showing how many succeeded and how many failed.

**Why this priority**: Batch processing is a major differentiator from manual single-file conversion. Users with multiple files need to set up the queue once and walk away, rather than babysitting each file individually. This is essential for the tool's real-world utility.

**Independent Test**: Can be fully tested by queuing 5+ files (including one intentionally invalid file), starting conversion, and verifying all valid files convert while the invalid file is marked as error and skipped.

**Acceptance Scenarios**:

1. **Given** a queue with 5 files, **When** the user clicks "Start", **Then** files are processed one at a time in queue order
2. **Given** a batch conversion is in progress, **When** a file completes, **Then** its status changes to "Complete" and the next file begins processing
3. **Given** a batch conversion encounters a corrupted file, **When** the conversion of that file fails, **Then** it is marked as "Error" with details, and the next file in the queue begins processing
4. **Given** all files in a batch have been processed, **When** the batch is complete, **Then** a summary is displayed showing total files, successful conversions, and failed conversions
5. **Given** a batch of 10 files, **When** the 3rd file fails, **Then** files 4-10 still process normally
6. **Given** a batch conversion is in progress (file 3 of 10 converting), **When** the user clicks "Cancel", **Then** the current file's conversion is immediately aborted, its partial output file is deleted, the file is marked as "Cancelled", and remaining files stay as "Pending"
7. **Given** a batch of 5 files where 2 already have `.mp4` outputs and the user selected "Skip all" conflict policy, **When** the batch runs, **Then** the 2 existing files are skipped (marked "Skipped") and the remaining 3 are converted normally

---

### User Story 5 - Output Directory Selection (Priority: P2)

A user wants all their converted `.mp4` files to go to a specific folder (e.g., `D:\Videos\Converted`). They click a "Browse" button to select a custom output directory. The selected directory path is displayed in the application. All subsequent conversions save output files to this chosen directory instead of the source file's directory. The setting persists for the duration of the session.

**Why this priority**: While the default behavior (same directory as source) covers most cases, many users need organizational control over where output files land. This is a high-value enhancement that significantly improves workflow flexibility.

**Independent Test**: Can be fully tested by selecting a custom output directory, converting a file, and verifying the output appears in the chosen directory rather than the source directory.

**Acceptance Scenarios**:

1. **Given** the application is open, **When** the user clicks the output directory "Browse" button, **Then** a folder picker dialog opens
2. **Given** a custom output directory is selected, **When** a file is converted, **Then** the output `.mp4` is saved in the custom directory
3. **Given** a custom output directory is displayed, **When** the user views the setting, **Then** the full path of the selected directory is visible
4. **Given** the user selects a read-only or invalid directory, **When** they confirm the selection, **Then** an error is displayed indicating the directory is not writable
5. **Given** no custom directory is selected (default), **When** a file is converted, **Then** the output is saved in the same directory as the source file

---

### User Story 6 - Queue Management Before Conversion (Priority: P2)

A user has added 15 files to the queue but realizes some files were added by mistake. Before starting the conversion, they remove specific files from the queue by selecting them and clicking a remove button. They can also clear the entire queue using a "Clear All" option. They then add a few more files and finally start conversion with the curated list.

**Why this priority**: Users need control over what they're about to convert. Without queue management, mistakes cannot be corrected without restarting the application. This feature completes the pre-conversion workflow.

**Independent Test**: Can be fully tested by adding files, removing some, clearing all, re-adding, and verifying the final queue state before starting conversion.

**Acceptance Scenarios**:

1. **Given** a queue with 5 files, **When** the user selects a file and clicks "Remove", **Then** the selected file is removed from the queue
2. **Given** a queue with 5 files, **When** the user clicks "Clear All", **Then** all files are removed from the queue
3. **Given** a queue with files, **When** more files are added (drag-drop or button), **Then** the new files are appended to the existing queue
4. **Given** a conversion is in progress, **When** the user tries to add or remove files, **Then** the queue modification is blocked and the user is informed that the queue cannot be changed during conversion

---

### User Story 7 - Conversion Progress Visibility (Priority: P2)

A user has started a batch conversion of large `.ts` files. They can see the overall queue progress (e.g., "3 of 10 files complete") and per-file status updates in real-time. For large files, a progress indicator shows conversion activity. Error details are displayed inline for any failed files. The GUI remains responsive throughout the entire conversion process — the user can scroll the queue, resize the window, etc.

**Why this priority**: Progress visibility builds user trust and helps users estimate time remaining. Without it, users might think the app has frozen and force-close it. GUI responsiveness is non-negotiable for a professional application.

**Independent Test**: Can be fully tested by starting a batch conversion with large files and verifying that progress updates appear in real-time, error details are visible for failed files, and the GUI remains responsive.

**Acceptance Scenarios**:

1. **Given** a batch conversion is running, **When** a file finishes converting, **Then** the overall progress counter updates (e.g., "3 of 10 complete")
2. **Given** a file is currently being converted, **When** the user views the queue, **Then** a progress indicator is visible for the active file
3. **Given** a file fails to convert, **When** it is marked as "Error", **Then** error details are displayed so the user understands what went wrong
4. **Given** a conversion is in progress, **When** the user interacts with the GUI (scrolling, resizing), **Then** the application responds immediately without freezing or lagging

---

### User Story 8 - File Preview (Priority: P3)

A user is unsure which `.ts` file in the queue is the one they want. They right-click or double-click a file in the queue to preview it. The file opens in the system's default media player. Previewing does not block or interfere with the conversion queue.

**Why this priority**: This is a nice-to-have feature that helps users verify files before converting. It can be added after the core functionality is complete and does not affect the primary conversion workflow.

**Independent Test**: Can be fully tested by double-clicking a queued file and verifying it opens in the default media player without blocking the application.

**Acceptance Scenarios**:

1. **Given** a file is in the queue, **When** the user double-clicks or right-clicks and selects "Preview", **Then** the file opens in the system default media player
2. **Given** a preview is open, **When** the user starts a conversion, **Then** the conversion proceeds normally without waiting for the preview to close
3. **Given** a conversion is running, **When** the user previews a queued file, **Then** the preview opens without affecting the active conversion

---

### Edge Cases

- What happens when the user tries to convert a file that has already been converted (`.mp4` already exists)? → For single file conversion, the system prompts the user (overwrite / skip / rename). For batch conversion, the user selects a conflict policy before the batch starts (Overwrite all / Skip all / Auto-rename all) so the batch runs uninterrupted
- What happens when the disk is full during conversion? → The system should pause the queue, alert the user, and allow them to free space or change the output directory
- What happens when FFmpeg is not found on the system? → The system should display a clear error dialog with instructions on how to resolve (if FFmpeg is bundled, this should not occur)
- What happens when a `.ts` file uses non-standard codec combinations that cannot be remuxed into `.mp4`? → The system automatically strips incompatible streams (teletext, DVB subtitles, etc.) and remuxes only video + audio. If even the primary video/audio streams are incompatible, the file is marked as "Error" with details and skipped
- What happens when the source `.ts` file is on a network drive with intermittent connectivity? → The system should handle I/O errors gracefully with a clear message, and continue processing other files
- What happens when the user closes the application during an active conversion? → The system should prompt the user with a confirmation dialog warning that conversion is in progress. Partial output files should be cleaned up if the user confirms exit
- What happens when a `.ts` file is extremely large (> 10GB)? → The system should handle it via stream-based processing without loading the entire file into memory
- What happens when the user adds hundreds of files to the queue? → The system should remain responsive and handle large queues without performance degradation
- What happens when the user cancels during a batch conversion? → The current file's conversion is immediately aborted, its partial output is deleted, and remaining queued files stay as "Pending" (not processed). A summary shows completed, cancelled, and pending counts
- What happens when auto-delete source files is enabled and a conversion fails? → Only files with status "Complete" are deleted. Failed, cancelled, skipped, and pending files' sources are never deleted

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a graphical window that accepts `.ts` files via drag-and-drop from the file system
- **FR-002**: System MUST provide an "Add Files" button that opens a file dialog filtered to `.ts` files with multi-select support
- **FR-003**: System MUST display a file queue showing each file's name, source path, and current status
- **FR-004**: System MUST convert `.ts` files to `.mp4` format using remuxing (container change only, no re-encoding) to preserve original quality, automatically selecting only compatible streams (video and audio)
- **FR-005**: System MUST preserve the original file name when creating the output `.mp4` (e.g., `video.ts` → `video.mp4`)
- **FR-006**: System MUST process queued files sequentially, one at a time, in queue order
- **FR-007**: System MUST continue processing remaining files in the queue if a single file conversion fails
- **FR-008**: System MUST track and display each file's status as one of: Pending, Converting, Complete, or Error
- **FR-009**: System MUST display a summary when batch conversion completes showing total, successful, and failed file counts
- **FR-010**: System MUST allow users to select a custom output directory via a folder picker dialog
- **FR-011**: System MUST default to saving output files in the same directory as the source file when no custom directory is set
- **FR-012**: System MUST allow users to remove individual files from the queue before conversion starts
- **FR-013**: System MUST provide a "Clear All" option to remove all files from the queue
- **FR-014**: System MUST prevent queue modification (add/remove) while a conversion is in progress
- **FR-015**: System MUST reject non-`.ts` files during import with a clear error message
- **FR-016**: System MUST detect and prevent duplicate files from being added to the queue
- **FR-017**: System MUST display overall queue progress (e.g., "X of Y files complete") during batch conversion
- **FR-018**: System MUST show a progress indicator for the file currently being converted
- **FR-019**: System MUST display error details for any file that fails to convert
- **FR-020**: System MUST remain responsive (no GUI freezing) during all conversion operations
- **FR-021**: System MUST prompt the user when an output file already exists during single-file conversion, offering options to overwrite, skip, or rename
- **FR-022**: System MUST prompt the user with a confirmation dialog if they attempt to close the application during an active conversion
- **FR-023**: System MUST clean up partial/incomplete output files if a conversion is interrupted, cancelled, or fails
- **FR-024**: System MUST handle files larger than 10GB without excessive memory usage or crashes
- **FR-025**: System MUST provide a file preview capability that opens the selected file in the system default media player without blocking the queue
- **FR-026**: System MUST provide a "Cancel" button during active conversion that immediately aborts the current file conversion, cleans up partial output, and stops processing the remaining queue
- **FR-027**: System MUST allow users to select a file conflict resolution policy before starting a batch conversion: Overwrite all existing outputs, Skip all existing outputs, or Auto-rename all conflicting outputs (e.g., append suffix `_1`, `_2`)
- **FR-028**: System MUST provide a setting to auto-delete original `.ts` source files after successful conversion, defaulting to OFF (keep originals). When enabled, only files with status "Complete" are deleted after the batch finishes
- **FR-029**: System MUST automatically log conversion activity to a log file stored in the same directory as the application executable, including: errors with details, a summary of each conversion session (files processed, succeeded, failed), and timestamps
- **FR-030**: System MUST automatically strip incompatible streams (e.g., teletext, DVB subtitles) during remuxing and only include video and audio streams in the output `.mp4`. A log entry should note which streams were excluded

### Key Entities

- **Conversion Job**: Represents a single file conversion task. Key attributes: source file path, output file path, status (Pending/Converting/Complete/Error/Cancelled/Skipped), error message (if failed), progress percentage
- **Conversion Queue**: An ordered collection of Conversion Jobs. Manages job ordering, sequential execution, and aggregate progress tracking
- **Application Settings**: User preferences for the current session. Key attributes: custom output directory path (or default/same-as-source behavior), file conflict resolution policy (overwrite/skip/auto-rename), auto-delete source files after success (default: OFF)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete their first file conversion in under 30 seconds from application launch (≤ 3 clicks: launch → add file → start)
- **SC-002**: Conversion speed exceeds 100 MB/s for standard `.ts` files (limited only by disk I/O, not processing)
- **SC-003**: 100% of successfully converted `.mp4` files are playable in standard media players without quality loss
- **SC-004**: Conversion success rate exceeds 99% for valid, non-corrupted `.ts` files
- **SC-005**: The application starts and is ready for use in less than 3 seconds
- **SC-006**: The GUI remains responsive (no perceptible lag or freezing) during active file conversion
- **SC-007**: The application handles batches of 100+ files without performance degradation or crashes
- **SC-008**: The application memory usage stays below 100 MB during conversion operations
- **SC-009**: Drag-and-drop file import succeeds reliably on first attempt (> 99% success rate)
- **SC-010**: All error messages are clear enough for non-technical users to understand the problem and take corrective action
- **SC-011**: The application runs as a standalone executable on Windows 10/11 without requiring additional software installations from the user
- **SC-012**: Application crashes occur in fewer than 0.1% of sessions

## Assumptions

- The application targets **Windows 10/11 (x64)** only. Cross-platform support is not in scope.
- **FFmpeg** will be bundled alongside the application executable, so users do not need to install it separately or configure system PATH.
- The application uses **remuxing only** (`ffmpeg -c copy`), not re-encoding. If a `.ts` file has codecs incompatible with the `.mp4` container, the conversion will fail gracefully rather than falling back to re-encoding.
- The application is a **standalone desktop application** — no network/cloud features, no user accounts, no telnet/analytics.
- **Settings persistence** is session-only for the MVP. Preferences (such as the last used output directory) do not persist across application restarts unless explicitly implemented in a later phase.
- Standard **sequential processing** is used for batch conversion. Parallel/concurrent conversion of multiple files simultaneously is not in scope.
- The application window uses a **single-window design** — no multi-window or tabbed interface.
- **File name collisions** (when output file already exists) default to prompting the user. No automatic conflict resolution policy is assumed.

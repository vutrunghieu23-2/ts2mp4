# Feature Specification: Avidemux Converter Engine

**Feature Branch**: `002-avidemux-converter-engine`  
**Created**: 2026-03-17  
**Status**: Draft  
**Input**: User description: "Khi dùng ffmpeg thì thi thoảng bị lỗi. Hãy thêm phương án (trong setting) sử dụng avidemux\avidemux_cli.exe để convert. (mặc định)"

## Clarifications

### Session 2026-03-17

- Q: Nếu engine đã chọn fail cho một file, hệ thống có nên tự động thử engine còn lại không? → A: Không auto-fallback — file fail thì đánh dấu Error, user tự switch engine nếu muốn thử lại
- Q: Nếu Avidemux CLI không output progress theo dạng parse được, hệ thống hiển thị progress thế nào? → A: Dùng indeterminate progress (thanh chạy liên tục) nếu không parse được output của Avidemux
- Q: Avidemux engine có cần strip incompatible streams (teletext, DVB subtitles) giống FFmpeg không? → A: Không cần logic strip riêng — để Avidemux CLI tự xử lý stream selection, nếu fail vì incompatible streams thì đánh dấu Error

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select Converter Engine in Settings (Priority: P1)

A user has been experiencing occasional FFmpeg conversion errors with certain `.ts` files. They open the Settings dialog and see a new "Converter Engine" option. The user can choose between two converter engines: **Avidemux** (default) and **FFmpeg**. The selected engine is saved and persisted across application restarts. All subsequent conversions use the selected engine.

**Why this priority**: This is the core of the feature — without the ability to switch engines, the alternative converter has no entry point. The setting must exist before any conversion logic can use it.

**Independent Test**: Can be fully tested by opening Settings, changing the converter engine, closing and reopening the app, and verifying the setting was persisted.

**Acceptance Scenarios**:

1. **Given** the application is freshly installed, **When** the user opens Settings, **Then** the Converter Engine is set to "Avidemux" by default
2. **Given** the user is in the Settings dialog, **When** they change the Converter Engine from "Avidemux" to "FFmpeg", **Then** the selection is updated and saved when they click OK
3. **Given** the user selected "FFmpeg" as the converter engine and closed the app, **When** they reopen the app and check Settings, **Then** the Converter Engine still shows "FFmpeg"
4. **Given** the user selected "Avidemux" as the converter engine, **When** they start a conversion, **Then** the system uses the Avidemux CLI engine to perform the conversion

---

### User Story 2 - Convert Files Using Avidemux Engine (Priority: P1)

A user has `.ts` files that fail to convert with FFmpeg due to corrupt packets or ADTS frame header errors. They switch to the Avidemux engine (or keep the default). When they add files and click "Start", the application invokes `avidemux\avidemux_cli.exe` with appropriate parameters to convert `.ts` to `.mp4` using stream copy (remuxing). The conversion completes successfully for files that previously failed with FFmpeg. Progress is tracked and displayed as with FFmpeg conversions.

**Why this priority**: This delivers the core value — an alternative converter that handles files FFmpeg cannot. Without this, the setting in User Story 1 has no practical effect.

**Independent Test**: Can be fully tested by selecting Avidemux engine, adding a `.ts` file, starting conversion, and verifying a valid `.mp4` file is produced in the expected output directory.

**Acceptance Scenarios**:

1. **Given** the converter engine is set to "Avidemux" and a `.ts` file is queued, **When** the user clicks "Start", **Then** the system invokes `avidemux_cli.exe` to convert the file to `.mp4`
2. **Given** an Avidemux conversion is running, **When** the user views the queue, **Then** an indeterminate progress indicator (continuous animation) is visible for the active file if Avidemux does not provide parseable progress output
3. **Given** the Avidemux conversion completes, **When** the user checks the output directory, **Then** an `.mp4` file exists with the same base name as the source `.ts` file
4. **Given** a `.ts` file that fails with FFmpeg, **When** the same file is converted with Avidemux engine, **Then** the conversion succeeds and produces a playable `.mp4` file
5. **Given** the converter engine is set to "Avidemux" and a batch of files is queued, **When** the user clicks "Start", **Then** all files are processed sequentially using the Avidemux engine

---

### User Story 3 - Convert Files Using FFmpeg Engine (Priority: P2)

A user prefers FFmpeg for certain conversions (e.g., files that convert perfectly with FFmpeg and benefit from its faster processing). They select "FFmpeg" in the Settings and convert files. The existing FFmpeg two-pass conversion behavior remains unchanged and fully functional.

**Why this priority**: FFmpeg is the existing engine and must continue to work exactly as before. This story ensures backward compatibility — no regression in existing functionality.

**Independent Test**: Can be fully tested by selecting FFmpeg engine, converting a `.ts` file, and verifying the same behavior as before the feature was added (two-pass strategy, error tolerance, etc.).

**Acceptance Scenarios**:

1. **Given** the converter engine is set to "FFmpeg" and a `.ts` file is queued, **When** the user clicks "Start", **Then** the system uses the existing FFmpeg two-pass conversion strategy
2. **Given** the converter engine is set to "FFmpeg", **When** stream copy fails, **Then** the system automatically retries with audio re-encoding (existing pass 2 behavior)
3. **Given** the converter engine was changed from "Avidemux" to "FFmpeg", **When** a conversion is started, **Then** the conversion uses FFmpeg with all existing error tolerance flags

---

### User Story 4 - Avidemux Binary Not Found (Priority: P2)

A user has selected Avidemux as the converter engine, but the `avidemux\avidemux_cli.exe` binary cannot be found at the expected location (relative to the application). The system displays a clear error message before starting conversion, explaining that the Avidemux binary is missing and suggesting the user either place it in the correct directory or switch to the FFmpeg engine.

**Why this priority**: Graceful error handling for a missing binary prevents confusing crashes and guides the user to a resolution.

**Independent Test**: Can be fully tested by removing or renaming the `avidemux_cli.exe` binary, selecting Avidemux engine, attempting a conversion, and verifying a helpful error message appears.

**Acceptance Scenarios**:

1. **Given** Avidemux is selected as the engine but `avidemux_cli.exe` is not found, **When** the user starts a conversion, **Then** an error message is displayed explaining the binary is missing
2. **Given** the Avidemux binary is missing, **When** the error message is shown, **Then** it suggests placing the binary in the correct directory or switching to FFmpeg
3. **Given** FFmpeg is selected as the engine and `avidemux_cli.exe` is missing, **When** the user starts a conversion, **Then** the conversion proceeds normally with FFmpeg (no error about Avidemux)

---

### Edge Cases

- What happens when the user switches converter engine mid-batch (during active conversion)? → The setting change takes effect only for the next batch; the current batch completes with the engine it started with
- What happens when Avidemux conversion fails for a file? → The file is marked as "Error" with details, and the queue continues to the next file (same behavior as FFmpeg failures). The system does NOT automatically fall back to the other engine; the user must manually switch engines and retry if desired
- What happens when the Avidemux binary exists but is corrupted or returns unexpected errors? → The system captures the error output, marks the file as failed with the error details, and continues processing remaining files
- What happens when the user upgrades from a version without this feature? → The settings file gains a new `converter_engine` field; if absent, it defaults to "avidemux" (the new default)
- What happens when both FFmpeg and Avidemux binaries are missing? → The system shows an error for whichever engine is selected, and the user is informed about the missing binary

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a "Converter Engine" setting in the Settings dialog allowing the user to choose between "Avidemux" and "FFmpeg"
- **FR-002**: System MUST default the Converter Engine to "Avidemux" for new installations and upgrades from versions without this setting
- **FR-003**: System MUST persist the selected Converter Engine across application restarts
- **FR-004**: System MUST use the selected Converter Engine for all file conversions
- **FR-005**: System MUST invoke `avidemux\avidemux_cli.exe` (relative to the application directory) when the Avidemux engine is selected, using appropriate command-line parameters for `.ts` to `.mp4` remuxing (stream copy)
- **FR-006**: System MUST display conversion progress when using the Avidemux engine. If Avidemux CLI provides parseable progress output, a percentage-based progress bar is shown. If not, the system MUST display an indeterminate progress indicator (continuous animation) to show the conversion is active
- **FR-007**: System MUST support batch conversion (sequential processing) with the Avidemux engine, following the same queue management behavior as FFmpeg conversions
- **FR-008**: System MUST support cancellation of Avidemux conversions, terminating the `avidemux_cli.exe` process and cleaning up partial output files
- **FR-009**: System MUST display a clear error message when the selected converter engine's binary is not found, with guidance on resolution
- **FR-010**: System MUST preserve all existing FFmpeg conversion behavior (two-pass strategy, error tolerance, stream filtering) when FFmpeg is selected as the engine
- **FR-011**: System MUST handle Avidemux conversion failures gracefully — marking the file as "Error" with details and continuing to the next file in the queue
- **FR-012**: System MUST support the existing conflict resolution policies (overwrite/skip/rename) regardless of which converter engine is selected
- **FR-013**: System MUST support the auto-delete source file setting regardless of which converter engine is selected

### Key Entities

- **Converter Engine**: An enumeration representing the available conversion tools. Values: Avidemux, FFmpeg. Stored as part of Application Settings. Determines which binary and command-line strategy is used for conversion
- **Application Settings** (updated): Extended with a new `converter_engine` attribute (default: "avidemux") persisted in the existing settings JSON file

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can switch between Avidemux and FFmpeg engines in under 10 seconds (open Settings → change engine → OK)
- **SC-002**: Files that previously failed with FFmpeg convert successfully using the Avidemux engine
- **SC-003**: Avidemux conversion preserves original video and audio quality (remuxing, no re-encoding)
- **SC-004**: All existing FFmpeg functionality continues to work identically when FFmpeg is the selected engine (zero regressions)
- **SC-005**: The converter engine setting persists correctly across 100% of application restarts
- **SC-006**: Batch conversion with the Avidemux engine handles 100+ files without performance degradation
- **SC-007**: Error messages for missing binaries are clear enough for non-technical users to resolve the issue

## Assumptions

- **Avidemux CLI** (`avidemux_cli.exe`) is bundled alongside the application in an `avidemux\` subdirectory relative to the application root. Users do not need to install it separately.
- Avidemux CLI supports `.ts` to `.mp4` conversion via stream copy (remuxing) through command-line parameters.
- The Avidemux CLI outputs progress information that can be parsed for progress tracking (or alternative progress estimation will be used if not available).
- The default converter engine is changed to **Avidemux** because it handles more `.ts` files reliably compared to FFmpeg, which occasionally fails with corrupt packets.
- All existing settings (output directory, conflict policy, auto-delete) apply equally regardless of the selected converter engine.
- The converter engine setting is a session-wide setting — it applies to all conversions, not per-file.
- Avidemux CLI tự xử lý stream selection khi convert sang MP4. Hệ thống không cần thêm logic strip incompatible streams riêng cho Avidemux engine — nếu file có streams không tương thích và Avidemux không xử lý được, file sẽ bị đánh dấu Error.

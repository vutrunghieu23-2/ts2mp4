<!--
  === Sync Impact Report ===
  Version change: N/A (initial) → 1.0.0
  Modified principles: N/A (first ratification)
  Added sections:
    - Principle I: Remux-Only Conversion
    - Principle II: Responsive GUI Architecture
    - Principle III: Defensive Error Handling
    - Principle IV: Test-Driven Quality
    - Principle V: Minimal Footprint
    - Section: Technical Constraints
    - Section: Development Workflow
    - Section: Governance
  Removed sections: N/A
  Templates requiring updates:
    - .specify/templates/plan-template.md ✅ reviewed (no changes needed)
    - .specify/templates/spec-template.md ✅ reviewed (no changes needed)
    - .specify/templates/tasks-template.md ✅ reviewed (no changes needed)
  Follow-up TODOs: None
-->

# Ts2Mp4 Constitution

## Core Principles

### I. Remux-Only Conversion

The application MUST convert `.ts` files to `.mp4` exclusively via
FFmpeg container remuxing (`-c copy`). Re-encoding is explicitly
prohibited in normal operation.

- The FFmpeg command MUST be: `ffmpeg -i input.ts -c copy -f mp4 output.mp4`
- No codec parameters (bitrate, resolution, encoder) MUST be exposed
  in the standard workflow.
- If a `.ts` file contains codecs incompatible with MP4 containers,
  the application MUST report an error rather than silently re-encode.
- This principle ensures: zero quality loss, near-instant speed, and
  minimal CPU usage — the core value proposition of the product.

### II. Responsive GUI Architecture

The GUI MUST remain responsive at all times. No user action may block
the main thread.

- All FFmpeg operations MUST execute on a background worker thread
  (QThread or equivalent), never on the UI thread.
- The UI MUST update status, progress, and file lists in real-time
  during batch conversion.
- Drag-and-drop, button clicks, and queue management MUST respond
  within 100ms under normal conditions.
- The application MUST use PySide6 (Qt 6) as the GUI framework.
  Tkinter is not acceptable for this project due to limited native
  widget support and drag-and-drop shortcomings on Windows.

### III. Defensive Error Handling

Every error scenario MUST be anticipated, caught, and communicated
clearly to the user. The application MUST NOT crash or silently fail.

- FFmpeg process failures MUST be caught via subprocess return codes
  and stderr parsing; error details MUST be displayed to the user.
- Invalid file types (non-`.ts`) MUST be rejected at import time
  with a user-friendly message.
- Missing FFmpeg binary MUST be detected at startup and surfaced
  with installation/configuration guidance.
- Disk space, permission, and file-exists conflicts MUST be checked
  before conversion begins.
- A single file failure MUST NOT halt the entire queue; processing
  MUST continue with subsequent files.

### IV. Test-Driven Quality

Critical business logic MUST be covered by automated tests. Tests
SHOULD be written before implementation when feasible.

- Unit tests MUST cover: file validation, queue management, FFmpeg
  command construction, progress parsing, and output path resolution.
- Integration tests SHOULD verify end-to-end conversion of sample
  `.ts` files using a real FFmpeg binary.
- GUI-specific logic (signal/slot connections, widget state) SHOULD
  be tested via Qt's test utilities where practical.
- Test framework: `pytest` with `pytest-qt` for GUI testing.
- Minimum coverage target: 80% for non-GUI business logic modules.

### V. Minimal Footprint

The application MUST be lightweight, fast to start, and small to
distribute. Unnecessary dependencies are rejected.

- Application startup MUST complete in under 3 seconds on a
  standard Windows 10/11 machine.
- Memory usage during conversion MUST stay below 100MB.
- The packaged `.exe` (excluding bundled FFmpeg) SHOULD be under
  50MB.
- Dependencies MUST be justified and minimal. No framework or
  library may be added without a clear, documented reason.
- FFmpeg MUST be bundled alongside the application (not embedded
  inside the `.exe`) to keep package size manageable and allow
  user-side updates.

## Technical Constraints

- **Language**: Python 3.10+ (required for modern type hints and
  PySide6 compatibility).
- **GUI Framework**: PySide6 (Qt 6). No other GUI framework is
  permitted.
- **Video Engine**: FFmpeg invoked via `subprocess`. No Python
  FFmpeg bindings (e.g., `ffmpeg-python`) unless they provide clear
  value over direct subprocess calls.
- **Packaging**: PyInstaller in `--onedir` mode. The `--onefile`
  mode is prohibited due to slow startup and Windows Defender false
  positives.
- **Target Platform**: Windows 10/11 x64 only. Cross-platform
  support is a non-goal for v1.
- **Threading**: `QThread` for worker threads. Python's `threading`
  module SHOULD NOT be mixed with Qt's event loop.
- **Configuration**: Application settings (last output directory,
  window geometry) MUST be persisted via `QSettings` or a JSON
  config file in the user's app data directory.

## Development Workflow

- **Branching**: Feature branches from `main`. Direct commits to
  `main` are prohibited.
- **Commit Discipline**: Each commit MUST be atomic and represent a
  single logical change. Commit messages MUST follow Conventional
  Commits format (e.g., `feat:`, `fix:`, `docs:`, `refactor:`).
- **Code Style**: All Python code MUST pass `ruff` linting and
  formatting checks. Line length limit: 100 characters.
- **Type Hints**: All public functions and methods MUST have type
  annotations. `mypy` SHOULD pass with no errors.
- **Documentation**: All public classes and functions MUST have
  docstrings. README MUST include installation, usage, and build
  instructions.
- **Review Gates**: Before merging, code MUST:
  1. Pass all existing tests (`pytest`).
  2. Pass linting (`ruff check`).
  3. Have no unresolved TODOs related to the change.

## Governance

This constitution is the governing document for the Ts2Mp4 project.
All development decisions, code reviews, and architectural choices
MUST comply with the principles and constraints defined herein.

- **Supremacy**: This constitution supersedes any conflicting
  guidance in other project documents, comments, or conventions.
- **Amendments**: Any change to this constitution MUST be:
  1. Documented with rationale.
  2. Reflected in a version bump (MAJOR for principle
     removal/redefinition, MINOR for additions, PATCH for
     clarifications).
  3. Propagated to dependent templates and documentation.
- **Compliance**: Every code contribution MUST be verified against
  the applicable principles before acceptance.
- **Complexity Justification**: Any deviation from these principles
  MUST be explicitly justified and documented in the relevant
  plan or task file.

**Version**: 1.0.0 | **Ratified**: 2026-03-16 | **Last Amended**: 2026-03-16

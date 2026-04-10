# Research: Avidemux Converter Engine

## R1: Avidemux CLI Command Syntax

**Decision**: Use `avidemux_cli.exe --load <input> --video-codec copy --audio-codec copy --output-format mp4 --save <output>`

**Rationale**: This is the standard Avidemux CLI invocation for remuxing. The `--video-codec copy` and `--audio-codec copy` flags ensure stream copy (no re-encoding), matching the FFmpeg `-c copy` behavior. The `--output-format mp4` sets the container format.

**Alternatives considered**:
- Using Avidemux TinyPy scripting (`--run script.py`): More flexible but adds complexity and requires maintaining script files. Not needed for simple remuxing.
- Using `avidemux2_cli.exe`: Some versions use `avidemux2_cli` as the binary name. The implementation should check both names during path resolution.

**Key Parameters**:
| Parameter | Value | Purpose |
|-----------|-------|---------|
| `--load` | `<input.ts>` | Load input file |
| `--video-codec` | `copy` | Copy video stream (no re-encoding) |
| `--audio-codec` | `copy` | Copy audio stream (no re-encoding) |
| `--output-format` | `mp4` | Set output container to MP4 |
| `--save` | `<output.mp4>` | Save output file |

## R2: Avidemux CLI Progress Output

**Decision**: Use indeterminate progress indicator. Avidemux CLI does not reliably output parseable progress in a standard format to stdout/stderr during conversion.

**Rationale**: Unlike FFmpeg which outputs `time=HH:MM:SS.ms` to stderr, Avidemux CLI's output to stdout/stderr is minimal and inconsistent across versions. There is no standard progress output format documented.

**Alternatives considered**:
- File size monitoring: Poll the output file size and compare against input file size. Rejected because the ratio between input and output sizes is not always 1:1 (container overhead differs).
- Parse Avidemux stdout: Output format is not standardized and varies between versions.

**Implementation**: When `converter_engine` is `avidemux`, the ConversionWorker emits `progress_updated(job_id, -1.0)` to signal indeterminate progress. The UI shows a pulsing/bouncing progress bar.

## R3: Binary Path Resolution

**Decision**: Resolve `avidemux_cli.exe` from `<app_dir>/avidemux/avidemux_cli.exe`, with system PATH fallback.

**Rationale**: Mirrors the existing FFmpeg resolution strategy (`resolve_ffmpeg_path()`). The Avidemux binary is expected in an `avidemux/` subdirectory alongside the application.

**Search order**:
1. `<app_dir>/avidemux/avidemux_cli.exe` (bundled — primary)
2. System PATH: `shutil.which("avidemux_cli")` (fallback)
3. If neither found → return `None`

## R4: Converter Interface Pattern

**Decision**: Introduce a common converter protocol/interface that both `FFmpegConverter` and `AvidemuxConverter` implement.

**Rationale**: The `ConversionWorker` currently hardcodes `FFmpegConverter`. To support both engines, we need a converter abstraction. Both converters share the same interface: `convert(job) -> Generator[str, None, bool]`, `get_process()`, returning stderr lines and success/failure.

**Alternatives considered**:
- Direct if/else in ConversionWorker: Simpler but violates OCP (Open/Closed Principle) and makes testing harder.
- Strategy pattern with factory: Clean separation, easy to add more engines later.

**Implementation**: Use Python's `Protocol` class (PEP 544) for structural subtyping, or a simple ABC. A factory function `create_converter(engine: ConverterEngine, settings: AppSettings) -> ConverterProtocol` selects the right implementation.

## R5: Settings Integration

**Decision**: Add `converter_engine: str` field to `AppSettings` dataclass with default value `"avidemux"`.

**Rationale**: Follows existing settings pattern. The value is serialized as a string in the JSON settings file. On deserialization, unrecognized values fall back to the default.

**Migration strategy**: When loading settings from a JSON file that lacks the `converter_engine` key, `dict.get("converter_engine", "avidemux")` returns the default. No explicit migration step needed.

# Data Model: Avidemux Converter Engine

## Entities

### ConverterEngine (Enum)

Enumeration of available converter tools.

| Value | String | Description |
|-------|--------|-------------|
| AVIDEMUX | `"avidemux"` | Avidemux CLI converter (default) |
| FFMPEG | `"ffmpeg"` | FFmpeg converter (existing) |

**Default**: `AVIDEMUX`

### AppSettings (Updated)

Extended with the `converter_engine` field.

| Field | Type | Default | Persisted | Description |
|-------|------|---------|-----------|-------------|
| output_directory | Optional[str] | None | ✅ | Custom output directory |
| conflict_policy | ConflictPolicy | ASK | ✅ | File conflict resolution |
| auto_delete_source | bool | False | ✅ | Delete source after success |
| window_geometry | Optional[str] | None | ✅ | Window position/size |
| last_import_directory | Optional[str] | None | ✅ | Last import dir |
| **converter_engine** | **ConverterEngine** | **AVIDEMUX** | **✅** | **Selected converter** |

**Migration**: `from_dict()` handles missing `converter_engine` key by defaulting to `"avidemux"`.

### ConverterProtocol (Interface)

Common interface for converter implementations.

| Method | Signature | Description |
|--------|-----------|-------------|
| convert | `(job: ConversionJob) -> Generator[str, None, bool]` | Run conversion, yield output lines, return success |
| get_process | `() -> Optional[subprocess.Popen]` | Get currently running process (for cancellation) |
| is_available | `() -> bool` | Check if the converter binary exists |

**Implementations**:
- `FFmpegConverter` (existing, refactored to implement protocol)
- `AvidemuxConverter` (new)

### AvidemuxConverter

Wraps `avidemux_cli.exe` subprocess for .ts → .mp4 conversion.

| Attribute | Type | Description |
|-----------|------|-------------|
| _avidemux_path | Optional[Path] | Path to avidemux_cli.exe |
| _current_process | Optional[Popen] | Running subprocess (for cancellation) |

**Command construction**: `avidemux_cli.exe --load <input> --video-codec copy --audio-codec copy --output-format mp4 --save <output>`

**Conversion strategy**: Single-pass (no two-pass retry). If conversion fails, mark as Error.

## State Transitions

No new state transitions. The existing `ConversionStatus` enum
(PENDING → CONVERTING → COMPLETE/ERROR/CANCELLED/SKIPPED) applies equally to both engines.

## Relationships

```
AppSettings --[has]--> ConverterEngine (enum value)
ConversionWorker --[uses]--> ConverterProtocol (selected based on settings)
ConverterProtocol <|-- FFmpegConverter
ConverterProtocol <|-- AvidemuxConverter
```

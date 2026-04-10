# ts2mp4

Convert MPEG-TS (`.ts`) files to MP4 **without CPU re-encoding**.

Both tools use **ffmpeg stream-copy** (`-c copy`), which remuxes the
container from MPEG-TS to MP4 without decoding or re-encoding any
video/audio streams.  The CPU load is negligible — only the container
wrapper changes.

---

## Requirements

- [ffmpeg](https://ffmpeg.org/download.html) must be installed and on `PATH`.

```bash
# Debian / Ubuntu
sudo apt install ffmpeg

# macOS (Homebrew)
brew install ffmpeg
```

---

## Shell script — `ts2mp4.sh`

```bash
# Single file (output derived automatically)
./ts2mp4.sh video.ts          # -> video.mp4

# Single file with explicit output path
./ts2mp4.sh video.ts out.mp4

# Batch conversion
./ts2mp4.sh *.ts
```

### Environment variable

| Variable | Default | Purpose |
|----------|---------|---------|
| `FFMPEG` | `ffmpeg` | Path to the ffmpeg binary |

---

## Python script — `ts2mp4.py`

```bash
# Single file (output derived automatically)
python ts2mp4.py video.ts              # -> video.mp4

# Single file with explicit output path
python ts2mp4.py video.ts -o out.mp4

# Batch conversion
python ts2mp4.py video1.ts video2.ts video3.ts
```

```
usage: ts2mp4 [-h] [-o output.mp4] input.ts [input.ts ...]

positional arguments:
  input.ts              One or more input .ts files.

options:
  -h, --help            show this help message and exit
  -o output.mp4, --output output.mp4
                        Output file path (single input only).
```

---

## How it works

```
ffmpeg -i input.ts -c copy -movflags +faststart -y output.mp4
```

| Flag | Effect |
|------|--------|
| `-c copy` | Copy all streams as-is — **no decoding or re-encoding** |
| `-movflags +faststart` | Move the MP4 index to the front for faster streaming / seeking |
| `-y` | Overwrite output file if it already exists |

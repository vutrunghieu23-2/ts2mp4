# Sample Test Files

This directory contains sample `.ts` files for integration testing.

## sample.ts

A small valid MPEG-TS file for testing conversion. This file should be generated
using FFmpeg with the following command:

```powershell
ffmpeg -f lavfi -i testsrc=duration=2:size=320x240:rate=25 -f lavfi -i sine=frequency=440:duration=2 -c:v libx264 -preset ultrafast -c:a aac -f mpegts tests/sample_files/sample.ts
```

If FFmpeg is not available, integration tests that require a valid `.ts` file will be
skipped automatically.

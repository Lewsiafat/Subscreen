---
name: deploy
description: >
  Deploy src/ files to Raspberry Pi Pico device via mpremote.
  Use when the user says "deploy", "部署", "上傳到 Pico", "upload to device",
  or wants to transfer code to the Pico board. Excludes __pycache__ and .DS_Store.
---

# Deploy to Pico

Upload all files from `src/` to the Pico device root, excluding `__pycache__` and `.DS_Store`.

## Usage

Run the deploy script from the project root:

```bash
bash .claude/skills/deploy/scripts/deploy.sh
```

## What It Does

1. Checks that `mpremote` is installed
2. Iterates all files in `src/`, skipping `__pycache__/` and `.DS_Store`
3. Creates directories on device as needed
4. Copies each file via `mpremote cp`

## Prerequisites

- Pico device connected via USB
- `mpremote` installed (`pip install mpremote`)
- Only one Pico device connected (or set `MPREMOTE_DEVICE` env var)

## Troubleshooting

- **"mpremote not found"** — Run `pip install mpremote`
- **Device not detected** — Check USB cable, try `mpremote connect list`
- **Permission error** — On macOS/Linux, ensure user has USB device access

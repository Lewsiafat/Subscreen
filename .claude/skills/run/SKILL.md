---
name: run
description: >
  Run Picore-W on Pico device via mpremote. Use when the user says "run",
  "執行", "跑", "啟動", "run debug", "執行除錯", or wants to execute code
  on the Pico board. Supports two modes: normal (main.py) and debug
  (main_debug.py with display dashboard).
---

# Run on Pico

Execute Picore-W on the connected Pico device via `mpremote run`.

## Modes

**Normal mode** — pure WiFi management, no display:
```bash
cd src/ && mpremote run main.py
```

**Debug mode** — with Pico Explorer display dashboard:
```bash
cd src/ && mpremote run main_debug.py
```

## Procedure

1. Ask the user which mode to run (if not specified):
   - **Normal** (default) — `main.py`
   - **Debug** — `main_debug.py` (requires Pico Explorer hardware)

2. Run the selected entry point with `mpremote run` from the `src/` directory.

3. The command runs interactively — output streams to terminal. User can press Ctrl+C to stop.

## Notes

- `mpremote run` executes code directly without uploading. Use `/deploy` first if files need to be on device.
- Debug mode requires Pico Explorer board with 2.8" display and buttons (GPIO 12-15).
- Pico must be connected via USB with no other serial connections active.

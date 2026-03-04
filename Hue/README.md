# Hue (Local Room Controller)

A local-only Philips Hue controller that discovers rooms on your Hue Bridge and lets you:
- Select a room
- View current on/off + brightness
- Activate a scene
- Adjust brightness (final trim)

This repo is structured to scale like a real Python project:
- `src/hue_async/clients/` → reusable Hue API client (HTTP + headers)
- `src/hue_async/services/` → business logic (rooms/scenes/state)
- `scripts/` → thin CLI entrypoints / utilities

> Everything runs on your local network. Nothing is exposed to the internet unless you explicitly port-forward.

---

## Requirements

- Philips Hue Bridge on the same local network as your Mac
- Python 3.11+ recommended

---

## Install

### 1) Create + activate a virtualenv
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip

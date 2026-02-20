# WIS — Webhook Image Sender

A desktop app that monitors folders for new images and automatically sends them to one or more webhook URLs

## Features

- **Multiple folders** — monitor any number of directories simultaneously, each with an independent enable toggle and optional recursive subfolder scanning
- **Multiple webhooks** — send every detection to all enabled webhooks at once
- **Sound notifications** — plays `validation.mp3` on success and `exclamation.mp3` on failure (volume adjustable)
- **Auto-start** — optionally begin monitoring immediately on launch
- **Persistent settings** — all configuration is saved between sessions
- **Debug mode** — verbose scan logging to help troubleshoot detection issues
- **Supported formats** — `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp` (configurable)

## Requirements

- Python 3.7+
- `requests`
- `pygame` (optional — required for sound notifications)

```bash
pip install requests pygame
```

> `tkinter` is included with most standard Python installations. If missing: `sudo apt install python3-tk` (Debian/Ubuntu)

## Usage

```bash
python WIS.py
```

1. Click **Manage Folders** to add the directories you want to monitor
2. Click **Manage Webhooks** to add your webhook URLs
3. Optionally check **Auto-start on launch**
4. Click **Start Monitoring**

## Folder Manager

Each folder entry has two toggles :

| Toggle | Effect |
|---|---|
| On/Off | Include or exclude this folder from the current session |
| Recursive | Also scan all subfolders within the directory |

## Webhook Manager

Add as many webhooks as needed. When a new image is detected, WIS sends it to every enabled webhook. Each delivery is logged individually with its success or failure status

## Settings

Click the **Settings** button to configure :

| Setting | Default | Description |
|---|---|---|
| Scan rate | `1.0 s` | How often folders are polled |
| Send timeout | `30 s` | HTTP request timeout per webhook |
| File settle delay | `0.8 s` | Wait after detection before sending |
| Extensions | `.jpg,.jpeg,.png,.gif,.bmp,.webp` | Watched file types |
| Sound enabled | On | Play sounds on send success / failure |
| Volume | `0.8` | Sound volume from `0.0` to `1.0` |
| Colours | — | Full UI colour customisation via hex codes |

All settings are saved to `webhook_settings.json` in the same directory as `WIS.py`

## Sound Notifications

Place `validation.mp3` and `exclamation.mp3` in the same directory as `WIS.py`. WIS will play :

- `validation.mp3` — when a file is successfully delivered to **all** webhooks
- `exclamation.mp3` — when delivery fails on **any** webhook

Sounds require `pygame`. If it is not installed, a notice is shown in the Settings menu

## How It Works

When monitoring starts, WIS snapshots all existing image files in each folder and marks them as already seen. It then polls at the configured scan rate. When a new image appears, WIS waits for the file settle delay, verifies the file is non-empty, and POSTs it to every enabled webhook as `multipart/form-data`

HTTP `200`, `201`, and `204` are treated as success. Anything else, or a network error, is logged and counts as a failure

## Notes

- The seen-files list resets each time monitoring is stopped and restarted
- Webhook endpoints must accept `multipart/form-data` file uploads
- Colour changes require an app restart to apply fully

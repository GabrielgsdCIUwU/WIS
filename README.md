# WIS — Webhook Image Sender

A desktop application that monitors folders for new images and automatically sends them to one or more Discord-compatible webhook URLs

## Features

- **Multiple folders** — monitor any number of directories simultaneously, each with independent enable/disable and optional recursive subfolder scanning
- **Multiple webhooks** — send every detected image to all enabled webhooks at once
- **Shared profiles** — create named identities (username + avatar URL) to override webhook default appearance per webhook
- **Statistics dashboard** — comprehensive analytics including sends per month, per webhook, per folder, file type breakdowns, error tracking, and a full recent-send history
- **Theme system** — 4 built-in color presets, live color editor with swatch previews, custom theme saving, and import/export via `.wistheme` files
- **Sound notifications** — plays `validation.mp3` on success and `exclamation.mp3` on failure (volume adjustable; requires `pygame`)
- **Auto-start** — optionally begin monitoring automatically on application launch
- **Persistent settings** — all configuration saved to `wis_settings.json` between sessions
- **Debug mode** — verbose scan logging for troubleshooting
- **Supported formats** — `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp` (configurable)

## Requirements

- **Python 3.7+**
- **tkinter** (included with most Python distributions; `sudo apt install python3-tk` on Debian/Ubuntu if missing)
- **requests** — HTTP client for webhook delivery
- **pygame** — optional, required for sound notifications

Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

The project includes convenience scripts that automatically create a virtual environment and install dependencies:

### Windows

Simply run the batch file:
```bash
run_wish_windows.bat
```

This creates `.venv`, installs requirements, and launches the app without a persistent console window.

### Linux / macOS

```bash
chmod +x run_wish_linux.sh
./run_wish_linux.sh
```

### Manual Setup

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Usage

1. Launch the app: `python main.py`
2. Click **Manage Folders** to add directories to monitor
3. Click **Manage Webhooks** to add webhook endpoints
4. *(Optional)* Configure **Settings** (scan rate, file extensions, sound, etc.)
5. Click **Start Monitoring**

## Folder Manager

Configure which directories to scan:

| Control | Effect |
|---|---|
| **On/Off toggle** | Enable or disable this folder for the current session |
| **Recursive toggle** | Include all subdirectories within this folder |

All enabled folders are scanned simultaneously at the configured scan rate.

## Webhook Manager

Each webhook can have:

- **Name** — label for logs and statistics
- **URL** — the Discord webhook endpoint (must start with `http`)
- **Enable/Disable toggle** — include or exclude from sending
- **Shared Profile (optional)** — assign a named identity to override the webhook's default username and avatar

When an image is detected, it is sent to every enabled webhook. Each delivery is logged individually.

## Shared Profiles

Create reusable identities to customize how images appear on Discord:

1. Click **Settings** → **Manage Shared Profiles**
2. Enter a **Profile Name** (e.g., "Bot Account")
3. Enter a **Display Username** (how it appears on Discord)
4. Optionally add an **Avatar Image URL** (must be a direct `https://` link)
5. Save the profile

Then, in **Webhook Manager**, enable **Shared Profile** for any webhook and select which profile to use. The profile's username and avatar override the webhook's defaults.

## Settings

Click **Settings** to configure all options:

### Behaviour

| Setting | Default | Description |
|---|---|---|
| Scan rate | `15.0 s` | How often folders are polled for new files |
| Send timeout | `15 s` | HTTP request timeout per webhook |
| File settle delay | `0.8 s` | Wait after file detection before sending |

### Watched Extensions

Configure which file types to monitor (comma-separated, e.g., `.jpg,.png,.gif`).

Default: `.jpg,.jpeg,.png,.gif,.bmp,.webp`

### Sound Notifications

| Setting | Default | Description |
|---|---|---|
| Enable sounds | On | Play notification sounds |
| Volume | `0.8` | Volume from `0.0` to `1.0` |

Requires `pygame`. If not installed, a notice is shown in Settings.

### Startup & Debug

| Setting | Default | Description |
|---|---|---|
| Auto-start monitoring | Off | Begin monitoring automatically on app launch |
| Debug mode | Off | Log every scan cycle to the activity log |

### Statistics Configuration

| Setting | Default | Description |
|---|---|---|
| Max send records | `10,000` | Number of send entries kept in history |
| Max error records | `2,000` | Number of error entries kept in history |
| Months in bar chart | `12` | Number of months shown in Overview chart |
| Autosave every N sends | `10` | How frequently to persist stats to disk |

### Theme Presets & Color Editor

#### Built-in Presets

- **Dark Blue (default)** — deep navy with blue accent
- **Nord** — arctic, north-bluish palette
- **Dracula** — purple-tinted dark theme
- **Light** — clean light theme with dark text

#### Color Editor

All UI colors are editable via hex input with live swatch previews. Changes apply after clicking **Save & Close**. A full app restart ensures colors apply everywhere.

#### Custom Presets

1. Adjust colors in the editor
2. Enter a name in **Save as** and click **Save Preset**
3. Your preset appears in the dropdown and persists between sessions
4. To delete a custom preset, select it and click **Delete Custom**

#### Import / Export

- **Export Theme** — save current colors to a `.wistheme` file to share
- **Import Theme** — load a `.wistheme` or `.json` file and optionally save it as a custom preset

#### Theme Folder

Point to a folder containing `.wistheme` / `.json` theme files to load them as additional presets. Click **Reload Folder Themes** to refresh.

## Statistics Dashboard

Click **Statistics** to view comprehensive analytics across five tabs:

| Tab | Contents |
|---|---|
| **Overview** | Summary cards (total sent, successful, failed, success rate, error count); a bar chart of monthly sends; a pie chart of sends by file extension |
| **Webhooks** | Bar chart of sends per webhook; table with per-webhook sent/failed/success-rate breakdown |
| **Folders** | Bar chart of sends per folder; detail table with paths and counts |
| **Errors** | Side-by-side pie/bar chart of error types; recent error log with timestamp, type, file, webhook, and details |
| **Recent** | Chronological table of last 500 sends (time, filename, webhook, folder, extension, OK/Fail status) |

### Statistics Controls

- **↻ Refresh** — update all charts with latest data
- **Clear All Stats** — delete entire statistics history (cannot be undone)

Statistics persist to `wis_stats.json`.

## Sound Notifications

Place `validation.mp3` and `exclamation.mp3` in the application root directory (same location as `main.py`).

WIS will play:

- **`validation.mp3`** — when an image is successfully sent to **all** enabled webhooks
- **`exclamation.mp3`** — when delivery fails on **any** webhook

Requires `pygame` to be installed. If missing, sounds are silently skipped and a notice appears in Settings.

## How It Works

1. **Snapshot** — When monitoring starts, all existing image files in configured folders are marked as seen
2. **Polling** — Folders are scanned at the configured scan rate
3. **Detection** — When a new image is found, WIS waits for the file settle delay, then verifies the file is non-empty
4. **Delivery** — The image is POSTed to every enabled webhook as `multipart/form-data`
5. **Logging** — HTTP 200, 201, or 204 responses are treated as success; anything else logs a failure
6. **Notifications** — A sound plays and statistics are updated

The seen-files list resets each time monitoring is stopped and restarted.

## Data Files

| File | Location | Purpose |
|---|---|---|
| `wis_settings.json` | App root | All settings, webhooks, folders, shared profiles, custom themes |
| `wis_stats.json` | App root | Send history and error log for the Statistics dashboard |

Both files are created automatically on first run.

## Project Structure

```
WIS/
├── main.py                          # Entry point
├── requirements.txt                 # Python dependencies
├── run_wish_windows.bat             # Windows startup script
├── run_wish_linux.sh                # Linux startup script
├── README.md
├── core/
│   ├── __init__.py
│   ├── config.py                    # Global constants, themes, SettingsStore, StatisticsStore
│   ├── events.py                    # Abstract interfaces (ISender, IAudioPlayer, IChartWidget)
│   └── app.py                       # Application bootstrap (deprecated in favor of main.py)
├── models/
│   └── __init__.py
├── services/
│   ├── __init__.py
│   ├── sender.py                    # HttpSender & NullSender implementations
│   ├── scanner.py                   # FolderScanner for directory traversal
│   ├── monitor.py                   # MonitoringService (background polling & sending)
│   ├── audio.py                     # PygameAudioPlayer & NullAudioPlayer
│   └── stats_manager.py             # Theme folder loading helper
├── ui/
│   ├── __init__.py
│   ├── main_window.py               # WIS: root application window
│   ├── styles/
│   │   └── theme_manager.py         # Theme helpers & widget factories
│   ├── components/
│   │   ├── __init__.py
│   │   ├── factory.py               # BasePopup, mk_entry, mk_chk
│   │   ├── tree_panel.py            # Reusable Treeview wrapper
│   │   └── charts.py                # BarChart & PieChart widgets
│   └── dialogs/
│       ├── __init__.py
│       ├── folder_manager.py        # FolderManager dialog
│       ├── webhook_manager.py       # WebhookManager dialog
│       ├── profile_manager.py       # SharedProfileManager dialog
│       ├── settings_manager.py      # SettingsManager dialog
│       └── stats_dashboard.py       # StatsWindow analytics dashboard
```

## Troubleshooting

### No images are being detected

1. Ensure the folder path is correct and readable
2. Enable **Debug mode** in Settings to see per-scan logs
3. Verify the file extensions match (check **Settings → Watched Extensions**)
4. Confirm the **File settle delay** is not too short for your system

### Webhooks are not receiving images

1. Verify the webhook URL is correct (must start with `http://` or `https://`)
2. Check that the webhook endpoint accepts `multipart/form-data` uploads
3. Review the **Activity Log** for error messages
4. Check the **Statistics → Errors** tab for detailed failure reasons

### Sounds are not playing

1. Ensure `validation.mp3` and `exclamation.mp3` are in the app root directory
2. Check that `pygame` is installed: `pip install pygame`
3. Verify your system volume is not muted
4. Confirm sound is enabled in **Settings**

### Theme colors not applying

Changes to colors in the editor take effect after clicking **Save & Close**. A full app restart ensures all UI elements update.

## Notes

- The seen-files list resets when monitoring is stopped and restarted
- Webhook endpoints must accept `multipart/form-data` file uploads
- Large images may exceed timeout limits; increase **Send timeout** if needed
- Statistics are automatically trimmed to the configured maximums upon save

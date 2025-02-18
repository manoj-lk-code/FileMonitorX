
# FileMonitorX [Created using Claude]

FileMonitorX is a Windows service that monitors a specified directory for new files and automatically uploads them to a webhook endpoint. It features a system tray interface and robust file handling capabilities.

## Features

- 🔍 Real-time file monitoring
- 🚀 Automatic file upload to webhook endpoint
- 🛡️ Configurable file/folder exclusions
- 🔄 Duplicate file detection
- ⚙️ YAML-based configuration

## Prerequisites

- Python 3.x
- Windows OS
- Required Python packages (Make sure to install these python libraries):
  - psutil
  - PyQt5
  - watchdog
  - pyyaml
  - requests

## Installation & Setup

1. Download the latest release from the repository
2. Extract all files to your desired location
3. Modify the `config.yaml` file with your settings:
   - Set the directory path you want to monitor
   - Add your webhook URL
   - Configure any file extensions or folders to ignore
4. Double-click `start_monitor.bat` to run the service
   - The script will automatically check for required Python packages and install them if missing
   - A system tray icon will appear when the service starts successfully

# Running the Service:

**Option 1 - Manual Start (Recommended):**
- Navigate to the folder containing the FileMonitorX files
- Double-click `start_monitor.bat` to run the service
- This ensures all required files are available and in the correct directory

**Option 2 - Automatic Startup: [ask ChatGPT to update the code]**
If you want the service to start automatically with Windows, you have two choices:

1. Modified Batch File:
   - Create a copy of `start_monitor.bat`
   - Edit the copy to include the full path to your FileMonitorX directory
   - Add a `cd` command to change to that directory
   - Place this modified batch file in your Windows startup folder (Win + R → `shell:startup`)

2. Task Scheduler:
   - Open Windows Task Scheduler
   - Create a new task that runs at startup
   - Set the "Start in" directory to your FileMonitorX folder
   - Set the action to run `start_monitor.bat`

Note: The service must be able to access all its files (control.py, monitor.py, config.yaml) to function properly. Always ensure these files are present in the working directory.

## Using FileMonitorX

### Starting the Service
- Double-click `start_monitor.bat`
- Look for the system tray icon indicating the service is running
- The service will automatically monitor your specified directory

### System Tray Features
Right-click the system tray icon to:
- View the monitored directory
- Check service status
- Exit the service

### Control Commands
The service can be managed using these commands:
- Start: `control.py start`
- Stop: `control.py stop`
- Status check: `control.py status`

## Configuration Guide

The `config.yaml` file controls service behaviour. Key settings include:

1. Monitoring Path:
   - Set the directory you want to monitor
   - Use double backslashes for Windows paths

2. Webhook URL:
   - Add your webhook endpoint for file uploads

3. File Exclusions:
   - List extensions to ignore (e.g., .tmp, .log)
   - Specify folders to skip

4. Monitoring Options:
   - Enable/disable recursive monitoring of subdirectories

## Troubleshooting

For any issues, Please talk to your developer or use ChatGPT to troubleshoot the issue. No support will be provided with this Github Repo.

import os
import sys
import yaml
import json
import time
import hashlib
import requests
import signal
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

class FileMonitorTray(QWidget):
    def __init__(self, observer, config):
        super().__init__()
        self.observer = observer
        self.config = config
        self.setWindowTitle("FileMonitorX")
        self.init_ui()

    def init_ui(self):
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # If you have an icon file:
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'monitor.ico')
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # Use default system icon if custom icon not found
            self.tray_icon.setIcon(QIcon.fromTheme("system-file-manager"))

        # Create tray menu
        tray_menu = QMenu()
        
        # Add status item
        status_action = tray_menu.addAction('FileMonitorX Running')
        status_action.setEnabled(False)
        
        # Add watched directory item
        watch_dir = tray_menu.addAction(f'Watching: {self.config["monitoring"]["path"]}')
        watch_dir.setEnabled(False)
        
        tray_menu.addSeparator()
        
        # Add quit option
        quit_action = tray_menu.addAction('Exit')
        quit_action.triggered.connect(self.cleanup_and_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.setToolTip('FileMonitorX - Active')

    def cleanup_and_quit(self):
        self.observer.stop()
        self.observer.join()
        pid_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'filemonitorx.pid')
        if os.path.exists(pid_file):
            os.remove(pid_file)
        QApplication.quit()

class FileAdditionHandler(FileSystemEventHandler):
    def __init__(self, config):
        self.config = config
        self.webhook_url = config['monitoring']['webhook_url']
        self.processed_files_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'processed_files.json'
        )
        self.processed_files = self._load_processed_files()
        self.ignore_extensions = set(config['monitoring']['ignore_extensions'])
        self.ignore_folders = set(config['monitoring']['ignore_folders'])

    def _load_processed_files(self):
        try:
            if os.path.exists(self.processed_files_path):
                with open(self.processed_files_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self._log_error(f"Error loading processed files: {e}")
            return {}

    def _save_processed_files(self):
        try:
            with open(self.processed_files_path, 'w') as f:
                json.dump(self.processed_files, f, indent=2)
        except Exception as e:
            self._log_error(f"Error saving processed files: {e}")

    def _log_message(self, message):
        log_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'file_monitor.log'
        )
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"{timestamp} - {message}"
        print(log_entry)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')

    def _log_error(self, message):
        self._log_message(f"ERROR: {message}")

    def _should_ignore_file(self, file_path):
        path = Path(file_path)
        if path.suffix.lower() in self.ignore_extensions:
            return True
        for parent in path.parents:
            if parent.name in self.ignore_folders:
                return True
        return False

    def _calculate_file_hash(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            self._log_error(f"Error calculating file hash: {e}")
            return None

    def on_created(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        self._log_message(f"New file detected: {file_path}")

        if self._should_ignore_file(file_path):
            self._log_message(f"Ignoring file: {file_path}")
            return

        # Wait for file to be completely written
        time.sleep(1)

        file_hash = self._calculate_file_hash(file_path)
        if not file_hash:
            return

        if file_hash not in self.processed_files:
            try:
                file_info = {
                    'file_name': os.path.basename(file_path),
                    'timestamp': datetime.now().isoformat(),
                    'file_size': os.path.getsize(file_path),
                    'file_hash': file_hash
                }

                self._log_message(f"Sending file: {file_path}")
                
                with open(file_path, 'rb') as f:
                    files = {
                        'file': (os.path.basename(file_path), f, 'application/octet-stream')
                    }
                    response = requests.post(
                        self.webhook_url,
                        files=files,
                        data={'info': json.dumps(file_info)},
                        timeout=30
                    )

                if response.status_code == 200:
                    self._log_message(f"Successfully sent file: {file_path}")
                    self.processed_files[file_hash] = file_info
                    self._save_processed_files()
                else:
                    self._log_error(f"Failed to send webhook: {response.status_code}")
                    self._log_error(f"Response: {response.text[:500]}")

            except Exception as e:
                self._log_error(f"Error processing file {file_path}: {str(e)}")

def write_pid():
    """Write current process ID to PID file"""
    try:
        pid_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'filemonitorx.pid')
        with open(pid_path, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except Exception as e:
        print(f"Error writing PID file: {e}")
        return False

def main():
    if not write_pid():
        sys.exit(1)

    try:
        # Load configuration
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Initialize Qt Application
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        # Create the event handler and observer
        event_handler = FileAdditionHandler(config)
        observer = Observer()
        observer.schedule(
            event_handler,
            config['monitoring']['path'],
            recursive=config['monitoring'].get('recursive', False)
        )

        # Start the observer
        observer.start()
        
        # Create system tray
        tray = FileMonitorTray(observer, config)
        
        print(f"FileMonitorX started with PID {os.getpid()}")
        print(f"Watching directory: {config['monitoring']['path']}")

        # Start Qt event loop
        sys.exit(app.exec_())

    except Exception as e:
        print(f"Error in main loop: {e}")
        pid_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'filemonitorx.pid')
        if os.path.exists(pid_file):
            os.remove(pid_file)
        sys.exit(1)

if __name__ == "__main__":
    main()
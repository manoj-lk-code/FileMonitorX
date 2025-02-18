import os
import sys
import psutil
import signal
import subprocess
import time
import traceback
from datetime import datetime
from pathlib import Path

def log_message(message):
    """Log a message with timestamp"""
    log_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'control_log.txt'
    )
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"{timestamp} - {message}"
    print(log_entry)
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_entry + '\n')

def get_script_directory():
    """Get the directory where the script is located"""
    return os.path.dirname(os.path.abspath(__file__))

def get_pid_file_path():
    """Get the path to the PID file"""
    return os.path.join(get_script_directory(), 'filemonitorx.pid')

def get_monitor_script_path():
    """Get the path to the monitor script"""
    return os.path.join(get_script_directory(), 'monitor.py')

def is_monitor_running():
    """Check if the FileMonitorX process is running"""
    pid_file = get_pid_file_path()
    
    if not os.path.exists(pid_file):
        log_message("FileMonitorX PID file not found")
        return False
        
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        log_message(f"Found FileMonitorX PID: {pid}")
            
        process = psutil.Process(pid)
        is_running = process.is_running() and 'python' in process.name().lower()
        log_message(f"FileMonitorX process is running: {is_running}")
        return is_running
    except (psutil.NoSuchProcess, ProcessLookupError, ValueError):
        log_message(f"Process not found or invalid PID")
        return False
    except Exception as e:
        log_message(f"Error checking FileMonitorX process: {str(e)}")
        return False

def kill_existing_monitor():
    """Kill any existing FileMonitorX processes"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline'] and 'monitor.py' in ' '.join(proc.info['cmdline']):
                    log_message(f"Killing existing process: {proc.info['pid']}")
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        log_message(f"Error killing existing processes: {str(e)}")

def start_monitor():
    """Start the FileMonitorX process"""
    try:
        if is_monitor_running():
            log_message("FileMonitorX is already running!")
            return

        # Kill any existing processes first
        kill_existing_monitor()

        # Clean up existing PID file if any
        if os.path.exists(get_pid_file_path()):
            os.remove(get_pid_file_path())

        monitor_script = get_monitor_script_path()
        log_message(f"Starting FileMonitorX at: {monitor_script}")
        
        if not os.path.exists(monitor_script):
            log_message(f"Error: FileMonitorX script not found at {monitor_script}")
            return

        if os.name == 'nt':  # Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            process = subprocess.Popen(
                [sys.executable, monitor_script],
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:  # Linux/Mac
            process = subprocess.Popen(
                [sys.executable, monitor_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

        # Wait for PID file to be created
        time.sleep(2)
        
        if os.path.exists(get_pid_file_path()):
            with open(get_pid_file_path(), 'r') as f:
                pid = f.read().strip()
            log_message(f"FileMonitorX started successfully! PID: {pid}")
        else:
            log_message("Warning: FileMonitorX started but PID file not created")
            
    except Exception as e:
        log_message(f"Error starting FileMonitorX: {str(e)}")
        log_message(f"Traceback: {traceback.format_exc()}")

def stop_monitor():
    """Stop the FileMonitorX process"""
    try:
        pid_file = get_pid_file_path()
        
        if not os.path.exists(pid_file):
            log_message("FileMonitorX is not running! (No PID file found)")
            return

        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        log_message(f"Attempting to stop process with PID: {pid}")

        try:
            process = psutil.Process(pid)
            process.terminate()
            log_message(f"Sent termination signal to PID {pid}")
            process.wait(timeout=5)
        except psutil.NoSuchProcess:
            log_message(f"Process {pid} not found")
        except psutil.TimeoutExpired:
            log_message(f"Process {pid} did not terminate gracefully, forcing...")
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
            else:
                os.kill(pid, signal.SIGKILL)

        # Clean up PID file
        if os.path.exists(pid_file):
            os.remove(pid_file)
            log_message("Removed PID file")
            
        log_message("FileMonitorX stopped successfully!")
        
    except Exception as e:
        log_message(f"Error stopping FileMonitorX: {str(e)}")
        log_message(f"Traceback: {traceback.format_exc()}")

def status_monitor():
    """Check the status of FileMonitorX"""
    try:
        if is_monitor_running():
            pid_file = get_pid_file_path()
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            process = psutil.Process(pid)
            
            log_message(f"FileMonitorX is running (PID: {pid})")
            log_message(f"CPU Usage: {process.cpu_percent()}%")
            log_message(f"Memory Usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")
            
            # Check monitor script
            monitor_script = get_monitor_script_path()
            if os.path.exists(monitor_script):
                log_message(f"Monitor script exists: {monitor_script}")
            else:
                log_message(f"Monitor script not found: {monitor_script}")
                
        else:
            log_message("FileMonitorX is not running")
    except Exception as e:
        log_message(f"Error getting status: {str(e)}")
        log_message(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python control.py [start|stop|status]")
        sys.exit(1)

    command = sys.argv[1].lower()
    log_message(f"Received command: {command}")

    if command == "start":
        start_monitor()
    elif command == "stop":
        stop_monitor()
    elif command == "status":
        status_monitor()
    else:
        log_message(f"Invalid command: {command}")
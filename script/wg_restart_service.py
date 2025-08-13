import os
import datetime
import re
from subprocess import check_output, CalledProcessError, call

# Function to get the running date and uptime of a systemd service
def get_service_uptime(service_name):
    try:
        output = check_output(['systemctl', 'status', service_name]).decode('utf-8')
        lines = output.split('\n')
        
        for line in lines:
            if 'Active:' in line:
                active_status = line.strip()
                break
        
        match = re.search(r'(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})', active_status)
        
        if match:
            date_time = f"{match.group(1)} {match.group(2)}"

            format = "%Y-%m-%d %H:%M:%S"
        start_date = datetime.datetime.strptime(date_time, format)        
        
        return start_date
    except CalledProcessError as e:
        print(f"Failed to get status for {service_name}: {e}")
        return None

# Function to get the last modification date of a file
def get_file_modification_time(file_path):
    try:
        output = check_output(['stat', '-c', '%Y', file_path]).decode('utf-8').strip()
        mtime_datetime = datetime.datetime.fromtimestamp(int(output))
        return mtime_datetime
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None


FILE_PATH = "/root/pippo"
SERVICE_NAME = "wg-quick@wg0.service"

# Get the current time and system uptime
service_uptime_seconds = get_service_uptime(SERVICE_NAME)
mtime_datetime = get_file_modification_time(FILE_PATH)

if service_uptime_seconds is not None and mtime_datetime is not None:
    # Check if the service is older than the file
    if service_uptime_seconds < mtime_datetime:
        print(f"Restarting {SERVICE_NAME} as it is older than the file.")
        call(['systemctl', 'restart', SERVICE_NAME])
    else:
        print("No need to restart service, service is not older than the file.")
else:
    if service_uptime_seconds is None:
        print(f"Failed to get uptime for service: {SERVICE_NAME}")
    if mtime_datetime is None:
        print(f"Failed to get modification time for file: {FILE_PATH}")
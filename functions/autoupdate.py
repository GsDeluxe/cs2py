import os
import requests
import hashlib
import shutil
from pathlib import Path

def get_remote_version():
    """Get version from GitHub"""
    try:
        url = "https://raw.githubusercontent.com/GsDeluxe/cs2py/refs/heads/main/version.txt"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text.strip()
    except Exception as e:
        print(f"Error getting remote version: {e}")
        return None


def get_local_version():
    """Get local version"""
    try:
        version_file = Path("version.txt")
        if version_file.exists():
            with open(version_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return None
    except Exception as e:
        print(f"Error reading local version: {e}")
        return None


def calculate_file_hash(file_path):
    """Calculate MD5 hash of a file"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None


def get_remote_file_list():
    """Get file list from GitHub"""
    try:
        api_url = "https://api.github.com/repos/GsDeluxe/cs2py/git/trees/main?recursive=1"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        data = response.json()
        files = []

        for item in data.get('tree', []):
            if item['type'] == 'blob':
                files.append({
                    'path': item['path'],
                    'url': f"https://raw.githubusercontent.com/GsDeluxe/cs2py/refs/heads/main/{item['path']}"
                })

        return files
    except Exception as e:
        print(f"Error getting file list: {e}")
        return None


def get_remote_file_hash(url):
    """Get MD5 hash of remote file"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return hashlib.md5(response.content).hexdigest()
    except:
        return None


def download_file(url, local_path):
    """Download a file from GitHub"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        dir_name = os.path.dirname(local_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        with open(local_path, 'wb') as f:
            f.write(response.content)

        return True
    except Exception as e:
        print(f"Error downloading {local_path}: {e}")
        return False


def backup_files():
    """Backup current files"""
    backup_dir = "backup_old_version"
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)

    exclude_dirs = {'.git', '__pycache__', 'backup_old_version', '.vscode'}
    exclude_files = {'.gitignore'}

    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if file in exclude_files:
                continue

            src_path = os.path.join(root, file)
            if backup_dir in src_path:
                continue

            dst_path = os.path.join(backup_dir, src_path[2:])

            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            try:
                shutil.copy2(src_path, dst_path)
            except Exception as e:
                print(f"Warning: Could not backup {src_path}: {e}")

    print(f"Backup created at: {backup_dir}")


def update_project():
    """Update the project"""
    print("Getting file list from GitHub...")
    remote_files = get_remote_file_list()
    if not remote_files:
        print("Error: Failed to get file list")
        return False

    print(f"Files to check: {len(remote_files)}")

    print("Creating backup...")
    backup_files()

    # Normalize all remote paths for cross-platform comparison
    remote_paths = {os.path.normpath(f['path']) for f in remote_files}

    success_count = 0
    fail_count = 0
    skip_count = 0
    delete_count = 0

    # --- Update or download new files ---
    for file_info in remote_files:
        local_path = os.path.normpath(file_info['path'])
        remote_url = file_info['url']

        needs_update = True
        if os.path.exists(local_path):
            local_hash = calculate_file_hash(local_path)
            remote_hash = get_remote_file_hash(remote_url)

            if local_hash and remote_hash and local_hash == remote_hash:
                needs_update = False
                skip_count += 1
                print(f"Skipping (unchanged): {local_path}")
                continue

        if needs_update:
            print(f"Updating: {local_path}")
            if download_file(remote_url, local_path):
                success_count += 1
            else:
                fail_count += 1

    # --- Delete local files not in remote ---
    exclude_dirs = {'.git', '__pycache__', 'backup_old_version', '.vscode'}
    exclude_files = {'.gitignore'}

    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file in exclude_files:
                continue

            local_path = os.path.normpath(os.path.join(root, file))
            relative_path = os.path.normpath(os.path.relpath(local_path, '.'))

            if relative_path not in remote_paths and not relative_path.startswith("backup_old_version"):
                try:
                    os.remove(local_path)
                    print(f"Deleted (removed from remote): {relative_path}")
                    delete_count += 1
                except Exception as e:
                    print(f"Warning: Could not delete {relative_path}: {e}")

    print(f"\nUpdate complete:")
    print(f"  {success_count} updated")
    print(f"  {skip_count} unchanged")
    print(f"  {fail_count} failed")
    print(f"  {delete_count} deleted (no longer in repo)")

    return fail_count == 0


def check_and_update():
    """Check version and update if needed"""
    print("\nChecking for updates...")

    local_version = get_local_version()
    remote_version = get_remote_version()

    if not remote_version:
        print("Cannot connect to GitHub")
        return False

    print(f"Local version: {local_version}")
    print(f"Remote version: {remote_version}")

    if local_version == remote_version:
        print("Project is up to date")
        return True
    else:
        print("New version available! Updating...")

        user_input = input("Do you want to update? (y/N): ")
        if user_input.lower() in ['y', 'yes']:
            if update_project():
                print("Update completed successfully")
                print("Please restart the application")
                return True
            else:
                print("Error during update")
                return False
        else:
            print("Update cancelled")
            return False

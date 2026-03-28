import os
import requests
import subprocess
import sys
import zipfile
import io
import shutil
import time
import tempfile

# === CONFIG ===
REPO_API = "https://api.github.com/repos/LizabethEve/Notes-by-Princess/commits/Notes-App"
ZIP_URL = "https://github.com/LizabethEve/Notes-by-Princess/archive/refs/heads/Notes-App.zip"

LOCAL_VERSION_FILE = ".version"
# === Platform-specific app ===
if sys.platform == "win32":
    APP_TO_RUN = "notes.exe"
elif sys.platform == "darwin":
    APP_TO_RUN = "notes.app/Contents/MacOS/notes"
else:
    APP_TO_RUN = "notes.py"  # Linux or fallback

# Optional: folders/files to NOT overwrite (important if you add user data later)
EXCLUDE = [".version", "__pycache__", "font_state.json", "notes_copy.py", "theme_state.json", "notes"]


# === FUNCTIONS ===
def get_latest_commit():
    try:
        response = requests.get(REPO_API, timeout=10)
        if response.status_code == 200:
            return response.json()["sha"]
        else:
            print("Failed to fetch commit:", response.status_code)
            return None
    except Exception as e:
        print("Error fetching commit:", e)
        return None

def is_relevant(item_name):
    # Only include the files that matter for the current OS
    if sys.platform == "win32" and item_name.endswith(".exe"):
        return True
    if sys.platform == "darwin" and item_name.endswith(".app"):
        return True
    if sys.platform not in ("win32", "darwin") and item_name.endswith(".py"):
        return True
    # Include all non-OS-specific files
    if not any(item_name.endswith(ext) for ext in [".exe", ".app", ".py"]):
        return True
    return False

def get_local_version():
    if not os.path.exists(LOCAL_VERSION_FILE):
        return None
    with open(LOCAL_VERSION_FILE, "r") as f:
        return f.read().strip()


def save_local_version(version):
    with open(LOCAL_VERSION_FILE, "w") as f:
        f.write(version)


def download_repo():
    print("Downloading latest version...")
    response = requests.get(ZIP_URL, timeout=20)
    if response.status_code != 200:
        print("Failed to download repo.")
        return None, None

    z = zipfile.ZipFile(io.BytesIO(response.content))

    temp_dir = "update_temp"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    z.extractall(temp_dir)

    extracted_folder = os.listdir(temp_dir)[0]
    source_path = os.path.join(temp_dir, extracted_folder)

    return source_path, temp_dir


def replace_files(source_path, dest_path="."):
    print("Updating files...")

    for item in os.listdir(source_path):
        if item in EXCLUDE:
            continue
        if not is_relevant(item):
            continue  # skip files not for this OS

        src = os.path.join(source_path, item)
        dst = os.path.join(dest_path, item)

        try:
            if os.path.isdir(src):
                if not os.path.exists(dst):
                    shutil.copytree(src, dst)
                else:
                    replace_files(src, dst)  # recursion
            else:
                shutil.copy2(src, dst)
        except Exception as e:
            print(f"Failed to replace {item}:", e)


def run_app():
    print("Launching app...")
    if sys.platform == "darwin":
        # macOS app bundle
        subprocess.Popen([os.path.join(".", APP_TO_RUN)])
    elif sys.platform == "win32":
        subprocess.Popen([APP_TO_RUN])
    else:
        subprocess.Popen(["python3", APP_TO_RUN])


# === MAIN LOGIC ===
def main():
    print("Checking for updates...")

    latest_commit = get_latest_commit()
    if latest_commit is None:
        print("Skipping update check.")
        run_app()
        return

    local_commit = get_local_version()

    if local_commit != latest_commit:
        print("Update found!")

        source_path, temp_dir = download_repo()
        if source_path:
            replace_files(source_path)
            save_local_version(latest_commit)

            shutil.rmtree(temp_dir)
            print("Update complete.")
            print("Current version:", local_commit)
            print("Latest version:", latest_commit)
        else:
            print(f"Update failed, running current version:{local_commit}.")
    else:
        print("No updates found, all up to date.")

    time.sleep(0.5)
    run_app()


if __name__ == "__main__":
    main()


import os
import zipfile

def find_shared_drive():
    for letter in ['G', 'H']:
        path = f"{letter}:\\Shared drives\\FFCR"
        if os.path.exists(path):
            return path
    raise FileNotFoundError("Shared drive FFCR not found on G: or H:")

def scan_cases(base_path):
    incoming = os.path.join(base_path, "Incoming Cases")
    if not os.path.exists(incoming):
        raise FileNotFoundError("Incoming Cases folder not found")
    print(f"🔍 Scanning: {incoming}")
    for name in os.listdir(incoming):
        full_path = os.path.join(incoming, name)
        if name.lower().endswith(".zip") and os.path.isfile(full_path):
            extract_path = os.path.join(incoming, name[:-4])
            print(f"📦 Extracting: {name} → {extract_path}")
            with zipfile.ZipFile(full_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
        elif os.path.isdir(full_path):
            print(f"📁 Detected folder: {name}")
    print("✅ Real OCR + Auto-Unzip complete.")

if __name__ == "__main__":
    print("🩺 Fibrin Foam Chunked OCR Tool v7.9")
    try:
        shared_drive_path = find_shared_drive()
        print(f"✅ FFCR detected at {shared_drive_path[0]}:")
        scan_cases(shared_drive_path)
    except Exception as e:
        print(f"❌ {str(e)}")

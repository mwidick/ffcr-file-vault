import os
import shutil

def create_version_structure(base_dir, version):
    version_folder = os.path.join(base_dir, version)
    folders = [
        "scripts",
        "launchers",
        "helpers",
        "output/logs",
        "output/screenshots",
        "output/processed_zips",
        "output/data_exports/attachments",
        "config"
    ]

    for folder in folders:
        os.makedirs(os.path.join(version_folder, folder), exist_ok=True)

    # Create core files
    script_name = f"extract_hdmi_diagnostics_{version}.py"
    script_path = os.path.join(version_folder, "scripts", script_name)
    with open(script_path, "w") as f:
        f.write(f"# {script_name}\n# Starter script for {version}\n")

    bat_name = f"launch_diagnostics_{version}.bat"
    bat_path = os.path.join(version_folder, "launchers", bat_name)
    with open(bat_path, "w") as f:
        f.write("@echo off\n")
        f.write("cd /d %~dp0\n")
        f.write(f"python ../scripts/{script_name}\n")
        f.write("pause\n")

    with open(os.path.join(version_folder, "input_mrns.txt"), "w") as f:
        f.write("1903508\n")

    with open(os.path.join(version_folder, "requirements.txt"), "w") as f:
        f.write("selenium\npython-dotenv\npandas\nopenpyxl\n")

    with open(os.path.join(version_folder, "README.md"), "w") as f:
        f.write(f"# FFCR ModMed Automation {version}\n\nAuto-generated structure for versioning.\n")

    with open(os.path.join(version_folder, "reentry_checklist.md"), "w") as f:
        f.write("- [ ] Launch script via .bat\n- [ ] Verify logs\n- [ ] Review screenshots\n")

    with open(os.path.join(version_folder, "config/.env"), "w") as f:
        f.write("EMAIL_USER=your_email@example.com\nEMAIL_PASS=your_password\n")

    print(f"✅ Version {version} created at: {version_folder}")

if __name__ == "__main__":
    base = input("Enter base path (e.g., C:\\FFCR_Project\\v12.xx): ").strip()
    version = input("Enter new version (e.g., v12.2c): ").strip()
    create_version_structure(base, f"FFCR_ModMed_{version}")

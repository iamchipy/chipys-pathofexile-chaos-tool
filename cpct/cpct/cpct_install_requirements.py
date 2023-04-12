import sys
import subprocess

SCRIPT_NAME = "Chipy's PathOfExile Chaos Tool"
installDependencyErrors = 0
installDependencyMessage = ""

# List of packages to install with pip
dependenciesInstall = ["requests","PyQt5", "websockets", "pywinauto", "pyautogui", "psutil"]

# List of packages to update with pip
dependenciesUpdate = ["PyQt5"]

# Make sure pip is updated
print("Checking pip is updated...")
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
except Exception as e:
    error = "ERROR: Unable to update pip."
    print(error, e)
    installDependencyMessage += f"    - {error}\n"
    installDependencyErrors += 1

# Install packages
for dependency in dependenciesInstall:
    print(f"\nInstalling {dependency}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", dependency])
    except Exception as e:
        error = f"ERROR: Unable to install {dependency}."
        print(error, e)
        installDependencyMessage += f"    - {error}\n"
        installDependencyErrors += 1

# Update packages
for dependency in dependenciesUpdate:
    print(f"\nUpdating {dependency}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", dependency])
    except Exception as e:
        error = f"ERROR: Unable to update {dependency}."
        print(error, e)
        installDependencyMessage += f"    - {error}\n"
        installDependencyErrors += 1


if installDependencyErrors == 0:
    # Print finished with no errors
    print(f"\n\nPython Dependencies for {SCRIPT_NAME} successfully installed.\n\nYou can now run the main program with:\n    python main.py\n\nOr by double clicking on _START_HERE\n")
    input("Press Enter to close this window...")
else:
    # Report the errors found
    print(f"\n\nFailed to install Python Dependencies for {SCRIPT_NAME}.\n\nEncountered the following errors:")
    print(installDependencyMessage)
    print(f"You must fix these errors to use the {SCRIPT_NAME}.\n")
    print("Feel free to reach out to Chipy#2023 for help")
    input("Press Enter to close this window...")


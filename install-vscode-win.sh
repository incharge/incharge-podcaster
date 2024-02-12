# Install the latest stable vscode for Windows
#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR/.."

[ -f bin/vscode/Code.exe ] && {
	echo VScode is already installed. Exiting.
	return 1
}

[ -f installers/VSCode-win32-x64.zip ] || {
	echo Downloading the latest vscode zip for Windows
	curl.exe --fail --location --output "boot/VSCode-win32-x64.zip" --url "https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-archive"
}

echo Unzipping vscode
unzip installers/VSCode-win32-x64.zip -d bin/vscode

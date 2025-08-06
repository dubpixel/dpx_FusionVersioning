#!/bin/bash

echo "Starting Fusion 360 add-in installation..."

SOURCE_ADDIN_PATH="$(dirname "$0")/.."
echo "Source add-in folder resolved to: $SOURCE_ADDIN_PATH"

DEST_ADDINS_PATH="$HOME/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns"
echo "Destination AddIns folder: $DEST_ADDINS_PATH"

if [ ! -d "$SOURCE_ADDIN_PATH" ]; then
  echo "ERROR: Source add-in folder does not exist: $SOURCE_ADDIN_PATH"
  exit 1
fi

echo "Ensuring destination directory exists..."
mkdir -p "$DEST_ADDINS_PATH"
if [ $? -ne 0 ]; then
  echo "ERROR: Failed to create destination directory: $DEST_ADDINS_PATH"
  exit 1
fi

echo "Copying add-in folder with progress..."
rsync -a --progress "$SOURCE_ADDIN_PATH/" "$DEST_ADDINS_PATH/$(basename "$SOURCE_ADDIN_PATH")/"

if [ $? -eq 0 ]; then
  echo "Add-in copied successfully to: $DEST_ADDINS_PATH/$(basename "$SOURCE_ADDIN_PATH")"
else
  echo "ERROR: Failed to copy add-in."
  exit 1
fi

echo "Installation complete."

#!/bin/bash

# Path to your local add-in folder (change this to your actual add-in folder path)
SOURCE_ADDIN_PATH="$(dirname "$0")/.."

# Fusion 360 AddIns destination directory on macOS
DEST_ADDINS_PATH="$HOME/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns"

# Check if source folder exists
if [ ! -d "$SOURCE_ADDIN_PATH" ]; then
  echo "Source add-in folder does not exist: $SOURCE_ADDIN_PATH"
  exit 1
fi

# Create destination directory if it doesn't exist
mkdir -p "$DEST_ADDINS_PATH"

# Copy the add-in folder recursively (replace if exists)
cp -R "$SOURCE_ADDIN_PATH" "$DEST_ADDINS_PATH"

if [ $? -eq 0 ]; then
  echo "Add-in copied successfully to $DEST_ADDINS_PATH"
else
  echo "Failed to copy add-in."
  exit 1
fi

#!/usr/bin/env bash

# libicu* libraries vary a lot from system to system so we need to copy
# them along with Qt. The same is done with the official Qt installer.

TARGET_FOLDER=$1
if [ "$#" -ne 1 ]; then
    TARGET_FOLDER=.
fi
TARGET_BINARY=libQt6Core.so.6

# Array of ICU libraries to check
ICU_LIBRARIES=("libicui18n" "libicuuc" "libicudata")

for ICU_LIBRARY in "${ICU_LIBRARIES[@]}"; do
    # Get the full path of the ICU library from ldd
    LIBRARY_PATH=$(ldd $TARGET_BINARY | grep $ICU_LIBRARY | awk '{print $3}')
    
    # Check if the library path exists and is not empty
    if [ -n "$LIBRARY_PATH" ]; then
        # Copy the library to the target folder if it hasn't already been copied
        if [ ! -f "$TARGET_FOLDER/$(basename $LIBRARY_PATH)" ]; then
            cp "$LIBRARY_PATH" "$TARGET_FOLDER/"
        fi
    else
        echo "Warning: $ICU_LIBRARY not found in $TARGET_BINARY"
    fi
done

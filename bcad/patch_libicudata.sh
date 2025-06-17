#!/usr/bin/env bash

# Tools like rcc (used to compile Qml) use RUNPATH, but it doesn't work with indirect dependencies.
# libicu* libs need to be included with the Qt binaries because they vary a lot from system to system.
# And for some reason libQt6Core.so.6 no longer links directly with libicudata so it is not found by RUNPATH in lib, from libexec.
# Solution: we can use patchelf for libicudata as a dependency to libQt6Core.
# This is also done by linuxdeployqt, but we don't use it this early.

if [ "$#" -ne 1 ]; then
    echo "Need target binary as parameter!"
    exit 1
fi

TARGET_BINARY=$1
ICUDATA_LIBRARY=$(ldd $TARGET_BINARY | grep libicudata.so | awk '{print $1}')
                                                        
if [ -n "$ICUDATA_LIBRARY" ]; then
    # If ICUDATA_LIBRARY is not null, run patchelf
    ../bin/patchelf --remove-needed $ICUDATA_LIBRARY $TARGET_BINARY
    ../bin/patchelf --add-needed $ICUDATA_LIBRARY $TARGET_BINARY
else
    # If ICUDATA_LIBRARY is null, print an error message
    echo "Error: ICUDATA_LIBRARY not found!"
fi


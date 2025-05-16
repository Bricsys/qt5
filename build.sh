#!/bin/bash

# Default build type
BUILD_TYPE="release_debug"
ACTION_TYPE="build"

# Parse command line arguments
if [ "$1" == "debug" ]; then
  BUILD_TYPE="debug"
elif [ "$1" == "release" ]; then
  BUILD_TYPE="release"
fi

if [ "$2" == "generate" ]; then
  ACTION_TYPE="generate"
elif [ "$2" == "build" ]; then
  ACTION_TYPE="build"
elif [ "$2" == "checkout" ]; then
  ACTION_TYPE="checkout"
fi

# Set CMakeExeFolder from the third parameter, or default based on platform
if [ -n "$3" ]; then
  CMakeExeFolder="$3"
else
  case $OSTYPE in
    darwin*)
      Platform=mac
      CMakeExeFolder="${THIRDPARTY_PATH}/cmake/mac/bin"
      ;;
    *)
      Platform=linux
      CMakeExeFolder="${THIRDPARTY_PATH}/cmake/lin64/bin"
      ;;
  esac
fi

export PATH=$PATH:$CMakeExeFolder

python3 ./build_qt.py --qt_version=6.8.2 --action="$ACTION_TYPE" --platform=$Platform --build_type="$BUILD_TYPE" --qt_src_dir="./" --qt_build_dir="./build" --qt_install_dir="./install" --qtwebengine_bin_dir="${QTWEBENGINE_PATH}"


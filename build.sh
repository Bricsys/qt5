#!/bin/bash

# Default build type
BUILD_TYPE="release"
ACTION_TYPE="build"

# Parse command line arguments
while [ "$#" -gt 0 ]; do
  case "$1" in
    debug)
      BUILD_TYPE="debug"
      ;;
    release)
      BUILD_TYPE="release"
      ;;
    generate)
      ACTION_TYPE="generate"
      ;;
    build)
      ACTION_TYPE="build"
      ;;
    checkout)
      ACTION_TYPE="checkout"
      ;;
  esac
  shift
done

case $OSTYPE in
  darwin*)
    Platform=mac
    CMakeExeFolder=${THIRDPARTY_PATH}/cmake/mac/bin
  ;;  
  *) 
    Platform=linux
    CMakeExeFolder=${THIRDPARTY_PATH}/cmake/lin64/bin
  ;;  
esac

export PATH=$PATH:$CMakeExeFolder

python3 ./build_qt.py --qt_version=6.8.2 --action="$ACTION_TYPE" --platform=$Platform --build_type="$BUILD_TYPE" --qt_src_dir="./" --qt_build_dir="./build" --qt_install_dir="./install" --qtwebengine_bin_dir="D:/Qt_OSS_6_8_2_/6.8.2/msvc2022_64"


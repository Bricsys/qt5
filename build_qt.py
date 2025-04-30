#!/usr/bin/env python3

###
#
#  Build instructions
#
### Windows:
#
# 1. Open a CMD window.
# 2. Setup the environment (also make sure python3 is in the PATH). Example:
#   set PATH=%PATH%;"C:/Program Files/Microsoft Visual Studio/2022/Professional/VC/Tools/"
#   set PATH=%PATH%;"C:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja"
#   call "C:/Program Files/Microsoft Visual Studio/2022/Professional/VC/Auxiliary/Build/vcvarsall.bat" amd64
# 3. Make sure QtWebEngine binaries are installed with the Qt open source installer in a folder of its own.
# 4. Run with example command:
#   python3 build_qt.py --qt_version=6.8.2 --platform=windows --qtwebengine_bin_dir=D:/path/to/Qt/install/folder/6.8.2/msvc
#
### Linux:
#
# 1. Open a terminal.
# 2. Setup the environment (also make sure python3 is in the PATH). Example:
#     export PATH=$PATH:/home/alexandrub/Qt_6_8_2/Tools/CMake/bin
# 3. Make sure QtWebEngine binaries are installed with the Qt open source installer in a folder of its own.
# 4. Run with example command:
#   python3 build_qt.py --qt_version=6.8.2 --platform=linux --qtwebengine_bin_dir=/home/alexandrub/Qt_6_8_2_qtwebengine/6.8.2/gcc_64/
#
# Note: building 'xcbglintegrations' can be tricky because you need many related libxcb -dev (-devel) packages installed on your distro.
# You can look at qtbase/src/gui/configure.cmake for all that are needed. You can start with line:
#   qt_find_package(XCB 1.11 PROVIDED_TARGETS XCB::XCB MODULE_NAME gui QMAKE_LIB xcb)
#
# Example for Ubuntu 22.04 (do double check with the cmake script thought, the list might not be complete):
#   libxcb1-dev libxcb-xfixes0-dev libx11-xcb-dev libxcb-icccm4-dev libxcb-glx0-dev libxcb-image0-dev libxcb-keysyms1-dev libxcb-xinput-dev libxcb-cursor-dev libxcb-render-util0-dev libxcb-render0-dev libxcb-randr0-dev libxcb-shape0-dev libxcb-shm0-dev libxcb-sync-dev libxcb-xinput-dev
#

import os
import subprocess
import shutil
from pathlib import Path
import argparse
import sys
import time
import math
from enum import IntFlag

def run_command(command, cwd=None, env=None):
    """Run a shell command and handle errors."""
    print(f"Running command: {command} (in {cwd})")
    result = subprocess.run(command, shell=True, cwd=cwd, env=env)
    result.check_returncode()

def initialize_and_update_submodules(cmake_source_path, submodules, cwd, env):
    run_command(
        f'"{cmake_source_path / "configure"}" -init-submodules -submodules {submodules}',
        cwd=cwd,
        env=env
    )

def copy_with_overwrite(src_dir, dest_dir):
    """Copy contents of src_dir to dest_dir, overwriting existing files."""
    for item in src_dir.iterdir():
        s = item
        d = dest_dir / item.name
        if item.is_dir():
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

def suppress_xcode_check(cmake_source_path):
    try:
        file_path = cmake_source_path / "CMakeLists.txt"
        set_as_warning = "set(QT_FORCE_WARN_APPLE_SDK_AND_XCODE_CHECK ON [CACHE BOOL])\n"

        # Read the existing contents of the file
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        # Check if the setting is already set
        for i, line in enumerate(lines):
            if set_as_warning in line:
                return

        for i, line in enumerate(lines):
            if "cmake_minimum_required" in line:
                lines.insert(i + 1, set_as_warning)
                break

        # Write the updated contents back to the file
        with open(file_path, "w", encoding="utf-8") as file:
            file.writelines(lines)

    except Exception as e:
        print(f"Error modifying {file_path}: {e}")

class Action(IntFlag):
    NONE = 0
    CHECKOUT = 1 << 0
    GENERATE = 1 << 1
    BUILD = 1 << 2
    ALL = CHECKOUT | GENERATE | BUILD

def main():
    parser = argparse.ArgumentParser(description='Build Qt from source.')
    parser.add_argument('--qt_version', required='True', help='Build type: release, debug')
    parser.add_argument('--platform', required='True', help='Platform: windows, linux, mac')
    parser.add_argument('--qtwebengine_bin_dir', required=True, help='QtWebEngine pre-built directory')
    parser.add_argument(
        '--action',
        default='all',
        help='Comma-separated actions: checkout, generate, build, all'
    )
    parser.add_argument('--cmake_generator', default='Ninja', help='The CMake Generator to use')
    parser.add_argument('--build_type', default='release', help='Build type: release, debug')
    parser.add_argument('--qt_src_dir', default='qt/src', help='Qt source directory (default: qt/src)')
    parser.add_argument('--qt_build_dir', default='qt/build', help='Qt build directory (default: qt/build)')
    parser.add_argument('--qt_install_dir', default='qt/install', help='Qt install directory (default: qt/install)')
    args = parser.parse_args()

    # Configurable Constants
    QT_REPO_URL = 'git@github.com:HEXAGON-GEO/qt5.git'
    SUBMODULES = 'qtbase,qtdeclarative,qt3d,qt5compat,qtwebchannel,qttools,qtpositioning'
    SKIP_MODULES = 'qtwebengine'
    PLATFORM = args.platform # windows, linux, mac
    CMAKE_GENERATOR =  args.cmake_generator # Adjust based on your platform and compiler
    QT_VERSION = args.qt_version

    # Build type
    if args.build_type == "debug":
        BUILD_TYPE = '-debug'
    elif args.build_type == "release":
        BUILD_TYPE = '-release'
    else:
        print(f"Unknown build type: {args.build_type}")
        sys.exit(1)

    # Paths
    SRC_DIR = Path(args.qt_src_dir).resolve()
    BUILD_DIR = Path(args.qt_build_dir).resolve()
    INSTALL_DIR = Path(args.qt_install_dir).resolve()
    QTWEBENGINE_BIN_DIR = Path(args.qtwebengine_bin_dir).resolve()

    # Parse actions
    action_str = args.action.lower()
    ACTION = Action.NONE

    if action_str == 'all':
        ACTION = Action.ALL
    else:
        actions = action_str.split(',')
        for act in actions:
            act = act.strip()
            if act == 'checkout':
                ACTION |= Action.CHECKOUT
            elif act == 'generate':
                ACTION |= Action.GENERATE
            elif act == 'build':
                ACTION |= Action.BUILD
            else:
                print(f"Unknown action: {act}")
                sys.exit(1)

    print(f"==============================================")
    print(f"Running script with the following config:")
    print(f"QT VERSION: {QT_VERSION}")
    print(f"ACTION: {args.action}")
    print(f"CMAKE GENERATOR: {CMAKE_GENERATOR}")
    print(f"PLATFORM: {PLATFORM}")
    print(f"BUILD TYPE: {BUILD_TYPE}")
    print(f"QT REPO URL: {QT_REPO_URL}")
    print(f"SRC DIR: {SRC_DIR}")
    print(f"BUILD DIR: {BUILD_DIR}")
    print(f"INSTALL DIR: {INSTALL_DIR}")
    print(f"QTWEBENGINE BIN DIR: {QTWEBENGINE_BIN_DIR}")
    print(f"==============================================", flush=True)

    # Prepare environment variables for subprocesses
    env = os.environ.copy()

    # Create directories
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)

    # Clone the Qt repository if the source directory is empty
    # When building from BuildTool this is already done by checking out the repository
    if Action.CHECKOUT in ACTION:
      if not any(SRC_DIR.iterdir()):
          run_command(
              f'git clone --branch {QT_VERSION} {QT_REPO_URL} .',
              cwd=SRC_DIR,
              env=env
          )
      else:
          print(f"Source directory is not empty. Skipping repository cloning.")

    CMAKE_SOURCE_PATH = SRC_DIR

    if PLATFORM == "mac":
        suppress_xcode_check(CMAKE_SOURCE_PATH)

    # Initialize and update submodules
    if Action.CHECKOUT in ACTION or Action.GENERATE in ACTION:
        initialize_and_update_submodules(CMAKE_SOURCE_PATH, SUBMODULES, BUILD_DIR, env)

    # Configure the build
    configure_command = (
        f'"{CMAKE_SOURCE_PATH / "configure"}" '
        f'-skip {SKIP_MODULES} '
        f'-nomake examples -nomake tests '
        f'-cmake-generator {CMAKE_GENERATOR} '
        f'-prefix "{INSTALL_DIR}" '
        f'{BUILD_TYPE}'
    )

    if PLATFORM == "linux":
        configure_command += f' -qpa xcb -default-qpa xcb -xcb -xcb-xlib -bundled-xcb-xinput '
    elif PLATFORM == "windows":
        configure_command += f' -platform win32-msvc'

    if Action.GENERATE in ACTION:
        run_command(configure_command, cwd=BUILD_DIR, env=env)

    # Build Qt
    if Action.BUILD in ACTION:
        start = time.time()
        run_command('cmake --build . --parallel', cwd=BUILD_DIR, env=env)
        interval = time.time() - start
        print("compilation took", math.floor(interval / 60), "minutes and", math.floor(interval % 60), "seconds")

        # Install to configured prefix
        run_command('cmake --install .', cwd=BUILD_DIR, env=env)
        print(f"Copying QtWebEngine files from {QTWEBENGINE_BIN_DIR} to {INSTALL_DIR}")
        copy_with_overwrite(QTWEBENGINE_BIN_DIR, INSTALL_DIR)
        print(f"Copying QtWebEngine files... Done.")    

if __name__ == '__main__':
    start = time.time()
    main()
    interval = time.time() - start
    print("total deployment took", math.floor(interval / 60), "minutes and", math.floor(interval % 60), "seconds")

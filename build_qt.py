#!/usr/bin/env python3

###
#
#  Build instructions
#
#  You need to install Vulkan SDK from: https://vulkan.lunarg.com
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
#   libxcb1-dev libxcb-xfixes0-dev libx11-xcb-dev libxcb-icccm4-dev libxcb-glx0-dev libxcb-image0-dev libxcb-keysyms1-dev libxcb-xinput-dev libxcb-cursor-dev libxcb-render-util0-dev libxcb-render0-dev libxcb-randr0-dev libxcb-shape0-dev libxcb-shm0-dev libxcb-sync-dev libxkbcommon-x11-dev libxcb-util-dev
#
# For Wayland support additionally install:
#   libwayland-dev libwayland-egl-backend-dev libxkbcommon-dev
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
    print(f"Running command: {command} (in {cwd})", flush=True)
    result = subprocess.run(command, shell=True, cwd=cwd, env=env)
    result.check_returncode()

def initialize_and_update_submodules(cmake_source_path, cmake_generator, submodules, cwd, env):
    """ Check if submodules are already initialized by looking for a marker file
        or checking if the submodules exist and have commits """
    requested_submodules = [s.strip() for s in submodules.split(',')]
    needs_init = False
    
    for submodule in requested_submodules:
        submodule_path = cmake_source_path / submodule
        # Check if submodule directory exists and has git content
        if not submodule_path.exists() or not (submodule_path / '.git').exists():
            needs_init = True
            break
    
    if needs_init:
        print("First-time setup detected. Running Qt configure with -init-submodules...")
        command_text = f'"{cmake_source_path / "configure"}" -cmake-generator {cmake_generator} -init-submodules -submodules {submodules}'
    
        run_command(
            command_text,
            cwd=cwd,
            env=env
        )
    else:
        print("Submodules already initialized. Skipping Qt configure -init-submodules.")

def get_debug_files_extension(platform):
    if platform == "windows":
        return '.pdb';
    elif platform == "linux":
        return '.debug';
    elif platform == "mac":
        return '.dSYM';

def copy_with_overwrite(src_dir, dest_dir):
    """Copy contents of src_dir to dest_dir, overwriting existing files."""
    def _copy_function(src, dst, *, follow_symlinks=True):
        """Custom copy function that handles symlinks and overwrites."""
        if os.path.islink(src):
            # Remove existing symlink/file at destination
            if os.path.lexists(dst):
                os.unlink(dst)
            linkto = os.readlink(src)
            os.symlink(linkto, dst)
        else:
            shutil.copy2(src, dst, follow_symlinks=follow_symlinks)
    
    for item in src_dir.iterdir():
        # Check if any part of the path is '.svn'
        if '.svn' in item.parts:
            continue
        s = item
        d = dest_dir / item.name
        if item.is_dir():
            # Use copytree with symlinks=False so copy_function handles everything
            shutil.copytree(s, d, dirs_exist_ok=True, symlinks=False, copy_function=_copy_function)
        else:
            _copy_function(str(s), str(d))

def copy_debug_files(src_dir, dest_dir, platform, build_type):
    """Copy only debug files from src_dir to dest_dir, overwriting existing files."""
    src_dir = Path(src_dir)
    dest_dir = Path(dest_dir)

    extension = get_debug_files_extension(platform);

    build_type_dir = build_type[1:]; # drop the dash in front
    dest_dir = dest_dir / build_type_dir;

    # Ensure the destination directory exists
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Recursively search for debug files in the source directory
    for debug_file in src_dir.rglob(f"*{extension}"):
        # Skip files in '.svn' directories
        if '.svn' in debug_file.parts:
            continue
        
        # Destination path for the debug file
        dest_path = dest_dir / debug_file.name
        
        # Copy the debug file to the destination directory
        if debug_file.is_dir():
            shutil.copytree(debug_file, dest_path, dirs_exist_ok=True, symlinks=True)
        else:
            shutil.copy2(debug_file, dest_path)

def copy_file(src_dir, dest_dir, file_name):
    """Copy contents of src_dir to dest_dir, overwriting existing files."""
    for item in src_dir.iterdir():
        if item.is_file() and item.name == file_name:
            shutil.copy2(item, dest_dir)

def delete_debug_files_recursive(target_dir, platform):
    """Recursively find and delete all debug files in the target_dir and its subdirectories."""
    print(f"Delete debug files in ${target_dir} folder recursively")
    target_dir = Path(target_dir)

    extension = get_debug_files_extension(platform);

    # Recursively search for debug files in the target directory
    for debug_file in target_dir.rglob(f"*{extension}"):
        try:
            if debug_file.is_dir():
                shutil.rmtree(debug_file)  # Delete the directory
            else:
                debug_file.unlink()  # Delete the file
        except Exception as e:
            print(f"Failed to delete {debug_file}: {e}")
    print("Deleting debug files... Done.")

def run_configure_command(command=None, platform="windows", cwd=None, env=None):
    if platform == "linux":
        command += f' -qpa xcb -default-qpa xcb -xcb -xcb-xlib -bundled-xcb-xinput -feature-wayland-client '
    elif platform == "windows":
        command += f' -platform win32-msvc'

    run_command(command, cwd=cwd, env=env)


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
    parser.add_argument('--qt_version', required='True', help='Qt version, e.g.: 6.8.2')
    parser.add_argument('--platform', required='True', help='Platform: windows, linux, mac')
    parser.add_argument('--qtwebengine_bin_dir', required=True, help='QtWebEngine pre-built directory')
    parser.add_argument('--qtdebugfiles_dir', required=False, help='QtDebugFiles destination directory')
    parser.add_argument(
        '--action',
        default='all',
        help='Comma-separated actions: checkout, generate, build, all'
    )
    parser.add_argument('--cmake_generator', default='Ninja', help='The CMake Generator to use')
    parser.add_argument('--build_type', default='release_debug', help='Build type: release, debug, release_debug')
    parser.add_argument('--qt_src_dir', default='qt/src', help='Qt source directory (default: qt/src)')
    parser.add_argument('--qt_build_dir', default='qt/build', help='Qt build directory (default: qt/build)')
    parser.add_argument('--qt_install_dir', default='qt/install', help='Qt install directory (default: qt/install)')
    args = parser.parse_args()

    # Configurable Constants
    QT_REPO_URL = 'git@github.com:Bricsys/qt5.git'
    SUBMODULES = 'qtbase,qtdeclarative,qt3d,qt5compat,qtwebchannel,qttools,qtpositioning,qtscxml'
    SKIP_MODULES = '-skip qtquick3d -skip qtwebengine'
    PLATFORM = args.platform # windows, linux, mac
    CMAKE_GENERATOR =  args.cmake_generator # Adjust based on your platform and compiler
    QT_VERSION = args.qt_version

    # Build type
    if args.build_type == "debug":
        BUILD_TYPE = '-debug'
    elif args.build_type == "release":
        BUILD_TYPE = '-release'
    elif args.build_type == "release_debug":
        BUILD_TYPE = '-debug-and-release'
    else:
        print(f"Unknown build type: {args.build_type}")
        sys.exit(1)

    # Paths
    SRC_DIR = Path(args.qt_src_dir).resolve()
    BUILD_DIR = Path(args.qt_build_dir).resolve()
    INSTALL_DIR = Path(args.qt_install_dir).resolve()
    QTWEBENGINE_BIN_DIR = Path(args.qtwebengine_bin_dir).resolve()
    QTDEBUGFILES_DIR = Path(args.qtdebugfiles_dir).resolve()

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
    print(f"QTDEBUGFILES BIN DIR: {QTDEBUGFILES_DIR}")
    print(f"==============================================", flush=True)

    # Prepare environment variables for subprocesses
    env = os.environ.copy()

    # Create directories
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_DIR_DEBUG=Path(args.qt_build_dir+'_debug').resolve()

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
        initialize_and_update_submodules(CMAKE_SOURCE_PATH, CMAKE_GENERATOR, SUBMODULES, BUILD_DIR, env)

    # Configure the build
    configure_command = (
        f'"{CMAKE_SOURCE_PATH / "configure"}" '
        f'-force-debug-info '
        f'-feature-vulkan ' # needed for QtWebEngine
        f'{SKIP_MODULES} '
        f'-no-feature-spatialaudio ' # because we skipped module QtQuick3D
        f'-nomake examples -nomake tests '
        f'-cmake-generator {CMAKE_GENERATOR} '
        f'-prefix "{INSTALL_DIR}" '
    )

    if PLATFORM == "linux":
        configure_command += f' -feature-icu -qt-pcre -feature-openssl -feature-opensslv30 -feature-openssl-runtime ' # ssl is needed for QtWebEngine
        if BUILD_TYPE != '-debug':
            configure_command += f' -separate-debug-info '

    if Action.GENERATE in ACTION:
        if BUILD_TYPE != '-debug-and-release':
            run_configure_command(command=configure_command+f'{BUILD_TYPE}',
                              platform=PLATFORM, cwd=BUILD_DIR, env=env) 
        else:
            # at config step from Build Tool, we want to do both debug and release
            CURR_BUILD_TYPE='-release'
            run_configure_command(command=configure_command+f'{CURR_BUILD_TYPE}',
                              platform=PLATFORM, cwd=BUILD_DIR, env=env) 

            CURR_BUILD_TYPE='-debug'
            CURR_BUILD_DIR=BUILD_DIR_DEBUG
            CURR_BUILD_DIR.mkdir(parents=True, exist_ok=True)
            run_configure_command(command=configure_command+f'{CURR_BUILD_TYPE}',
                              platform=PLATFORM, cwd=CURR_BUILD_DIR, env=env) 

    # Build Qt
    if Action.BUILD in ACTION:
        start = time.time()
        build_command = f'cmake --build . --parallel '
        CURR_BUILD_DIR=BUILD_DIR
        if BUILD_TYPE == '-debug': # we build to a different folder, but install to ./install
            CURR_BUILD_DIR=BUILD_DIR_DEBUG
        run_command(build_command, cwd=CURR_BUILD_DIR, env=env)
        interval = time.time() - start
        print("compilation took", math.floor(interval / 60), "minutes and", math.floor(interval % 60), "seconds")

        # Install to configured prefix
        run_command('cmake --install .', cwd=CURR_BUILD_DIR, env=env)
        print(f"Copying QtWebEngine files from {QTWEBENGINE_BIN_DIR} to {INSTALL_DIR}")
        copy_with_overwrite(QTWEBENGINE_BIN_DIR, INSTALL_DIR)
        print(f"Copying QtWebEngine files... Done.")    

        if(QTDEBUGFILES_DIR != ''):
            print(f"Copying debug files from {INSTALL_DIR} to {QTDEBUGFILES_DIR}")
            copy_debug_files(INSTALL_DIR, QTDEBUGFILES_DIR, PLATFORM, BUILD_TYPE)
            print(f"Copying debug files... Done.")    

        BIN_DIR = INSTALL_DIR / 'bin' 
        copy_file(SRC_DIR / 'bcad', BIN_DIR, 'LICENSE.LGPLv3')
        copy_file(SRC_DIR / 'bcad', BIN_DIR, 'linuxdeployqt')
        copy_file(SRC_DIR / 'bcad', BIN_DIR, 'patchelf')

        delete_debug_files_recursive(INSTALL_DIR, PLATFORM) 

        if PLATFORM == "linux":
            copy_file(SRC_DIR / 'bcad', BIN_DIR, 'patch_libicudata.sh')
            copy_file(SRC_DIR / 'bcad', BIN_DIR, 'copy_libicu_libs.sh')
            LIB_DIR = INSTALL_DIR / 'lib'
            run_command(f'{BIN_DIR}/patch_libicudata.sh libQt6Core.so.6', cwd=LIB_DIR, env=env)
            run_command(f'{BIN_DIR}/copy_libicu_libs.sh {LIB_DIR}', cwd=LIB_DIR, env=env) # keep the order: call this after patching

if __name__ == '__main__':
    start = time.time()
    main()
    interval = time.time() - start
    print("total deployment took", math.floor(interval / 60), "minutes and", math.floor(interval % 60), "seconds")

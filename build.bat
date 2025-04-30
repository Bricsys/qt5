:: Default build type
set BUILD_TYPE=release
set ACTION_TYPE=build

set VS_TOOLS_PATH="C:/Program Files/Microsoft Visual Studio/2022/Professional/VC/Tools/"
set NINJA_PATH="C:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja"
set VCVARSALL_PATH="C:/Program Files/Microsoft Visual Studio/2022/Professional/VC/Auxiliary/Build/vcvarsall.bat" 

:: Parse command line arguments
:parse_args
if not "%~1" == "" set BUILD_TYPE=%~1
if not "%~2" == "" set ACTION_TYPE=%~2
if not "%~3" == "" set VS_TOOLS_PATH="%~3"
if not "%~4" == "" set NINJA_PATH="%~4"
if not "%~5" == "" set VCVARSALL_PATH="%~5"

:after_parse_args

set PATH=%PATH%;%VS_TOOLS_PATH%
set PATH=%PATH%;%NINJA_PATH%
call %VCVARSALL_PATH% amd64

python .\build_qt.py --qt_version=6.8.2 --action=%ACTION_TYPE% --platform=windows --build_type=%BUILD_TYPE% --qt_src_dir=".\\" --qt_build_dir=".\\build" --qt_install_dir=".\\install" --qtwebengine_bin_dir="%QTWEBENGINE_PATH%"

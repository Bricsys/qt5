:: Default build type
set BUILD_TYPE=release
set ACTION_TYPE=build

:: Parse command line arguments
:parse_args
if "%~1"=="" goto after_parse_args
if "%~1"=="debug" set BUILD_TYPE=debug
if "%~1"=="release" set BUILD_TYPE=release
if "%~2"=="generate" set ACTION_TYPE=generate
if "%~2"=="build" set ACTION_TYPE=build
if "%~2"=="checkout" set ACTION_TYPE=checkout
shift
goto parse_args

:after_parse_args

set PATH=%PATH%;"C:/Program Files/Microsoft Visual Studio/2022/Professional/VC/Tools/"
set PATH=%PATH%;"C:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja"
call "C:/Program Files/Microsoft Visual Studio/2022/Professional/VC/Auxiliary/Build/vcvarsall.bat" amd64

python .\build_qt.py --qt_version=6.8.2 --action=%ACTION_TYPE% --platform=windows --build_type=%BUILD_TYPE% --qt_src_dir=".\\" --qt_build_dir=".\\build" --qt_install_dir=".\\install" --qtwebengine_bin_dir="D:/Qt_OSS_6_8_2_/6.8.2/msvc2022_64"

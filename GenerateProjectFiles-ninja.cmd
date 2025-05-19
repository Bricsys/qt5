set BUILD_TYPE=release_debug
if not "%~1" == "" set BUILD_TYPE=%~1


.\build.bat %BUILD_TYPE% generate

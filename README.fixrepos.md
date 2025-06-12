Before the build script can be run, some git repo magic should happen. The repo we originally cloned (https://code.qt.io/qt/qt5.git) doesn't have any issues, but the GitHub one we had to fork from does however. There is a problem with one of the submodules (qttools), which points to a nonexistent submodule. It can be fixed by creating both in the super module (qt5) and qttools a branch. In qttools the problematic submodule gets removed after which qt5 needs to point to the fixed qttools submodule.

## Remove the untraceable submodule from qttools
* git clone git@github.com:HEXAGON-GEO/qttools.git
* make a new branch based on a tag (e.g. bricsys_6.8.2 based on v6.8.2)
* go into qttools
* git rm src/assistant/qlitehtml
* remove "add_subdirectory(assistant)" from src/CMakeLists.txt
* git add -A && git commit -m "Ignore qlitehtml" && git push -u origin <branch_name>:<branch_name>

## Point the qt5 super module to the fixed qttools module
* git clone git@github.com:HEXAGON-GEO/qt5.git
* make a new branch based on a tag (e.g. bricsys_6.8.2 based on v6.8.2)
* go into qt5
* git submodule set-branch --branch <branch_name> qttools
* git submodule sync
* git submodule update --remote qttools
* git add -A && git commit -m "Add necessary modification for qttools" && git push -u origin <branch_name>:<branch_name>

## Run the build script
* now build_qt.py can be run with qt_version=<branch_name>

Note: git repos can be moved by doing "git clone --bare <old_url>" and "git push --mirror <new_url>" from the cloned folder.

## Introduction

BricsCAD® is a powerful CAD software that leverages the Qt framework to deliver a robust and versatile user experience. As an open-source library, Qt is licensed under the Lesser General Public License ([LGPL](https://www.gnu.org/licenses/lgpl-3.0.html)), which allows users to modify and replace its components, provided certain conditions are met. This flexibility can be particularly useful for developers who wish to customize the Qt libraries to better suit their specific needs or to enhance certain functionalities within BricsCAD.

This guide provides a walkthrough for users who wish to replace the standard Qt libraries used by BricsCAD with their own custom-compiled versions. The process involves several key steps, including backing up existing libraries, deploying custom versions, and ensuring compliance with LGPL requirements by providing access to the modified source code.

Whether you're looking to optimize performance, fix bugs, or introduce new features, this guide will help you navigate the technical and legal aspects of replacing Qt libraries in BricsCAD. By following these instructions, you can ensure a smooth transition to your custom libraries while maintaining the functionality and stability of your BricsCAD installation.

## Step 1: Replace the existing Qt libraries in BricsCAD

1. **Backup original libraries**:
   - Navigate to the BricsCAD installation directory.
      - Windows: This is usually located at `C:\Program
   Files\Bricsys\BricsCAD V[version] [locale]\`
      - Linux: This is usually located at `/opt/bricsys/bricscad/v[version]/`
      - macOS: This is usually located at `/Applications/BricsCAD V[version].app/Contents/Frameworks/`

   - Locate the Qt libraries within this directory. These files typically have a `*.dll` (Windows), `*.so` (Linux). On macOS, look for the `*.framework` folders.
   - Create a backup of these libraries by copying them to a secure location. This backup ensures you can restore the original files if necessary.

2. **Deploy custom libraries**:
   - After [compiling your custom Qt libraries](https://doc.qt.io/qt-6/build-sources.html), ensure they have the same names as the original libraries used by BricsCAD.
   - Copy your custom libraries into the same directory, replacing the original Qt libraries. On macOS, replace the `*.framework` folders with the custom compiled `*.framework` folders.
   - Maintain the directory structure and include any additional resources or dependencies your custom libraries require.

## Step 2: Provide Source Code

1. **Include Source Code**:
   - As you are distributing a modified version of an LGPL library, you must provide access to the source code of your custom Qt libraries.
   - This can be done by including the source code of the modified Qt library in the distribution package or offering a written offer to supply the source code upon request.

2. **Documentation**:
   - Clearly document any changes you have made to the Qt library, explaining how these modifications impact the application.
   - Provide instructions on how users can compile the modified library themselves. This should include details on setting up the build environment, configuring the build options, and compiling the source code.

3. **User Guidance**:
   - Offer detailed guidance for users on how to replace the libraries, including any potential impacts on functionality.
   - Provide support channels, such as forums or email support, for users who encounter difficulties during the replacement process.

### Additional Considerations

- **Legal Compliance**: Ensure that all modifications and distributions comply with the LGPL, preserving the users' rights to modify and replace the library.
- **Reversion Instructions**: Include instructions on how to revert to the original libraries if users encounter issues with the custom versions.

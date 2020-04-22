# Installing FED3 Viz

There are two methods for running FED3 Viz: either **downloading the application** or **running the Python script**.

The application (created with [PyInstaller](https://www.pyinstaller.org/)) *hopefully* works like any other computer GUI: just double-click to start.  This method of installation is intended to work for people who don't have Python installed or don't want to mess around with any code.  **The big caveat is that there is currently only a 64-bit Windows option (only tested on Windows 10)**.  Ideally, there eventually will be 32-bit and Mac OS X applications as well.

The more universal installation option is running the FED3 Viz Python script in your own interpreter.  This option will involve some futzing with a terminal, but I've done my best to provide detailed instructions below.

If you have any issues with either of the installation methods below, please post your issue here or on the [FED3 Google Group](https://groups.google.com/forum/#!forum/fedforum).  The process of converting the Python script to an application is a black box to me, so I cannot promise that issues with running the `.exe` will be solvable.  Running the Python script will hopefully be less error-prone, and I will aim to prioritize getting that method functioning for everyone.

### Method 1: Running FED3 Viz from an .exe

System Requirements:

- Windows (64-bit)
- built on Windows 10, though not sure if that is required

Instructions:

1. Visit the [releases page](https://github.com/earnestt1234/FED3_Viz/releases)
2. From the most recent version, download the`FED3_Viz_Windows64.zip` and unzip.
3. In the unzipped folder, navigate to `FED3 Viz/dist/main/FED3Viz.exe`.
4. (Optional) Right-click > Create shortcut and place the shortcut in a less nasty folder*.
5. Double click the `.exe` or the shortcut to run - you may have to permit Windows security to let the application run.

*_I haven't figured out how to bundle the zip folder with a working relative shortcut..._

### Method 2: Running FED3 Viz from a Python interpreter


# Installing FED3 Viz

There are two methods for running FED3 Viz: either **downloading the application** or **running the Python script**.

The application (created with [PyInstaller](https://www.pyinstaller.org/)) *hopefully* works like any other computer GUI: just double-click to start.  This method of installation is intended for people who don't have Python installed or don't want to mess around with any code.  **The big caveat is that there is currently only a 64-bit Windows option (only tested on Windows 10)**.  Ideally, there eventually will be 32-bit and Mac OS X applications as well.

The more universal option is running the FED3 Viz Python script in your own interpreter.  This option will involve some futzing with a terminal, but I've done my best to provide detailed instructions below.

If you have any issues with either of the installation methods, please post your issue [here](https://github.com/earnestt1234/FED3_Viz/issues) or on the [FED3 Google Group](https://groups.google.com/forum/#!forum/fedforum).  The process of converting the Python script to an application is a black box to me, so I cannot promise that issues with running the `.exe` will be solvable.  Running the Python script will hopefully be less error-prone, and I will aim to prioritize getting that method functioning for everyone.

## Method 1: Running FED3 Viz from an .exe

System Requirements:

- Windows (64-bit)
- built on Windows 10, though not sure if that is required

Instructions:

1. Visit the [releases page](https://github.com/earnestt1234/FED3_Viz/releases)
2. From the most recent version, download the`fed3viz-win64.zip` and unzip.
3. In the unzipped folder, navigate to `fed3viz/fed3viz.exe`.
4. (Optional) Right-click > Create shortcut and place the shortcut in a less nasty folder*.
5. Double click the `.exe` or the shortcut to run - you may have to permit Windows security to let the application run.  Startup is sometimes slow on the first use but gets better.

*_I haven't figured out how to bundle the zip folder with a working relative shortcut..._

## Method 2: Running FED3 Viz from a Python interpreter

These are the things you need to run FED3 Viz as a script:

- the FED3 Viz source files
- Python 3 
- some third party Python packages

These instructions will assume you have none of these.   

If you already have Python installed, you only need to ensure that you have installed the third-party packages used by FED3 Viz (**Step 3** below).

#### Step 1: Download FED3 Viz source files

Visit the [releases page](https://github.com/earnestt1234/FED3_Viz/releases), and download the latest `Source code (zip)` file.  Unzip the files on your computer (doesn't matter where).

#### Step 2: Install Python​ :snake:

Python can be installed in multiple ways.  These instructions will follow the Anaconda Distribution, and will refer to some of its specific features.

Visit the [Anaconda download page](https://www.anaconda.com/distribution/) and download/install the **Python 3** (e.g. 3.7) version that matches your OS.  Anaconda will install the Python language, a place to run code, and lots of helpful packages (some used by FED3 Viz).

#### Step 3a: Install requirements with a virtual environment (recommended*)

FED3 Viz was built in Python 3.7.7, with specific versions of some 3rd party packages (like `pandas`, `matplotlib`, etc.).  It is possible that changes to any of these libraries may alter or disrupt FED3 VIz's functionality in the future.  To get around that issue, you can create a *virtual environment*; a segmented version of Python on your PC where specific versions of packages can be installed.  These instructions will describe how to do so in Anaconda (but this is [doable](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/) without Anaconda).

To make a virtual environment with Anaconda (a la [these instructions](https://docs.anaconda.com/anaconda/user-guide/tasks/switch-environment/)), open Anaconda Prompt.  Run the following command, where `fed_viz` is the name you give the new environment:

```
conda create --name fed_fiz python=3.7
```

Once finished, "activate" the environment by running (on Windows):

```
activate fed_viz
```

Or on Mac/Linux:

```
conda activate fed_viz
```

You should see the command line change to start with `(fed_viz)`.  

Now, you can install FED3 Viz's dependencies in this `fed_viz` environment using Python's `pip` package manager.  These dependencies can be installed in one go by using the `requirements.txt` file, available inside the main `FED3_Viz` folder of the downloaded source code.  

In Anaconda Prompt, navigate to the directory of `requirements.txt`, using `cd`, e.g.:

```
cd C:/Users/earne/Downloads/FED3_Viz
```

This will look slightly different depending on your OS.  If you are in the correct directory, you can then call the following command to install the required packages:

```
pip install -r requirements.txt
```

This may take a few minutes.  

*Note that you don't *have* to create a virtual environment - you can do the `pip` install in your global Python installation as well.  However, this may cause issues if you have other scripts with different dependencies.  You also may need to uninstall and reinstall some packages if you want to match the versions in `requirements.txt` exactly.

#### Step 4: Run the FED3 Viz script

You are now ready to run FED3 Viz!  The script which generates the application is `fed3viz.py`.  You can run this script from Anaconda Prompt by moving into the `FED3_Viz` folder and calling:

```
python fed3viz.py
```

You can also run the script in any other Python terminal or IDE, but you may have to take extra steps to point to the `fed_viz` virtual environment.

In my hands, there are a few guidelines which, if not met, may result in errors:

- The script is being run in the virtual environment with the dependencies installed
- the current working directory of the interpreter running the script is the same of `fed3viz.py`
- the files and organization of folders within `FED3_Viz/` have not been moved or altered (with the exception of saved settings or group labels in the `settings/` and `groups/` directories.)

Note that if you want to close the environment and return to the global installation of Python, you can call (on Windows):

```
deactivate
```

Or on Mac/Linux:

```
conda deactivate
```


# Installing FED3 Viz

There are two methods for running FED3 Viz: either **downloading the application** or **running the Python script**.

The application (created with [PyInstaller](https://www.pyinstaller.org/)) works like any other computer GUI: just double-click to start.  This method of installation is intended for people who don't have Python installed or don't want to mess around with any code.  Currently, there are 64-bit Windows and Mac OS X options.  **I recommend using Windows if you have the choice between that and Mac;** FED3 Viz is primarily developed on Windows, and can be significantly slower on some newer Mac devices that I have tested ([see this issue](https://stackoverflow.com/questions/64937106/plotting-with-tkinter-slows-and-crashes-on-newer-macs)).

The more universal option is running the FED3 Viz Python script in your own interpreter.  This option will involve some futzing with a terminal, but I've done my best to provide detailed instructions below.

If you have any issues with either of the installation methods, please post your issue [here](https://github.com/earnestt1234/FED3_Viz/issues) or on the [FED3 Google Group](https://groups.google.com/forum/#!forum/fedforum).  The process of converting the Python script to an application is a black box to me, so I cannot promise that issues with running the `.exe` will be solvable.  Running the Python script will hopefully be less error-prone, and I will aim to prioritize getting that method functioning for everyone.

## Method 1: Running FED3 Viz from an .exe

### Windows:

System Requirements:

- Windows (64-bit)
- built on Windows 10, though not sure if that is required

Instructions:

1. Visit the [releases page](https://github.com/earnestt1234/FED3_Viz/releases)

2. From the most recent version, download the`fed3viz-win64.zip` (under "Assets") and unzip.

3. (Optional) Add a Windows Defender exclusion for the `fed3viz` folder (in the unzipped folder), following [these instruction from Microsoft](https://support.microsoft.com/en-us/help/4028485/windows-10-add-an-exclusion-to-windows-security).  

   Explanation: FED3 Viz may be very slow to open (~1 min) when first starting if Windows antivirus has to scan it;  [you can see this thread for a discussion of the issue](http://pyinstaller.47505.x6.nabble.com/very-slow-start-td2089.html).  Adding the exclusion seems to fix the issue, and I have not found a way around that isn't significantly more complicated or expensive.  If you do add the exclusion, **you should not add any other foreign files to the `fed3viz` folder**.  You will also need to redo the exclusion if the folder moves.  If you do not want to add the exclusion, you can expect the first start of FED3 Viz to be slow each use, but following starts to be quicker.

4. In the unzipped folder, navigate to `fed3viz/fed3viz.exe`.

5. (Optional) Right-click > Create shortcut and place the shortcut in a less nasty folder.*  There are `.ico` files which can be used to replace the shortcut icon in the `img` folder.

6. Double click the `.exe` or the shortcut to run - you may have to permit Windows security to let the application run (from an unknown developer).  Startup is sometimes slow on the first use but gets better.

### Mac:

System Requirements:

- Mac OS X
- built on Yosemite v10.10.5, but I have tested on a machine with Catalina

Instructions:

1. Visit the [releases page](https://github.com/earnestt1234/FED3_Viz/releases)

2. From the most recent version, download the`fed3viz-osx.zip` (under "Assets") and unzip.

3. In the unzipped folder, navigate to `fed3viz/fed3viz` (the UNIX executable file)

4. (Optional) Right-click > Make Alias and place the shortcut in a less nasty folder.*  There are `.ico` files which can be used to replace the shortcut icon in the `img` folder.

5. Double click `fed3viz` or the shortcut to run.

   You may have to permit Mac security to let the application run (from an unknown developer).  This can be slightly more complicated on Mac than Windows, especially with new versions.  You will likely need to follow one of 3 options (taken from [here](https://www.macworld.co.uk/how-to/mac-software/mac-app-unidentified-developer-3669596/)):
   
   - If a popup warns you but still allows you to open the program, you can do that
   - Otherwise, you may have to go to System Preferences > Security and check the option for allowing applications from unidentified developers.  There may also be an option to start the program from this menu (as it knows that it was just blocked).
   - If the option above is not available, you need to go to Terminal and enter `sudo spctl --master-disable` to unhide this option.  Then go back to System preferences and toggle the option to allow the program to run.

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

#### Step 3: Install requirements with a virtual environment (recommended*)

FED3 Viz was built in Python 3.7.7, with specific versions of some 3rd party packages (like `pandas`, `matplotlib`, etc.).  It is possible that changes to any of these libraries may alter or disrupt FED3 VIz's functionality in the future.  To get around that issue, you can create a *virtual environment*; a segmented version of Python on your PC where specific versions of packages can be installed.  These instructions will describe how to do so in Anaconda (but this is [doable without Anaconda](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)).

To make a virtual environment with Anaconda (a la [these instructions](https://docs.anaconda.com/anaconda/user-guide/tasks/switch-environment/)), open Anaconda Prompt on Windows, or on Mac you can just use Terminal (for the latter if you find you can't use `conda` commands, you may have to do some [additional setup](https://towardsdatascience.com/how-to-successfully-install-anaconda-on-a-mac-and-actually-get-it-to-work-53ce18025f97)).  Run the following command, where `fed_viz` is the name you give the new environment:

```
conda create --name fed_viz python=3.7
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

***Note that you don't *have* to create a virtual environment** - you can do the `pip` install in your global Python installation as well.  However, this may cause issues if you have other scripts with different dependencies.  You also may need to uninstall and reinstall some packages if you want to match the versions in `requirements.txt` exactly.

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

##### Note for Mac/Linux Users:

FED3 Viz was developed on Windows, which may cause issues when running on another system.

When running on **Mac**, I noticed some cosmetic differences in FED3 Viz (due to differences in the system's default widgets); I have been able to make quick fixes for these.  Most of these issues seem to disappear when using the executable, curiously.  Running from the Python script still works (so far I can tell), but there may be some ugly looking buttons and wonky coloring.  I haven't detected any Mac specific functionality issues yet.

I will not be able to test the script on **Linux** , or make any kind of application for Linux.  If anyone does end up using this on Linux, I'd be curious to see how it works.

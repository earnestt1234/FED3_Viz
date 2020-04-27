# FED3 Viz Manual



<p align="center">
	<img src="img/fedviz_textlogo.png" width="500">
</p>



**Written for version**: v0.0.2 (beta)

**Date of creation**: April 27th, 2020

**GitHub**: [https://github.com/earnestt1234/FED3_Viz](https://github.com/earnestt1234/FED3_Viz)



### Welcome!

Welcome to FED3 Viz, a Python GUI for graphing data from FED3 devices.  This manual will describe the basic functionalities of FED3 Viz and how to use them.  It will also try to address any common confusions/errors that may pop up.

You can find the FED3 Viz landing page at [GitHub](https://github.com/earnestt1234/FED3_Viz); all changes to the program will be made and logged though GitHub.  

### Installation

On the FED3 Viz GitHub, there is an "Installation.md" markdown file which contains instructions on how to run FED3 Viz via either a) running the Python script or b) running a bundled application (from Windows or Mac).  These instructions have been appended at the end of this manual.  The rest of the manual will deal with the use of the application once installed.

<div style="page-break-after: always; break-after: page;"></div> 

# Table of Contents

- [Loading Data](#loading-data)

  - [File View](#file-view)
  - Loading FEDs
    - Loading Process
    - Load Errors
  - Deleting FEDs
- Groups
  - Group View
  - Creating Group
  - Deleting Group
  - Saving Groups
- Plots
  - Single Pellet Plot
  - Multi Pellet Plot
  - Average Pellet Plot
  - Interpellet Interval Plot
  - Diagnostic Plot
  - Day/Night Plot
- Viewing and Editing Plots
  - Renaming
  - New Window
  - Deleting Plots
  - Saving Plots
  - Saving Plot Data
  - Saving Plot Code
- Settings
  
  - Loading and Saving Settings
- FAQ
- Appendix:
  - Plot Data Dependencies
  - Installation Repost

  

<div style="page-break-after: always; break-after: page;"></div> 

# Loading Data

FED3 saves data as a `.csv` file on its internal SD card; these are the files used by FED3 Viz.  They have the following naming structure:

*FED{FED #}\_{DATE}\_{RECORDING #}.csv*

- FED # = Label number of the FED
- Date = Date of recording in monthdayyear format
- Recording # = Unique number given to the recording

FED3 Viz will recognize these `.csv` files, as well as files converted into Excel (`.xlsx`) format.  If the data have been changed out of one of these file types, they will have to be reconverted in order to be used by FED3 Viz.

### File View

When F
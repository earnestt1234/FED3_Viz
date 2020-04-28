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

If you do notice any inaccuracies, typos, misinformation, or missed content in this manual, please report the issue through GitHub - thanks!

### Installation

On the FED3 Viz GitHub, there is an "Installation.md" markdown file which contains instructions on how to run FED3 Viz via either a) running the Python script or b) running a bundled application (from Windows or Mac).  These instructions have been appended at the end of this manual.  The rest of the manual will deal with the use of the application once installed.

<div style="page-break-after: always; break-after: page;"></div> 

# Table of Contents

- [Tour](#tour)

  - [Home Tab](#home-tab)
  - [Plots Tab](#plots-tab)
  - [Settings Tab](#settings-tab)
  - [About Tab](#about-tab)

- [Loading Data](#loading-data)

  - [Loading FEDs](#loading-feds)
    - [How FEDs Are Loaded](#how-feds-are-loaded)
    - [Loading Errors](#loading-errors)
  - [File View](#file-view)
  - [Deleting FEDs](#deleting-feds)
  
- [Groups](#groups)
  
  - [Creating Groups](#creating-groups)
  - [Deleting Groups](#deleting-groups)
- [Saving Groups](#saving-groups)
  
- [Plots](#plots)
  
  - [Single Pellet Plot](#single-pellet-plot)
  - [Multi Pellet Plot](#multi-pellet-plot)
  - [Average Pellet Plot](#average-pellet-plot)
  - Interpellet Interval Plot
  - Day/Night Plot
  - Diagnostic Plot
  
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
  - Installation Repost

  

<div style="page-break-after: always; break-after: page;"></div> 

# Tour

This section will introduce the layout of FED3 Viz, and define some areas of the application.  FED3 Viz has 4 different panes, which can be selected by clicking the following tabs at the top of the application window.

- **Home Tab**
- **Plots Tab**
- **Settings Tab**
- **About Tab**

### Home Tab

The **Home Tab** is the tab that is open when FED3 Viz starts up.  On this tab, you can load FED3 data and create plots from them.

<p align="center">
	<img src="img/manual/hometab_num.png" width="500">
</p>
Elements of the Home Tab:

1. The **Info Bar** shows text describing button functions on the Home Tab.  Hover the mouse over a button and the Info Bar will give a brief description of that button's function.
2. The top row of buttons, which are tools for loading and managing data files within FED3 Viz.
3. The **File View** is the largest element of the Home Tab.  When a FED data file is loaded, it will appear as a row in the File View.  Each column will show data associated with that data file.
4. The **Group View** lists all the currently loaded "groups," used for combining data from multiple FEDs (see the "Groups" section below).
5. The bottom row of buttons, which correspond to buttons used to create plots.

Whether or not a button is active depends on what data have been loaded into the application; for example, most plotting buttons must have some files selected in order to be active.  Specific cases will be described below in the context of each button's function.

### Plots Tab

The **Plots Tab** is used for selecting, viewing, and editing the plots that have been created.  

<p align="center">
	<img src="img/plottab.png" width="500">
</p>

The Plots Tab is made up of three elements (from left to right):

- A column of buttons for working with plots
- A **Plot List** showing all the currently loaded plots
- A **Display Pane** which renders the plots.  At the bottom of the Display Pane, there is a a **Navigation Toolbar** (included from [`matplotlib`](https://matplotlib.org/3.1.1/users/navigation_toolbar.html)) used for editing the view of the plot on display.

### Settings Tab

The **Settings Tab** offers controls for creating plots and preferences for the way FED3 Viz runs.

<p align="center">
	<img src="img/manual/settingstab.png" width="500">
</p>

The Settings Tab is divided into different headered sections, corresponding to options for different plots.  It starts with a **General** section (options for that affect the whole application or multiple plot types), and ends with a **Save/Load Settings** section (for preserving desired settings for future use).

### About Tab

The **About Tab** shows the version number and date of FED3 Viz, as well as some FED3-related links.

<p align="center">
	<img src="img/manual/abouttab.png" width="500">
</p>

<div style="page-break-after: always; break-after: page;"></div> 

# Loading Data

FED3 saves data as a `.csv` file on its internal SD card; these are the files used by FED3 Viz.  You can access these files by ejecting the SD card and connecting it to your computer (**not** by connecting the FED to the computer via the micro-USB).  They have the following naming structure:

*FED{FED #}\_{DATE}\_{RECORDING #}.csv*

- FED # = 3 digit device number
- Date = 6 digit date (month-day-year format)
- Recording # = 2 digit recording number

FED3 Viz will recognize these `.csv` files, as well as files converted into Excel (`.xlsx`) format.  If the data have been changed out of one of these file types, they will have to be reconverted in order to be used by FED3 Viz.

### Loading FEDs

The **Load Button** of the Home Tab is used for loading data into FED3 Viz; this button is always active.  Clicking it will bring up a file dialog where one or more FED3 files can be selected to import.

##### How FEDs Are Loaded

FED3 Viz will attempt to load every file `.csv` or `.xlsx` file selected by the Load Button file dialogue using a Python library for working with tabular data (`pandas`).  The loading process first tries to parse the file to find columns matching the standard FED3 data columns (as of the time of writing).

*Standard FED3 Data Columns:*

- MM:DD:YYYY hh:mm:ss
- Device_Name
- Battery_Voltage
- Motor_Turns
- Session_Type
- Event
- Active_Poke
- Left_Poke
- Right_Poke
- Pellet_Count
- Retrieval_Time

These columns are looked for **by name, not the content or type of data in the column**.  If all correctly found, these columns will be used to try and generate additional variables used for plotting (elapsed time, pellets as a binary entries, etc.).  By default, files with the same name will not be reloaded (even if they reside in different folders); to load duplicate file names, untick **Settings > General > Don't load a FED if it's filename is already loaded**. 

##### Loading Errors

An error message pop-up may be raised if there are any issues encountered during the loading process.  The two major types of errors are:

- Unrecognized: the file(s) was not recognized as FED3 data.  This error means that the program failed to load the data.  This can occur from attempts to read non `.csv` or `.xlsx` files, or from correct file types that differ significantly from the standard FED3 file format.  This error can not be suppressed.
- Missing Data: the file(s) is missing at least one of the default columns.  This means that the file was loaded, but it may be missing some columns which are used by FED3 Viz for plotting; it is meant to serve as a warning that some plots may be unavailable or may produce unexpected results.  This error can occur when the raw data has been edited to remove or rename columns, or when using an earlier version of FED3 Arduino code.  This error can be suppressed by unticking **Settings > General > Show missing column warning when loading.**

Further discussion of problems with loading may be brought up in the **FAQ** as the application develops.  Additionally, the description of each plot in the "Plots" section below will list the data columns required by each plot.

### File View

<p align="center">
	<img src="img/manual/loaded.png" width="500">
</p>

Loaded FED data can be inspected on the File View of the Home Tab.  Each loaded FED will correspond to a row in the File View, where column entries will correspond to properties of the file:

- Name: the name & extension of the file
- \# events: how many events were logged by the device, either Pokes or Pellets (essentially the number of rows in the data file)
- start time: the date and time of the start of the recording
- end time: the date and time of the end of the recording
- duration: the amount of time between the first and last logged event
- groups: any user-defined groups associated with the recording

When more than one file is loaded, the files can be sorted by clicking on the column headers of the File View.  A single click will sort the column in order (alphabetical/smallest>largest/shortest>longest), while a double-click will reverse the order.

### Deleting FEDs

FEDs can be removed from the application by using the **Delete Button** of the Home Tab.  The Delete Button will only be active when one or multiple FEDs are highlighted in the File View.

<div style="page-break-after: always; break-after: page;"></div> 

# Groups

**Groups** are user-defined labels for aggerating data from multiple FED recordings.  Plots which utilize Groups will show data from each Group as a separate curve or bar.  Groups can be compare data from mice in multiple experimental groups, or from mice before and after an intervention.

### Creating Groups

To create a Group:

- Select one or more FEDs from the File View
- Click the **Create Group Button**
- In the text box on the pop-up window, enter a name for the Group.  Group names need to be unique, and repeated names will not be enterable.
- Click OK

The Groups associated with each loaded data file will be shown in the "groups" column of the File View.  Additionally, all currently loaded Groups are viewable in the **Group View** of the Home Tab.  Selecting a group will highlight all its members.

FEDs do not have to be grouped uniquely; one FED can be part of multiple groups.

There is currently no ability to edit the members of a Group once it has been created.  Rather, this can be achieved by creating a new Group with the desired members.  

### Deleting Groups:

To delete a Group:

- Select one or more Groups from the Group View
- click the **Delete Group Button**

Groups will also be removed if all of its members (FED files) are deleted.

### Saving Groups:

Groups can be saved and loaded for relabeling devices over multiple uses of FED3 Viz.  Groups can be loaded from anywhere, but have a default location which depends on the installation method:

- **Windows or Mac Executable:** `fed3viz/groups/`
- **Python Script** (i.e. GitHub source code): `FED3_Viz/FED3_Viz/groups/`

To save the currently loaded groups, click the **Save Groups Button** on the Home Tab.  This will bring up a file dialogue with the default Groups file location.  Group files are saved in `.csv` format. 

Groups can then be reloaded with the **Load Groups Button**; at least one FED file must be loaded for the button to be active.  Clicking the button will prompt the user to select a Group file to load.

Group files associated **file names** with **Group names**.  In this way, files that are moved around the computer will still be recognized.  However, **files with changed names will not be re-grouped**.  Additionally, if a new file matches a name in the Groups file, it will be Grouped, even if it was not the original file used to create the group.

<div style="page-break-after: always; break-after: page;"></div> 

# Plots

The general steps to create a plot are:

- Select the desired settings from the Settings Tab (if applicable)
- Select the FED files to include in the plot
- Press a plot button from the bottom row of the Home Tab

This section will go through the plots currently available in FED3 Viz and describe what they show and how they are made.

There are a couple settings which apply to multiple plots: 

- *Shading dark periods*:  When enabled, applicable plots will have a light gray shading during periods when the lights are off - this can help for detecting circadian patterns of activity.  This setting can be toggled from **Settings > General > Shade dark periods (lights on/off)**.  The start and and time of the dark period can be selected using the dropdown menus next to this setting. Plots which make use of this feature will include a :new_moon_with_face: symbol in their description
- *Using Groups*: Some plots aggregate data and rely on Groups.  By default, plots which rely on Groups will **plot all Groups present in the Group View**; you can instead use the Group View to select which Groups to include by unticking **Settings > General > For plots using groups, include all loaded groups rather than those selected**.  Plots that utilize groups will be tagged with a :paperclip: symbol in their description.

### Single Pellet Plot

*Dependent columns =  MM:DD:YYYY hh:mm:ss, Pellet_Count*

*Can use night shading* :new_moon_with_face:

<p align="center">
	<img src="img/examples/pelletplot.png" width="500">
</p>

This plot shows the pellets retrieved over time for a single data file.  By default, the raw *Pellet_Count* column (the cumulative total) is plotted against the timestamps (**Settings > Individual Pellet Plots > Values to plot > Cumulative**).  This can be changed to show the sum of pellets retrieved at a specified bin size using **Settings > Individual Pellet Plots > Values to plot > Frequency** and **Settings > Individual Pellet Plots > Bin size of pellet frequency (hours):**

<p align="center">
	<img src="img/manual/freqplot.png" width="500">
</p>

The color of these plots can be set, also (**Settings > Individual Pellet Plots > Default color (single pellet plots**)).

### Multi Pellet Plot

*Dependent Columns = MM:DD:YYYY hh:mm:ss, Pellet_Count*

*Can use night shading* :new_moon_with_face:

<p align="center">
	<img src="img/examples/multipellet.png" width="500">
</p>

Multi Pellet Plots are basically Single Pellet Plots, but individual devices are plotted as separate lines.  As above, either the cumulative amount or binned frequency of pellet retrieval can be plotted.

The only additional setting is **Settings > Individual Pellet Plots > Align multi pellet plots to the same start time**.  When ticked (as above), pellets will be plotted against the *elapsed time* (since each device started); this prevents shading of dark periods.  When unticked (default), the *absolute date/time* will be preserved, so FEDs which were recorded at different times will not overlap.

### Average Pellet Plot

*Dependent Columns = MM:DD:YYYY hh:mm:ss, Pellet_Count*

*Can use night shading* :new_moon_with_face:

*Uses groups* :paperclip:

<p align="center">
	<img src="img/examples/average.png" width="500">
</p>

Average Pellet Plots average the pellets retrieved for each file in a Group.  Each group in the plot is plotted as a separate line.  Average Pellet Plots can only be plotted using a binned frequency of pellet retrieval.

Settings specific to these plots are under **Settings > Average Pellet Plots > Average Pellet Plots:**

- **Error value for average plots**: how to show the spread of data within each group.  Options are standard error of the mean (SEM), standard deviation (STD), raw data (each file shown as a lighter line surrounding the mean line), or None.

- **Bin size for averaging (hours):** how frequently to average data (must be done as pellets are logged to the second)

- **Align average plots to the same start time:**  When unticked (default), the program only average  over *absolute date & time*; i.e. only FEDs that were active at the same time can be averaged, and averaging can only be done for the window of time where **all** FEDs in the Groups are active.  When ticked, the data are aligned such that the same hours of the day are averaged for each Group.  This opens up two more options:

  - **Start time**: the time of day to start taking an average - data before this time on the first day of recording will be ignored
  - **No. days**: how many days to try and average data for, since the **Start time** on the first day.

  If the box is unticked, and the Groups selected have no periods when all their members are active, a warning will be raised, directing the user to try making the aligned version of the plot.

### Interpellet Interval Plot

*Dependent Columns = MM:DD:YYYY hh:mm:ss, Pellet_Count*

*Uses groups* :paperclip:

<p align="center">
	<img src="img/examples/ipi.png" width="500">
</p>

The Interpellet Interval Plot is a histogram where the values counted are the time between each pellet retrieval event.  This plot can give you a sense of how the mouse feeds or earns pellets, and it show changes in meal or eating frequencies
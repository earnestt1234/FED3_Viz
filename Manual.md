# FED3 Viz Manual



<p align="center">
	<img src="img/fedviz_textlogo.png" width="500">
</p>


**Written for version**: v0.1.0 (beta)

**Date of creation**: May 11th, 2020

**GitHub**: [https://github.com/earnestt1234/FED3_Viz](https://github.com/earnestt1234/FED3_Viz)



### Welcome!

Welcome to FED3 Viz, a Python GUI for graphing data from FED3 devices.  This manual will describe the basic functionalities of FED3 Viz and how to use them.  It will also try to address any common confusions/errors that may pop up.

You can find the FED3 Viz landing page at [GitHub](https://github.com/earnestt1234/FED3_Viz); all changes to the program will be made and logged though GitHub.  I wrote this application while working as a research technician in the Kravitz Lab (with input from Dr. Kravitz and the rest of the lab!).

If you do notice any inaccuracies, typos, misinformation, or missed content in this manual, please report the issue through GitHub.  You can also find this manual as a PDF under `FED3_Viz/pdfs`.

Thanks!

Tom Earnest ([@earnestt1234](https://github.com/earnestt1234))

### Installation

On the FED3 Viz GitHub, there is an [Installation.md](https://github.com/earnestt1234/FED3_Viz/blob/master/Installation.md) markdown file which contains instructions on how to run FED3 Viz via either a) running the Python script or b) running a bundled application (from Windows or Mac).  This manual will only cover the use of the application once installed.

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
  - [Interpellet Interval Plot](#interpellet-interval-plot)
  - [Group Interpellet Interval Plot](#group-interpellet-interval-plot)
  - [Single Poke Plot](#single-poke-plot)
  - [Average Poke Plot](#average-poke-plot)
  - [Poke Bias Plot](#poke-bias-plot)
  - [Average Poke Bias Plot](#average-poke-bias-plot)
  - [Day/Night Plot](#daynight-plot)
  - [Chronogram (Line)](#chronogram-line)
  - [Chronogram (Heatmap)](#chronogram-heatmap)
  - [Diagnostic Plot](#diagnostic-plot)
- [Managing Plots](#managing-plots)
  
  - [Renaming Plots](#renaming-plots)
  - [New Window](#new-window)
  - [Navigation Toolbar](#navigation-toolbar)
  - [Saving Plots](#saving-plots)
    - [Saving Images](#saving-images)
    - [Saving Data](#saving-data)
    - [Saving Code](#saving-code)
  - [Deleting Plots](#deleting-plots)
- [Settings](#settings)

  - [Saving Settings](#saving-settings)
  - [Default Settings](#default-settings)
  - [Last Used Settings](#last-used-settings)
- [FAQ](#faq)
- [Appendix](#appendix)
- [Averaging Methods Diagram](#averaging-methods-diagram)
  - [Plot Column Dependencies](#plot-column-dependencies)

<div style="page-break-after: always; break-after: page;"></div> 

# Tour

This section will introduce the layout of FED3 Viz, and define some areas of the application.  FED3 Viz has four different panes, which can be selected by clicking the following tabs at the top of the application window.

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

1. The **Info Bar** shows helpful text for the Home Tab.  Hover over a button or select a plot to show a brief description.  A progress bar will also display here when loading FEDs.
2. The top row of buttons, which are tools for loading and managing data files within FED3 Viz.
3. The **File View** is the largest element of the Home Tab.  When a FED data file is loaded, it will appear as a row in the File View.  Each column will show data associated with that data file.
4. The **Group View** lists all the currently loaded "groups," used for combining data from multiple FEDs (see the "Groups" section below).
5. The **Plot Selector** pane, where you can choose which plots to make for the loaded devices.
6. The **Create Plot Button**, which creates a plot based on the loaded device files and the selection in the Plot Selector.  Whether or not this button is active depends on what data have been loaded into the application; for example, most plotting buttons must have some files selected in order to be active.

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

FED3 Viz will attempt to load every file `.csv` or `.xlsx` file selected by the Load Button file dialogue using a Python library for working with tabular data (`pandas`).  The loading process first tries to parse the file to find columns matching the standard FED3 data columns (as of the time of writing this manual).

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

Further discussion of problems with loading may be brought up in the [FAQ](#FAQ) as the application develops.  Additionally, the dependent columns of each plot can be viewed in the Appendix.

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
- Select the FED files to include in the plot, either by clicking or by Grouping
- Highlight the desired plotting function from the Plot Selector
- Hit the Create Plot Button

This section will go through the plot buttons currently available in the Home Tab and describe the plots they create.

There are a couple settings which apply to multiple plots: 

- *Shading dark periods*:  When enabled, applicable plots will have a light gray shading during periods when the lights are off - this can help for detecting circadian patterns of activity.  This setting can be toggled from **Settings > General > Shade dark periods (lights on/off)**.  The start and and time of the dark period can be selected using the dropdown menus next to this setting. Plots which make use of this feature will include a :new_moon_with_face: symbol in their description
- *Using Groups*: Some plots aggregate data and rely on Groups.  By default, plots which rely on Groups will **plot all Groups present in the Group View**; you can instead use the Group View to select which Groups to include by unticking **Settings > General > For plots using groups, include all loaded groups rather than those selected**.  Plots that utilize groups will be tagged with a :paperclip: symbol in their description.
- *Handling multiple selections*: For plots that don't use Groups, the data to plot depends on which loaded FED data are highlighted.  More than one file can be highlighted at once, and there are two main ways the program deals with this.  Buttons that combine the highlighted files into one graph are marked by :bar_chart:, while buttons that create multiple plots (one for each highlighted file) are marked by :bar_chart::bar_chart::bar_chart:.
- *Pellet & Poke Averaging:*  Several plots that average data on pellet retrieval and pokes rely on specific settings for determining the method of averaging across a time series.  These settings occur under the heading **Averaging (Pellet & Poke Plots)**, and plots that use them will include a 🧮 symbol in their description.  These settings include:
  
  - **Error value for average plots:**  How to show the spread of data.  Options are SEM (standard error of the mean), STD (standard deviation), raw data (data for each device shown around the average), or None.
  - **Bin size for averaging (hours):** how frequently to average data (must be done as pellets are logged to the second)
  - **Alignment method for averaging:**  How to deal with alignment of time series.  The three options are:
    - **shared date & time**: The program only averages over *absolute date & time*; i.e. only FEDs that were active at the same time can be averaged, and averaging can only be done for the window of time where **all** FEDs in the Groups are active.  This option makes sense for experiments where devices were started and ended at the same time.
    - **shared time**: The program averages over time of day but disregards the date; i.e., the program aligns the files to the first occurrence of a selected time, and then creates an average.  This setting requires you to specify the **Start time & length of averaging (time/days)** (what time of day to align the data to and how many days to try and average).  This option makes sense for experiments where devices were recording on different days or from different cohorts of mice, but you want circadian patterns to be preserved.
    - **elapsed time**: The program disregards both time of day and data and instead averages over the elapsed recording time.  This options makes sense for experiments where you want to visualize mice activity relative to the start of each recording, and you want to disregard the time of day when the recording was created.
    
    A diagram illustrating these different types of averaging can be found in the [Appendix](#averaging-methods-diagram).  Note the a warning may be raised, or an empty plot may be created, if there are no times when the selected files can be averaged.

### Single Pellet Plot

*Can use night shading* :new_moon_with_face:

*Creates one plot for each highlighted file* :bar_chart::bar_chart::bar_chart:

<p align="center">
	<img src="img/examples/pelletplot.png" width="500">
</p>

This plot shows the pellets retrieved over time for a single data file.  By default, the raw *Pellet_Count* column (the cumulative total) is plotted against the timestamps (**Settings > Individual Pellet Plots > Values to plot > Cumulative**).  This can be changed to show the sum of pellets retrieved at a specified bin size using **Settings > Individual Pellet Plots > Values to plot > Frequency** and **Settings > Individual Pellet Plots > Bin size of pellet frequency (hours):**

<p align="center">
	<img src="img/manual/freqplot.png" width="500">
</p>
Highlighting a single 

The color of these plots can be set, also (**Settings > Individual Pellet Plots > Default color (single pellet plots**)).

### Multi Pellet Plot

*Can use night shading* :new_moon_with_face:

*Combines all highlighted files into a single plot* :bar_chart:

<p align="center">
	<img src="img/examples/multipellet.png" width="500">
</p>

Multi Pellet Plots are basically Single Pellet Plots, but individual devices are plotted as separate lines.  As above, either the cumulative amount or binned frequency of pellet retrieval can be plotted.

The only additional setting is **Settings > Individual Pellet Plots > Align multi pellet plots to the same start time**.  When ticked (as above), pellets will be plotted against the *elapsed time* (since each device started); this prevents shading of dark periods.  When unticked (default), the *absolute date/time* will be preserved, so FEDs which were recorded at different times will not overlap.

### Average Pellet Plot

*Can use night shading* :new_moon_with_face:

*Uses groups* :paperclip:

*Uses averaging methods* 🧮

<p align="center">
	<img src="img/examples/average.png" width="500">
</p>

Average Pellet Plots average the pellets retrieved for each file in a Group.  Each group in the plot is plotted as a separate line.

### Interpellet Interval Plot

*Combines all highlighted files into a single plot* :bar_chart:

<p align="center">
	<img src="img/manual/ipi_kde.png" width="500">
</p>

The Interpellet Interval Plot is a histogram where the values counted are the time between each pellet retrieval event.  This plot can give you a sense of how the mouse feeds or earns pellets, and it show changes in meal or eating frequencies.

This plot is a fairly unaltered use of [`seaborn.distplot`](https://seaborn.pydata.org/generated/seaborn.distplot.html).  The only option, **Settings > Interpellet Interval Plots > Use kernel density estimation** toggles the `kde` argument of this function:

- When ticked, a kernel density estimation (KDE) is used to model the probability density function of the interepellet intervals.  The density estimation is plotted on the y-axis: the area under the whole curve of the KDE is 1, and the area under a certain portion estimates the probability of observations occurring within that portion.
- When unticked, a raw histogram is parted, the KDE line is removed, and the y-axis represents counts in each bin.

Note that Interpellet Interval Plots use logarithmically spaced x-axes (in minutes).

### Group Interpellet Interval Plot

*Uses groups* :paperclip:

<p align="center">
	<img src="img/manual/group_ipi.png" width="500">
</p>

Same as the Interpellet Interval Plot (see above), except this version plots groups as separate curves.  The Interpellet Intervals from the files of every group are appended to one array, and then plotted.  The KDE line can also be turned on or off.

### Single Poke Plot

*Can use night shading* :new_moon_with_face:

*Creates one plot for each highlighted file* :bar_chart::bar_chart::bar_chart:

<p align="center">
	<img src="img/manual/pokeplot.png" width="600">
</p>
The Poke Plot shows the amount of pokes overtime for a single file.  The file is binned at a user-specified frequency, and the amount of pokes within each bin is plotted.  Settings for tweaking this plot are under **Settings > Individual Poke Plots**:

- **Values to plot**: How to represent the pokes plotted (cumulative, frequency per bin, or percent per bin)

- **Bin size for poke plots (hours)**: The size of bins for resampling
- **Show correct pokes**: Shows the amount of correct pokes when ticked
- **Show incorrect pokes**: Shows the amount of errors when ticked

### Average Poke Plot

*Can use night shading* :new_moon_with_face:

*Uses groups* :paperclip:

*Uses averaging methods* 🧮

<p align="center">
	<img src="img/manual/avg_correctpokes.png" width="700">
</p>

The Average Poke Plot creates a Group average of either correct or incorrect pokes (depending on the selection from the Plot Selector).  Currently, the frequency of pokes per bin (rather than the cumulative total or percentage) must be plotted.

### Poke Bias Plot

*Can use night shading* :new_moon_with_face:

*Creates one plot for each highlighted file* :bar_chart::bar_chart::bar_chart:

<p align="center">
	<img src="img/manual/pokebias.png" width="700">
</p>

The Poke Bias Plot visualizes the preference for one poke versus another over time.  The program bins the data (at a frequency set by **Settings > Individual Poke Plots > Bin size of poke plots (hours)**), and for each bin computes the difference in the amount of one type of poke versus another.  Either the difference between correct & incorrect pokes, or left & right poke (regardless of correctness) can be visualized (**Settings > Individual Poke Plots > Comparison for poke bias plots **).  By default, the program will use a red-white-blue color map to highlight the bias; it can be changed to a single solid color by unticking **Use dynamic color for bias plots***.

*Note that the dynamic coloring of the line plots is actually made by creating a scatter plot of thousands of points, rather than a true line plot (this is easier given options provided by `matplotlib`).  In some cases, the dots may be visible rather than a complete line; a work around for this would need to increase the density of points created in the source code (the `DENSITY` argument in the `poke_bias` function of `plots/plots.py`).

### Average Poke Bias Plot

*Can use night shading* :new_moon_with_face:

*Uses groups* :paperclip:

*Uses averaging methods* 🧮

<p align="center">
	<img src="img/manual/avg_pokebias.png" width="700">
</p>

Average Poke Bias plots average the poke bias (see above) for Grouped devices.  Note that the dynamic coloring style cannot be used here.

### Chronograms (Line)

*Can use night shading* :new_moon_with_face:

*Uses groups* :paperclip:

<p align="center">
	<img src="img/manual/chronoline.png" width="700">
</p>

The "Chronogram" is one way of visualizing circadian activity in FED3 Viz.  The line plot shows the average 24-hour pattern of a variable for a Group of devices.  The data are resampled to hour-long bins, and matching hours across multiple days are averaged for each device to create 24 points (one for each hour of the day).  The individual files within each Group are then averaged and plotted.

There are a few settings which affect these plots, as well as the other Circadian Plots ([Chronogram (Heatmap)](#chronogram-heatmap) and [Day/Night](#daynight-plot)]):

- **Values to plot**: What values are being plotted on the y-axis.  Options are pellets, interpellet intervals, retrieval time (of pellets), correct pokes, and errors; the latter two can also be expressed as a percent.
- **Error value**: What values to use to create error bars; options are SEM (standard error of the mean), STD (standard deviation), or None.
- **Show individual FED data points**: When ticked, values for individual recordings are superimposed over the bars to show the values contributing to the average.  For Chronogram (Line) plots, ticking this will override the **Error value**.

These plots all refer to the light/dark cycle, which is set under **Settings > General > Shade dark periods (lights on/lights off)**.

### Chronogram (Heatmap)

*Combines all highlighted files into a single plot* :bar_chart:

<p align="center">
	<img src="img/manual/chronoheat.png" width="700">
</p>

The Heatmap version of the Chronogram is simply a different representation of the data from the Chonogram (Line) Plot (see above).  Rather than an average line, each file is shown as a row in a heatmap, where the colors correspond to the selected variable value over the averaged 24-hour period.

Note that this plot type does not use Groups; it plots what is selected in the File View, and provides an average of them in the final row of the heatmap.

### Day/Night Plot

*Uses groups* :paperclip:

<p align="center">
	<img src="img/examples/daynightplot.png" width="500">
</p>

Day/Night Plots show average values for Groups of data during daytime and nighttime.  What is consider day or night is set by the times selected in **Settings > General > Shade dark periods (lights on/off)**.  Regardless of the value plotted, the bars represent the *Group average of the daily or nightly average values of each file*.  That is, for each file, the program averages the selected value for all its day or night periods; those values represent the individual FED data points, and they are averaged to create the value for the bar.  Note that both individual values and error bars can be shown for these plots.

### Diagnostic Plot

*Can use night shading* :new_moon_with_face:

*Creates one plot for each highlighted file* :bar_chart::bar_chart::bar_chart:

<p align="center">
	<img src="img/examples/diagnostic plot.png" width="500">
</p>

The Diagnostic Plot is used to help identify problems with the FED over the course of its recording.  It is a 3 panel plot, which shows the pellets retrieved, motor turns, and battery life over time.

The motor should only need to turn a few times (under 10) for each pellet dispensed.  Slightly higher values than this (10-50) may represent the FED's mechanism to try and unjam, while much higher values (>100) may represent a longer pellet jam.

<div style="page-break-after: always; break-after: page;"></div> 

# Managing Plots

When a plot is created using a button on the Home Tab, the Plots Tab will be raised and the newest plot will be shown in the Display Pane.  All active plots will be shown in the Plot List, and clicking the name of the plot will render it in the Display Pane.  

The Plots Tab has additional buttons which allow you to manage and save your plots; there are also some additional features which allow for editing of the plot after creation.

### Renaming Plots:

To rename a plot, select a **single** plot from the Plot List, and click the **Rename Button**.  In the text entry box that pops up, enter a new name for the plot and click OK.  Plot names must be unique.

### New Window:

To show plots in a new window, select one or more graphs from the Plot List and click the  **New Window Button**.  This feature allows for viewing of multiple graphs simultaneously.

### Navigation Toolbar:

<p align="center">
	<img src="img/manual/toolbar.png" width="250">
</p>

FED3 Viz includes a `matplotlib` interactive toolbar for editing rendered plots.  This can be used to limit the axes, zoom in on a certain region of the graph, or alter the aspect ratio.  Specific guidance on how to use this tool can be found [here](https://matplotlib.org/3.1.1/users/navigation_toolbar.html), but note that the keyboard shortcuts will not work.

### Saving Plots

There are three main aspects of plots which can be saved in FED3 Viz: images, data, and code.

Note that by default, FED3 Viz will not overwrite images or data saved with conflicting names.  This can be changed by checking **Settings > General > Overwrite plots & data with the same name when saving**.

##### Saving Images

To save plots, highlight one or more plots from the Plot List and click the **Save Plots Button**.  This will bring up a file dialogue, and prompt the user to select a folder to save the images in.   Plots are saved in `.png` format at 300 DPI.  The name of the file will be the same as the plot's name in the Plot List.  Note that the Navigation Toolbar also has a button that can save plots, but using it (in this case) will limit the DPI to 150.

##### Saving Code

<p align="center">
	<img src="img/manual/plotcode.png" width="400">
</p>

FED3 Viz can return the code used to create each plot through the **Plot Code Button**.  The aim of this feature is to allow users to be able to tweak graphs (with Python) in ways not possible from FED3 Viz. 

Each plot button in FED3 Viz is associated with one or more plotting functions defined in Python; settings from the Settings Tab translate into arguments passed to these functions.  The Plot Code Button uses Python's `inspect` library to return the source code of these plotting functions.  The program formats this code with additional lines that are specific to each plot, like the data source and the settings used.

**The Plot Code output should be a functional script**; that is, running the script in a separate Python session should recreate the plot (given the appropriate packages and package versions in that environment).  To achieve this, the output script has to include the following:

- a list of packages to import
- the definition of a class used to load FED3 data and do some preprocessing
- definitions of helper functions used by the plotting function
- definition of the plotting function
- assignment of the specific arguments used by the function for the plot
- a line calling the function

All this makes the code somewhat verbose, but it aims to make the script run-able without modification.

Plot Code is displayed in a new window, and can be saved as a `.py` or `.txt` file using the Save As... button at the bottom of the window.

**Saving Data**

Clicking the **Save Plot Data Button** will export one or more `.csv` files which contain the values plotted; the format depends on the type of graph.  These files can be used to recreate graphs or run statistics in separate software.  Clicking the Save Plot Data Button will bring up a file dialogue, and will ask the user to select a location for saving the output.

### Deleting Plots

To delete plots, highlight one or more plots from the Plot List and hit the **Delete Button**.

<div style="page-break-after: always; break-after: page;"></div> 

# Settings

Most of the settings available on the Settings Tab pertain to plots and were described above.  There are a couple additional aspects of the Settings menu which will be described here.

### Saving Settings

FED3 Viz can save settings and load settings in case of specific user preferences.  Settings files are saved in `.csv` format, and they preserve the state of all settings in the Settings Tab.  There is a default **Settings Folder** for saving settings, which depends on the installation method:

- **Windows or Mac Executable:** `fed3viz/settings/`
- **Python Script** (i.e. GitHub source code): `FED3_Viz/FED3_Viz/settings/`

To save the current settings, click the **Save Button** under **Settings > Save/Load Settings.**  This will prompt you to provide a name for the settings file.

Settings can later be loaded by using the **Load Button** under **Settings > Save/Load Settings**.  This will default to looking in the Settings Folder.

### Default Settings

The Settings Folder comes with a `DEFAULT.CSV` file, and the program attempts to load this every time it starts up.  You can overwrite this file, or save any other settings as `DEFAULT.CSV` in order to load them automatically at startup.  If this file cannot be found or is improperly formatted in anyway, it will not be loaded and the application will fall back to some built-in default settings.

### Last Used Settings

There is also an option to remember the settings used the last time the application was closed.  Every time the program closes, it writes a `LAST_USED.CSV` file into the Settings Folder, containing the state of settings at that time.  If you have checked **Settings > Save/Load Settings > Load last used settings when opening**, these settings will be loaded.  

<div style="page-break-after: always; break-after: page;"></div> 

# FAQ

This section will mainly cover troubleshooting and issues; please also check the manual for discussion of specific functions and features.

- **I downloaded the executable but it won't run.**   Unfortunately, I am fairly unaware of the exact system requirements for FED3 Viz (it was built with `PyInstaller`, which is largely a black box to me).  If on Windows, one thing you can try is running the `.exe` from the command line (`cd` into the directory and then enter `fed3viz.exe`).  This will leave the console open and may provide an error message which can be shared.  On Mac, the Terminal can similarly be inspected.  

  If the error persists, I would instead recommend trying to run FED3 Viz from the Python script (Method 2 of the Installation instructions).  This is more likely to be troubleshooted successfully.
  
- **The program slows down, doesn't respond, or crashes.**  In previous iterations of the code, I experienced slowdown when many FED files were loaded in one go (especially with long files) or when a plot was created with many devices shown as separate curves.  In my experience, the program recovered and finished the loading/plotting after a few seconds.  To avoid these issues, I had to select fewer (10 or less) devices when loading (i.e. per push of the Load Button) or plotting devices.  However, changes since then have cleared up some of these issues (on my end; the program now "checks in" in between each device load or plot creation).  If the problems on your device result in frequent crashes or persistent slow downs, even when using small amounts of data, please report this.  I have taken a relatively minimal approach to optimizing speed, and there may be ways to improve.

- **I can't load some of my FED data, or I can load but some plots don't work**.  The most likely cause is that you have a previous version of FED output data, or that there have been edits to raw data.  FED3 Viz tries to handle old formats of the data, but there may be cases which cannot be caught.  Some examples of current data are included on GitHub in the `example_data` folder.  You can compare your data to these to see if there might be any obvious differences; you can also test that the example data load correctly.  Please share any specific issues on GitHub.

- **One of the plots I made looks weird.**  By "looks weird" I mean things like broken lines, empty areas of the plot, lines during off periods, smooshed axes text, or completely empty plots.  "Issues" like this may occur given some specific cases of data; I put issues in quotes because some peculiarities may actually accurately reflect the data (say if they have missing values or are temporally distant from each other).  Hopefully, this manual can give you an intuition of the processing that goes into creating a specific plot.

  On the other hand, if "looks weird" means you think the plot isn't actually representing the data, or the plot doesn't match one you have created, this could reflect a code error, or an unclear description of what the plots are doing.  Regardless of what "looks weird" means, I would be happy discuss and sort out any specific cases.

- **I'm seeing console errors & warning when starting up or running the program.**  Some of these are to be expected, and you shouldn't worry about them if the program continues to work as expected.  If there are functional issues, please report these errors.

- **On Mac, I don't get the option to select some files when loading.**  This is a bug right now; try to change the file types searched for from "All" to another option, and then back to "All".

- **I'm encountering issues when using files with the same name**.  Please report these; there could be some errors with duplicate files or files with exactly matching names which need to be resolved.  The easiest workaround before a fix is to rename files (outside of FED3 Viz) to be unique. 

- **Will there be more plots/features added?**  Yes!  FED3 Viz will likely be worked on through Summer 2020.  There are more features in the works, particularly in regards to the operant functions of FED3 Viz.  Please share any suggestions for development on GitHub or the FED3 Google Group.

- **I saved the Python code for a plot and it doesn't run.**  This could be due to many issues, but some possible causes are:
  
  - You are not using Python 3
  - You do not have the necessary packages installed, or their versions are incompatible with FED3 Viz.  The packages used by FED3 Viz are documented in the `requirements.txt` file on GitHub
  - Your IDE is not showing the plot (sometimes an issue with how inline plotting is handled; sometimes this causes plots not to show on the first run)
  - There is an error in the output plot script, which is certainly possible!  The most likely issues are that some of the necessary helper functions were not included or the arguments are improperly formatted.  Please report these errors on GitHub with the specific context, both to help solve your specific case and to improve the application.
  
- **I have suggestions for improving the plot code I saved.**  Please note that FED3 Viz's plotting functions are designed to handle different settings on the fly, and the code to make one specific plot may be writable in a much less verbose way.  Some pieces of the code may be helpful for the application, but irrelevant to your specific plot.  

  That being said, I would enjoy discussing (on GitHub) and possibly including any proposed changes which significantly contribute to the readable or speed of the code.  Aside from that, sharing code may be useful for other users.

- **I can't load some settings, or my settings look weird.**  This could be an issue with altered setting files, or settings files with which have entries that don't match the application.  Please redownload the `DEFAULT.CSV` and `LAST_USED.CSV` files from GitHub and replace them in your FED3 Viz folder.  Alternatively, try to save new settings from the application to overwrite the `DEFAULT.CSV` file.

- **I have an issue that I have shared and I haven't heard back from anyone.**  Please be aware that FEDs are being worked on by a small group of researchers, and FED3 Viz is only really maintained by me :sunglasses:.  We will do our best to respond prudently to questions shared online, but bear with us!

<div style="page-break-after: always; break-after: page;"></div> 

# Appendix

<div style="page-break-after: always; break-after: page;"></div> 

### Averaging Methods Diagram

See in higher resolution at `FED3_Viz/img/manual/average_illustration.png`.

<p align="center">
	<img src="img/manual/average_illustration.png" width="800">
</p>

<div style="page-break-after: always; break-after: page;"></div> 

### Plot Column Dependencies

This table shows which columns of a FED3 data file are used by FED3 Viz to create each plot.  If a file is missing a column, or contains changes in a column, associated plots may not be able to be created.

| **Plot**                     | **MM:DD:YYYY hh:mm:ss** | **Pellet_Count**   | **Left_Poke_Count** | **Right_Poke_Count** | **Active_Poke**    | Retrieval_Time     | **Battery_Voltage** | **Motor_Turns**    |
| ---------------------------- | ----------------------- | ------------------ | ------------------- | -------------------- | ------------------ | ------------------ | ------------------- | ------------------ |
| Single Pellet Plot           | :heavy_check_mark:      | :heavy_check_mark: |                     |                      |                    |                    |                     |                    |
| Multi Pellet Plot            | :heavy_check_mark:      | :heavy_check_mark: |                     |                      |                    |                    |                     |                    |
| Average Pellet Plot          | :heavy_check_mark:      | :heavy_check_mark: |                     |                      |                    |                    |                     |                    |
| Inter Pellet  Interval Plots | :heavy_check_mark:      | :heavy_check_mark: |                     |                      |                    |                    |                     |                    |
| Single Poke Plot             | :heavy_check_mark:      |                    | :heavy_check_mark:  | :heavy_check_mark:   | :heavy_check_mark: |                    |                     |                    |
| Average Poke Plot            | :heavy_check_mark:      |                    | :heavy_check_mark:  | :heavy_check_mark:   | :heavy_check_mark: |                    |                     |                    |
| Poke Bias Plot               | :heavy_check_mark:      |                    | :heavy_check_mark:  | :heavy_check_mark:   | :heavy_check_mark: |                    |                     |                    |
| Average Poke Bias Plot       | :heavy_check_mark:      |                    | :heavy_check_mark:  | :heavy_check_mark:   | :heavy_check_mark: |                    |                     |                    |
| Circadian (Pellets or IPI)   | :heavy_check_mark:      | :heavy_check_mark: |                     |                      |                    |                    |                     |                    |
| Circadian (Pokes)            | :heavy_check_mark:      |                    | :heavy_check_mark:  | :heavy_check_mark:   | :heavy_check_mark: |                    |                     |                    |
| Circadian (Retrieval Time)   | :heavy_check_mark:      |                    |                     |                      |                    | :heavy_check_mark: |                     |                    |
| Diagnostic Plot              | :heavy_check_mark:      | :heavy_check_mark: |                     |                      |                    |                    | :heavy_check_mark:  | :heavy_check_mark: |


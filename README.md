# FED3 Viz (Beta)
a GUI for plotting FED3 data

<p align="center">
	<img src="img/fedviz_textlogo.png" width="500">
</p>

## Table of Contents
- [What is FED3?](#what-is-fed3)
- [What is FED3 Viz?](#what-is-fed3-viz)
- [Current Features](#current-features)
- [Installation](#installation)
- [Beta Statement](#beta-statement)

## What is FED3?

FED3 is the [3rd version of the Feeding Experimentation Device](https://hackaday.io/project/106885-feeding-experimentation-device-3-fed3), an open-source, home-cage feeding device for mouse operant behavioral tasks.  FED3 was developed in the [Kravitz Lab](https://kravitzlab.com/) in order to run high-throughput, inexpensive experiments on reward and learning.

<p align="center">
    <img src="img/manyfeds.png" width="500">
</p>

## What is FED3 Viz?

**FED3 Viz** is software for graphing data produced from FED3 devices.  FED3 Viz is written in Python using the `tkinter` library.  FED3 Viz is meant to create a quick & easy method for visualizing FED3 data without having to edit the raw data.

<p align="center">
    <img src="img/plottab.png" width="500">
</p>

## Current Features

- Various graphs to visualize:
  - individual pellet retrieval
  - group average pellet retrieval
  - intervals between pellet retrieval
  - motor turns & battery life
  - day vs. night activity
  
- Toolbar for live plot editing (from [`matplotlib`](https://matplotlib.org/3.1.1/users/navigation_toolbar.html))

- Savable code and data for each plot

- Viewer showing properties of FED data files

- Group labels for averaging data

- Savable settings

  <p align="center">
      <img src="img/daynightplot.png" width="500">
  </p>

## Installation

FED3 Viz can either be run from a packaged application file, or from a Python interpreter.  Specific instructions for installation and system requirements can be found [here](https://github.com/earnestt1234/FED3_Viz/blob/master/Installation.md).

## Beta Statement

**This program is currently in "beta"**: it has only been tested by a few individuals on their machines, with a small selection of data files.  Additionally, the program is still being actively worked on, and likely will be through summer 2020.  I am eager to have other people try the application and report bugs, preferably through GitHub or on the [FED3 Google Group](https://groups.google.com/forum/#!forum/fedforum).  

Moreover, we will certainly consider and try to meet any requests for additional features/graphs! I appreciate the [input so far*](https://groups.google.com/forum/#!topic/fedforum/YhF0pzMGD9c), and would love more.

*The user-requested features so far have not been implemented, but working on it :sweat_smile:




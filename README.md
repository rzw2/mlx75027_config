# MLX75027 Sensor Configuration

## Description

This Python utility is for calculating the register values of the [MLX75027](https://www.melexis.com/en/product/MLX75027/Automotive-VGA-Time-Of-Flight-Sensor) Time-of-Flight image sensor. 

There is a set of functions in the mlx75027_config folder for calculating register values and for importing and export csv files. 

A Tkinter GUI is provided for visually setting the values and generating configurations, this GUI is in the configTool folder.  

## Installation

Add the this folder (the one with the README.md in) to your PYTHONPATH variable. 

## Using 
The run the Tkinter GUI
    
    python MLX75027_RegisterMap.py 

The mlx75027.csv file contains the registers, there names and the default values. 

The test cases can be run in the test folder 

    python MLX75027ConfigTest.py 

## Documentation 

The version of the datasheet v0.8 that this tool was written for is provided in the doc folder for reference, as the datasheet might be updated by Melexis. 

## Contact 

For comment, assistance or bug reporting (or the correct interpretation of the datasheet) please contact Refael Whyte, r.whyte@chronoptics.com 

[Chronoptics](https://www.chronoptics.com) designs and develops 3D time-of-flight depth sensing cameras, contact us for any of your 3D ToF needs. 

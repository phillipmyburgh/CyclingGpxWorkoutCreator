# Cycling Gpx Workout Creator


## Introduction

If you would like to simulate riding a race/course on your Tacx smart indoor trainer, and you have the *Tacx Training Software*, but you don't want to buy/use the Google Licence, then this is the script for you.


The main script uses a library which can do math on GPS coordinates and manipulate and analyze GPX files. All the tools needed to do just this one task can later be harnessed to create other tools.

The main script **ConvertGpxToTcx** takes the GPS coordinates from a given GPX file and converts it into a slope/distance Tacx workout. The indoor training application would then be responsible to "simulate" the speed using parameters such as rider weight, bike type and frontal area.


## Installation
All the scripts require *Python 2.7.* and *pip*. You can [search the internet](http://lmgtfy.com/?q=Install+Python+2.7) for installation instructions.

Additional Python packages are contained in the *requirements.txt* file. If you have *pip*, then you can install the packages using the commandline:
	
	pip install -r requirements.txt

# GpxLib
The *GpxLib.py* library is where everything really happens. This library has some nice functions such as:

* Haversine: Calculating the great-circle distance between points
* Google Polyline encoding
* Getting corrected elevation data from the Google Maps API
* Plotting
* And everything that has been needed to create the other scripts


## Usage
To run any of the scripts you have to open up the terminal/commandline in the repository folder.

### What is this ".gpx" file needed by the scripts?
A GPX file (GPS Exchange) is an open standard in which GPS locations, elevations, waypoints etc. can be stored and exchanged.


### Where to get the input .gpx file?
Most training applications can export previous cycling workouts to a GPX file. Here are some examples of how to get a gpx file:

1. **Strava:** With strava you can download the GPX file from any of your friend's workouts
2. **Garmin Connect:** With Garmin Connect you can create a course by "drawing" it onto a map, and then export this as GPX


### Google API Key
Some scripts give you the option to include a Google Maps API key. You can get a free key from [here](https://developers.google.com/maps/documentation/javascript/get-api-key) which will then allow the script to download accurate elevation information from the Google Maps server.

###Drag-and-Drop option
In the bin/Windows folder you will find .bat files for each of the python scripts. These allow you to drag-and-drop the gpx file(s) onto the .bat file, which would then in turn invoke the python script.

You can add your Google API key into the ApiKey.txt file, which can then be used by these Windows wrappers.

### Converting GPX to slope-distance TCX workout
```
python ConvertGpxToTcx.py [-h] [--apiKey APIKEY]
                          [--outputFilename OUTPUTFILENAME]
                          [--interpolationResolution INTERPOLATIONRESOLUTION]
                          [--startDistance STARTDISTANCE]
                          [--stopDistance STOPDISTANCE] [--plot]
                          inputFilename
                          
positional arguments:
  inputFilename         Input Filename

optional arguments:
  -h, --help            show this help message and exit
  --apiKey APIKEY, -a APIKEY
                        Google Maps API Key
  --outputFilename OUTPUTFILENAME, -o OUTPUTFILENAME
                        Output Filename (defaults to <inputFilename>.tcx
  --interpolationResolution INTERPOLATIONRESOLUTION, -r INTERPOLATIONRESOLUTION
                        Resolution of the interpolation in meter (defaults to
                        100m)
  --startDistance STARTDISTANCE, -start STARTDISTANCE
                        Trims everything before the start distance (default
                        0m)
  --stopDistance STOPDISTANCE, -stop STOPDISTANCE
                        Trims everything after the stop distance
  --plot, -p            Flag without a value to enable plotting
```

### Show GPX Profile
```
python ShowGpxInformation.py [-h] [--apiKey APIKEY]
                             [--interpolationResolution INTERPOLATIONRESOLUTION]
                             [--startDistance STARTDISTANCE]
                             [--stopDistance STOPDISTANCE]
                             inputFilename

Show profile information of the given .gpx file

positional arguments:
  inputFilename         Input Filename

optional arguments:
  -h, --help            show this help message and exit
  --apiKey APIKEY, -a APIKEY
                        Google Maps API Key
  --interpolationResolution INTERPOLATIONRESOLUTION, -r INTERPOLATIONRESOLUTION
                        Resolution of the interpolation in meter (defaults to
                        100m)
  --startDistance STARTDISTANCE, -start STARTDISTANCE
                        Trims everything before the start distance (default
                        0m)
  --stopDistance STOPDISTANCE, -stop STOPDISTANCE
                        Trims everything after the stop distance
```

### Compare Profiles
```
python CompareProfiles.py [-h] [--apiKey APIKEY]
                          [--interpolationResolution INTERPOLATIONRESOLUTION]
                          [--startDistance STARTDISTANCE]
                          [--stopDistance STOPDISTANCE]
                          [inputFilenames [inputFilenames ...]]

Compare the profiles of multiple .gpx files

positional arguments:
  inputFilenames        Input Filenames

optional arguments:
  -h, --help            show this help message and exit
  --apiKey APIKEY, -a APIKEY
                        Google Maps API Key
  --interpolationResolution INTERPOLATIONRESOLUTION, -r INTERPOLATIONRESOLUTION
                        Resolution of the interpolation in meter (defaults to
                        100m)
  --startDistance STARTDISTANCE, -start STARTDISTANCE
                        Trims everything before the start distance (default
                        0m)
  --stopDistance STOPDISTANCE, -stop STOPDISTANCE
                        Trims everything after the stop distance
                        
```


## Testing Frameworks
Unit tests for the GpxLib are run on the **Travis CI** platform:

[![Build status](https://travis-ci.org/phillipmyburgh/CyclingGpxWorkoutCreator.svg?master)](https://travis-ci.org/phillipmyburgh/CyclingGpxWorkoutCreator)
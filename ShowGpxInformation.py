# (c) 2018 Phillip Myburgh
# Distributed under the MIT Licence


import sys
import os
# To parse command line arguments
import argparse

from GpxLib import *



argumentParser = argparse.ArgumentParser(
                description='Show profile information of the given .gpx file')
argumentParser.add_argument('inputFilename', type=str, help='Input Filename')
argumentParser.add_argument('--apiKey', "-a", type=str, help='Google Maps API Key')
argumentParser.add_argument('--interpolationResolution', "-r", type=int, help='Resolution of the interpolation in meter (defaults to 100m)')
argumentParser.add_argument('--startDistance', "-start", type=int, help='Trims everything before the start distance (default 0m)')
argumentParser.add_argument('--stopDistance', "-stop", type=int, help='Trims everything after the stop distance')

commandlineArguments = argumentParser.parse_args()

inputFilename = commandlineArguments.inputFilename
apiKey = commandlineArguments.apiKey
interpolationResolution = commandlineArguments.interpolationResolution
startDistance = commandlineArguments.startDistance
stopDistance = commandlineArguments.stopDistance


# If the interpolation resolution was left out, set it to 100m
if interpolationResolution is None:
    interpolationResolution = 100

if startDistance is None:
    startDistance = 0
if stopDistance is None:
    stopDistance = 0

print "Parsing ", inputFilename, "..."

gpxCourse = ParseGpxFile(inputFilename)

print "There are " + str(gpxCourse.GetNumberOfPoints()) + " gps points..."
print "Interpolating..."

gpxCourse = gpxCourse.InterpolateToGivenResolution(interpolationResolution)

if startDistance > 0 or stopDistance > 0:
    print "Trimming..."
    if stopDistance == 0:
        stopDistance = sys.maxint
    gpxCourse = gpxCourse.PruneDistance(stopDistance, startDistance)

print "There are " + str(gpxCourse.GetNumberOfPoints()) + " gps points after interpolation..."

if apiKey:
    print "Getting all the elevation data from google..."
    gpxCourse = gpxCourse.CorrectElevation(apiKey)

profile = gpxCourse.CreateEquidistantProfile(interpolationResolution)

if profile.GetElevationGain() == 0 and apiKey is None:
    print "Elevation data seems to be missing. You would need an API key to retrieve this info from the internet."

PlotProfile(profile, 0, "Course Profile")

print "Done!!!"

raw_input("Press Enter to continue...")
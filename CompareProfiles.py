# (c) 2018 Phillip Myburgh
# Distributed under the MIT Licence


import sys
import os
# To parse command line arguments
import argparse

from GpxLib import *



argumentParser = argparse.ArgumentParser(
                description='Compare the profiles of multiple .gpx files')
argumentParser.add_argument('inputFilenames', type=str, help='Input Filenames', nargs='*')
argumentParser.add_argument('--apiKey', "-a", type=str, help='Google Maps API Key')
argumentParser.add_argument('--interpolationResolution', "-r", type=int, help='Resolution of the interpolation in meter (defaults to 100m)')
argumentParser.add_argument('--startDistance', "-start", type=int, help='Trims everything before the start distance (default 0m)')
argumentParser.add_argument('--stopDistance', "-stop", type=int, help='Trims everything after the stop distance')

commandlineArguments = argumentParser.parse_args()

inputFilenames = commandlineArguments.inputFilenames
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

print "Parsing..."

profiles = []
for filename in inputFilenames:
    print "Parsing " + filename + "..."
    gpxCourse = ParseGpxFile(filename)
    print "    Interpolating..."
    gpxCourse = gpxCourse.InterpolateToGivenResolution(interpolationResolution)
    if startDistance > 0 or stopDistance > 0:
        print "    Trimming..."
        if stopDistance == 0:
            stopDistance = sys.maxint
        gpxCourse = gpxCourse.PruneDistance(stopDistance, startDistance)

    if apiKey:
        print "    Getting all the elevation data from google..."
        gpxCourse = gpxCourse.CorrectElevation(apiKey)

    profile = gpxCourse.CreateEquidistantProfile(interpolationResolution)

    if profile.GetElevationGain() == 0 and apiKey is None:
        print "Elevation data seems to be missing from " + filename + ". You would need an API key to retrieve this info from the internet."

    profiles.append(profile)

PlotProfiles(profiles, 0)

print "Done!!!"

raw_input("Press Enter to continue...")
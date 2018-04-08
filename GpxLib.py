# (c) 2018 Phillip Myburgh
# Distributed under the MIT Licence

import math
from math import radians, cos, sin, asin, sqrt
from time import sleep
import urllib
import json
from StringIO import StringIO
import copy

import xml.etree.ElementTree
from lxml.etree import tostring
from lxml.builder import E

import matplotlib.pyplot as plt
plt.ion()


def DegreesToRadians(x):
    '''Convert Degrees to Radians'''
    return x * math.pi / 180.0


def RadiansToDegrees(x):
    '''Convert Radians to Degrees'''
    return x * (180.0 / math.pi)


def Haversine(latitude1, longitude1, latitude2, longitude2, sphereRadius):
    '''
        Determines the great-circle distance between two points on a sphere given their longitudes and latitudes
        Inputs should be in decimal degrees.
        Returns the distance in meters
    '''
    # convert decimal degrees to radians
    longitude1, latitude1, longitude2, latitude2 = map(radians, [longitude1, latitude1, longitude2, latitude2])

    # haversine formula
    dlon = longitude2 - longitude1
    dlat = latitude2 - latitude1
    a = sin(dlat / 2.0) ** 2 + cos(latitude1) * cos(latitude2) * sin(dlon / 2.0) ** 2
    c = 2.0 * asin(sqrt(a))
    return c * sphereRadius


def GetDistanceBetweenPoints(point1, point2):
    '''
        Get the 2d distance between 2 Point objects. Does not account for elevation.
        Returns distance in meters.
    '''
    radiusOfEarth = 6378.1 * 1000.0
    return Haversine(point1.latitude, point1.longitude, point2.latitude, point2.longitude, radiusOfEarth)


def GetMiddlePoint(point1, point2):
    '''
        Get the middel of 2 points.
        Modified from http://code.activestate.com/recipes/577713-midpoint-of-two-gps-points/
    '''
    lonDeg1 = DegreesToRadians(point1.longitude)
    latDeg1 = DegreesToRadians(point1.latitude)
    lonDeg2 = DegreesToRadians(point2.longitude)
    latDeg2 = DegreesToRadians(point2.latitude)
    lonDiffDeg = DegreesToRadians(point2.longitude - point1.longitude)

    bx = math.cos(latDeg2) * math.cos(lonDiffDeg)
    by = math.cos(latDeg2) * math.sin(lonDiffDeg)

    lat3 = math.atan2(math.sin(latDeg1) + math.sin(latDeg2), \
           math.sqrt((math.cos(latDeg1) + bx) * (math.cos(latDeg1) \
           + bx) + by**2))
    lon3 = lonDeg1 + math.atan2(by, math.cos(latDeg1) + bx)
    ele3 = (point1.elevation + point2.elevation) / 2.0

    return GpxPoint(RadiansToDegrees(lat3), RadiansToDegrees(lon3), ele3)


def LinearInterpolate(x1, y1, x2, y2, x):
    return ((x-x1)*(y2-y1)/(x2-x1)) + y1


def ConvertGpxPointsToPolyLineEncoding(gpxPoints):
    '''
        Basically does a lossy compression of the gpx points to an ascii string
        See for explanation: https://developers.google.com/maps/documentation/utilities/polylinealgorithm
    '''
    def GetFiveBitChunks(value):
        # Makes an array of 5 bit chunks, starting from the right (as first array element)
        fiveBitMask = (2**5)-1
        chunks = []
        while value > 0:
            chunkValue = value & fiveBitMask
            if (value > fiveBitMask): # if this isn't the last element
                chunkValue |= 0x20
            chunks.append(chunkValue)
            value >>= 5
        return chunks

    def PolylineEncodeValue(value):
        if value < 0:
            value = ~(value << 1)
        else:
            value = (value << 1)
        chunks = GetFiveBitChunks(value)
        chunks = [chunk + 63 for chunk in chunks]
        outputString = ""
        for chunk in chunks:
            outputString += chr(chunk)

        # We cannot have an empty string, otherwise the lat,lon pairs would become shredded
        # We escape 0 values with a ? (which is 0 + 63 offset)
        if outputString == "":
            outputString = "?"

        return outputString

    previousGpxPoint = GpxPoint(0,0,0)
    outputString = ""
    for gpxPoint in gpxPoints:

        latitudeDiff = int(round(gpxPoint.latitude * 1.0e5)) - int(round(previousGpxPoint.latitude * 1.0e5))
        longitudeDiff = int(round(gpxPoint.longitude * 1.0e5)) - int(round(previousGpxPoint.longitude * 1.0e5))

        outputString += PolylineEncodeValue(latitudeDiff)
        outputString += PolylineEncodeValue(longitudeDiff)
        previousGpxPoint = gpxPoint
    return outputString


def GetCorrectElevationFromGoogle(gpxPoints, apiKey):
    '''Using the Google maps API, we fill in the correct elevation for the gpsPoints'''
    outputGpxPoints = []
    maxLocationsPerRequest = 512 # 512 Location Limit according to Google
    maxRequestLength = 2000 # Not an official limit. There has been some issues online by dev's if the request is too long
    requestDelay = 1.0 / 10.0 # Google's limit is 50 requests per second. So we err on the safe side
    retries = 3
    retryBackoffTime = 5 # Wait in 5 seconds multiples before trying again

    pointsProcessed = 0
    while True:
        pointsLeft = len(gpxPoints) - pointsProcessed

        if pointsLeft == 0:
            return outputGpxPoints

        pointsToProcess = min(pointsLeft, maxLocationsPerRequest)

        # Encode the points otherwise we cannot use the maximum number of points because there is a character limit
        # for all requests. We also have to check the length of the string
        while (True):
            requestString = "https://maps.googleapis.com/maps/api/elevation/json?locations=enc:"
            polylineEncodedPoints = ConvertGpxPointsToPolyLineEncoding(gpxPoints[pointsProcessed : pointsProcessed + pointsToProcess])
            requestString += polylineEncodedPoints
            requestString += "&key=" + apiKey
            if (len(requestString) <= maxRequestLength):
                break
            # If the request is too long, decrease the number of points to process
            if (pointsToProcess <= 10):
                print "GetCorrectElevationFromGoogle> We have a problem! We cannot bring the request length down without having less than 10 points..."
                exit(2)
            pointsToProcess -= 10

        urlFp = urllib.urlopen(requestString)
        data = urlFp.read()
        try:
            js = json.loads(str(data))
        except:
            js = None

        urlFp.close()
        if 'status' not in js or js['status'] != 'OK':
            retries -= 1
            if retries <= 0:
                print '==== Failure To Retrieve ===='
                print requestString
                print "returned:"
                print data
                exit (2)

            print "Failed, Retrying in ", retryBackoffTime, "seconds..."
            sleep(retryBackoffTime)
            retryBackoffTime *= 2
            continue

        for jsonLocation in js["results"]:
            latitude = jsonLocation["location"]["lat"]
            longitude = jsonLocation["location"]["lng"]
            elevation = jsonLocation["elevation"]
            outputGpxPoints.append(GpxPoint(latitude, longitude, elevation))

        sleep(requestDelay)
        pointsProcessed += pointsToProcess



def InterpolateBetweenPoints(gpxPoints, interpolationResolution):
    '''
        Creates a new GpxPoint array so none of the points are further apart than the interpolation resolution.
        New points are placed between all points that are too far apart. The distance between points vary and are
        not equal in distance
    '''
    if len(gpxPoints) <= 1:
        return copy.deepcopy(gpxPoints)

    elif len(gpxPoints) == 2:
        distance = GetDistanceBetweenPoints(gpxPoints[0], gpxPoints[1])

        if distance > interpolationResolution:
            middlePoint = GetMiddlePoint(gpxPoints[0], gpxPoints[1])

            outputCopy = []
            # Recursively add the first + middle, and middle + last point
            outputCopy.extend(InterpolateBetweenPoints([gpxPoints[0], middlePoint], interpolationResolution))
            outputCopy.extend(InterpolateBetweenPoints([middlePoint, gpxPoints[1]], interpolationResolution))

            return outputCopy

        else:  # 2 points are fine, just return them
            return copy.deepcopy(gpxPoints)

    elif GetDistanceBetweenPoints(gpxPoints[0], gpxPoints[-1]) <= interpolationResolution:
        # if the distance between the first and the last point are still within spec, we can remove all points inbetween
        outputCopy = [gpxPoints[0], gpxPoints[-1]]
        return copy.deepcopy(outputCopy)

    outputCopy = []
    #for index in range(0, len(gpxPoints) - 1):
    upperIndex = len(gpxPoints) - 1
    outputCopy.extend(InterpolateBetweenPoints(gpxPoints[0:upperIndex/2], interpolationResolution))
    outputCopy.extend(InterpolateBetweenPoints(gpxPoints[upperIndex/2:upperIndex], interpolationResolution))
    return outputCopy


class GpxPoint:
    '''
        A single GPS point consisting of latitude, longitude and elevation
    '''
    latitude = 0
    longitude = 0
    elevation = 0
    def __init__(self, latitude, longitude, elevation):
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation


class ProfilePoint:
    '''
        A single point of a profile which consists of a distance and elevation
    '''
    distance = 0
    elevation = 0
    def __init__(self, distance, elevation):
        self.distance = distance
        self.elevation = elevation


class SlopePoint:
    '''
        A single Slope point consisting of distance, slope
    '''
    distance = 0
    slope = 0
    def __init__(self, distance, slope):
        self.distance = distance
        self.slope = slope


class GpxCourse:
    '''
        Represents a course, which is an array of GpxPoints.
        Class is immutable and will give a copy whenever you try and change something
    '''
    def __init__(self, gpxPoints):
        self.__gpxPoints = gpxPoints


    def GetNumberOfPoints(self):
        return len(self.__gpxPoints)


    # Overload the [] by returning a copy of the gpx point
    def __getitem__(self, key):
        return copy.deepcopy (self.__gpxPoints[key])


    def GetGpxPoints(self):
        return copy.deepcopy(self.__gpxPoints)


    def GetDistanceAtIndex(self, index):
        '''Get the total distance of the given array of Points, up to a certain index'''
        totalDistance = 0.0
        for index in range(0, index): # do for indices 0 to index-1
            totalDistance += GetDistanceBetweenPoints(self[index], self[index + 1])
        return totalDistance


    def GetTotalDistance(self):
        '''Get the total distance of the given array of Points'''
        return self.GetDistanceAtIndex(self.GetNumberOfPoints() - 1)


    def GetElevationAtDistance(self, distance):
        '''Finds the elevation at a given distance. Will also use linear interpolation between points'''
        # First we use binary search to find the distance
        lower = 0
        upper = self.GetNumberOfPoints() - 1
        while lower < upper:
            middleIndex = lower + (upper - lower) // 2
            middleDistance = self.GetDistanceAtIndex(middleIndex)
            if distance == middleDistance:
                return self[middleIndex].elevation
            elif distance > middleDistance:
                if lower == middleIndex:
                    break
                lower = middleIndex
            elif distance < middleDistance:
                upper = middleIndex

        # if we end up here, it means that we have to interpolate between upper and lower...
        x1 = self.GetDistanceAtIndex(lower)
        y1 = self[lower].elevation
        x2 = self.GetDistanceAtIndex(upper)
        y2 = self[upper].elevation
        elevation = LinearInterpolate(x1, y1, x2, y2, distance)

        return elevation


    def RemoveAllDuplicateGpxPoints(self):
        outputPoints = []
        outputPoints.append(self[0])
        for index in range(1, self.GetNumberOfPoints()-1):
            distance = GetDistanceBetweenPoints(self[index], self[index - 1])
            if distance > 0:
                outputPoints.append(copy.copy(self[index]))

        return GpxCourse(outputPoints)


    def CorrectElevation(self, apiKey):
        newPoints = GetCorrectElevationFromGoogle(self.GetGpxPoints(), apiKey)
        return GpxCourse(newPoints)


    def PruneDistance(self, distance, start=0):
        '''
            Return a new GpxCourse which is a copy of the current instance expect that the distance is limited
            to the distance passed as parameter
        '''
        newGpxPoints = []
        index = 0
        while index < self.GetNumberOfPoints():
            currentDistance = self.GetDistanceAtIndex(index)
            if currentDistance > distance:
                break
            if currentDistance >= start:
                newGpxPoints.append(self[index])
            index += 1

        return GpxCourse(newGpxPoints)


    def InterpolateToGivenResolution(self, interpolationResolution):
        '''
            Create a new GpxCourse where none of the points are further apart than the interpolation resolution.
            New points are placed between all points that are too far apart. The distance between points vary and are
            not equal in distance
        '''
        newGpxPoints = self.GetGpxPoints()
        newGpxPoints = InterpolateBetweenPoints(newGpxPoints, interpolationResolution)
        return GpxCourse(newGpxPoints)


    def CreateProfile(self):
        '''
            Take a Point array and return a new ProfilePoint array. 
            The profile is easier to do processing on so is a good first step
        '''
        outputPoints = []
        distance = 0.0
        outputPoints.append(ProfilePoint(distance, self[0].elevation))
        for index in range(0, self.GetNumberOfPoints() - 1):
            distance += GetDistanceBetweenPoints(self[index], self[index + 1])
            outputPoints.append(ProfilePoint(distance, self[index + 1].elevation))

        return ProfileCourse(outputPoints)


    def CreateEquidistantProfile(self, gapInMeters):
        '''
            Take a Point array and return a new ProfilePoint array where all points are equally far apart (specified by the gapInMeters
            parameter. This is extremely useful when you want to do filtering on the data because filters are highly
            dependent on the sampling frequency of the data
        '''
        # First generate a profile, then we will interpolate
        profilePoints = self.CreateProfile()

        outputPoints = []
        totalDistance = profilePoints.GetTotalDistance()
        truncatedTotalDistance = int(totalDistance)
        for distance in range(0, truncatedTotalDistance, gapInMeters):
            elevation = profilePoints.GetElevationAtDistance(distance)
            outputPoints.append(ProfilePoint(distance, elevation))

        # Now add the last point, which we did not get with the trunk
        if truncatedTotalDistance < totalDistance:
            outputPoints.append(ProfilePoint(totalDistance, profilePoints.GetElevationAtDistance(totalDistance)))

        return ProfileCourse(outputPoints)


class ProfileCourse:

    def __init__(self, profilePoints):
        self.__profilePoints = profilePoints


    # Overload the [] by returning a copy of the gpx point
    def __getitem__(self, key):
        return copy.deepcopy(self.__profilePoints[key])


    def GetNumberOfPoints(self):
        return len(self.__profilePoints)


    def GetProfilePoints(self):
        return copy.deepcopy(self.__profilePoints)


    def GetElevationGain(self):
        '''
            Get the total elevation gain of the profile. This value may be a bit optimistic on unfiltered data because
            each jitter with a positive value will increase the elevation gain.
        '''
        elevationGain = 0
        for index in range(0, self.GetNumberOfPoints() - 1):
            elevationDifference = self[index + 1].elevation - self[index].elevation
            if elevationDifference > 0:
                elevationGain += elevationDifference

        return elevationGain


    def GetTotalDistance(self):
        return self[-1].distance


    def GetHighestElevation(self):
        '''
            Get the highest elevation of the profile. 
        '''
        highestElevation = self[0].elevation
        for index in range(0, self.GetNumberOfPoints()):
            if self[index].elevation > highestElevation:
                highestElevation = self[index].elevation

        return highestElevation


    def GetLowestElevation(self):
        '''
            Get the lowest elevation of the profile. 
        '''
        lowestElevation = self[0].elevation
        for index in range(0, self.GetNumberOfPoints()):
            if self[index].elevation < lowestElevation:
                lowestElevation = self[index].elevation

        return lowestElevation


    def GetElevationAtDistance(self, distance):
        '''Finds the elevation at a given distance. Will also use linear interpolation between points'''
        # First we use binary search to find the distance
        lower = 0
        upper = self.GetNumberOfPoints() - 1
        while lower < upper:
            middleIndex = lower + (upper - lower) // 2
            middleDistance = self[middleIndex].distance
            if distance == middleDistance:
                return self[middleIndex].elevation
            elif distance > middleDistance:
                if lower == middleIndex:
                    break
                lower = middleIndex
            elif distance < middleDistance:
                upper = middleIndex

        # if we end up here, it means that we have to interpolate between upper and lower...
        x1 = self[lower].distance
        y1 = self[lower].elevation
        x2 = self[upper].distance
        y2 = self[upper].elevation
        elevation = LinearInterpolate(x1, y1, x2, y2, distance)

        return elevation


    def GetAverageDistanceBetweenPoints(self):
        return self[-1].distance / self.GetNumberOfPoints()


    def CreateSlopeCourse(self):
        '''
        Convert the Profile points to slope/distance points and return a Slope Course.
        '''
        slopePoints = []
        trailingIndex = 0
        for index in range(1, self.GetNumberOfPoints() - 1):
            previousPoint = self[trailingIndex]
            currentPoint = self[index]

            distanceBetweenPoints = currentPoint.distance - previousPoint.distance

            if distanceBetweenPoints == 0:
                continue

            elevationGainBetweenPoints = currentPoint.elevation - previousPoint.elevation
            slope = float(elevationGainBetweenPoints) / float(distanceBetweenPoints) * 100.0

            # Slopes are constant between 2 profile points. So we should make it "look" like a bar graph
            # by adding 2 points for each slope
            slopePoints.append(SlopePoint(previousPoint.distance, slope))
            slopePoints.append(SlopePoint(currentPoint.distance, slope))

            trailingIndex = index

        if len(slopePoints) == 0:
            return SlopeCourse(slopePoints)

        # Add the last point
        lastPoint = self[-1]
        lastSlopePoint = slopePoints[-1]
        slopePoints.append(SlopePoint(lastPoint.distance, lastSlopePoint.slope))

        return SlopeCourse(slopePoints)



class SlopeCourse:
    '''
    Represents a slope based course where the course is represented by slope instead of the normal elevation
    Class is immutable and will give a copy whenever you try and change something
    '''
    def __init__(self, slopePoints):
        self.__slopePoints = slopePoints


    # Overload the [] by returning a copy of the slope point
    def __getitem__(self, key):
        return copy.copy(self.__slopePoints[key])


    def GetNumberOfPoints(self):
        return len(self.__slopePoints)


    def GetSlopePoints(self):
        return copy.deepcopy(self.__slopePoints)


    def GetSlopeAtDistance(self, distance):
        '''Finds the slope at a given distance. '''
        # First we use binary search to find the distance
        lower = 0
        upper = self.GetNumberOfPoints() - 1
        while lower < upper:
            middleIndex = lower + (upper - lower) // 2
            middleDistance = self[middleIndex].distance
            if distance == middleDistance:
                return self[middleIndex].slope
            elif distance > middleDistance:
                if lower == middleIndex:
                    break
                lower = middleIndex
            elif distance < middleDistance:
                upper = middleIndex

        # if we end up here it means that we are between 2 points. We don't interpolate slopes, slopes are constant
        # and we need to return the lower bound slope
        return self[lower].slope


    def GetAverageDistanceBetweenPoints(self):
        return self[-1].distance / self.GetNumberOfPoints()


    def Compress(self):
        # TODO: Test me
        outputSlopes = []
        outputSlopes.append(self[0])
        for index in range(1, self.GetNumberOfPoints()):
            if outputSlopes[-1].slope != self[index].slope:
                outputSlopes.append(self[index])

        return SlopeCourse(outputSlopes)




def _GetAllGpxPointsFromRootXml(root):
    gpxPoints = []
    for child in root.findall('.//trkpt'):
        latitude = float(child.attrib['lat'])
        longitude = float(child.attrib['lon'])

        elevationTag = child.find("ele")

        if elevationTag is None:
            print "The file does not contain elevation data."
            exit(2)

        elevation = float(elevationTag.text)
        gpxPoints.append(GpxPoint(latitude, longitude, elevation))

    return gpxPoints



def ParseGpxFile(inputFilename):
    '''Parse the gpx file and return a GpxCourse'''
    with open(inputFilename, 'r') as myfile:
        xmlData = myfile.read().replace('\n', '')
    e = xml.etree.ElementTree.parse(inputFilename).getroot()
    it = xml.etree.ElementTree.iterparse(StringIO(xmlData))
    for _, el in it:
        if '}' in el.tag:
            el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
    root = it.root
    gpxPoints = _GetAllGpxPointsFromRootXml(root)
    return GpxCourse(gpxPoints)


def GenerateTcxSlopeWorkout(slopeCourse, outputName):
    '''Create a tcx file of name outputName.tcx (do not add the extension to the name)'''
    TrainingDbTag = E("TrainingCenterDatabase")
    TrainingDbTag.attrib["xmlns"] = "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
    output = TrainingDbTag
    Courses = E("Courses")
    Course = E("Course")
    CourseName = E("name", outputName)
    Track = E("Track")

    TrainingDbTag.append(Courses)
    Courses.append(Course)
    Course.append(CourseName)
    Course.append(Track)

    for slopePoint in slopeCourse.GetSlopePoints():
        TrackPoint = E("Trackpoint")
        Track.append(TrackPoint)
        TrackPoint.append(E("DistanceMeters", str(slopePoint.distance)))
        ExtensionsTag = E("Extensions")
        TrackPoint.append(ExtensionsTag)
        TPXTag = E("TPX")
        ExtensionsTag.append(TPXTag)
        TPXTag.append(E("Slope", str(slopePoint.slope)))

    outputXml = tostring(output, pretty_print=True)

    outputFilename = outputName + ".tcx"

    with open(outputFilename, "w+") as f:
        f.write('<?xml version="1.0"?>\n')
        f.write(outputXml)


def NextFigure(title = ""):
    plt.figure(NextFigure.currentFigure)
    NextFigure.currentFigure += 1
    plt.title(title)
NextFigure.currentFigure = 0


def PlotSlope(slopeCourse, maxDistance, title = "", style=""):
    NextFigure(title)
    plotDataSlope = []
    plotDataDistance = []
    for slopePoint in slopeCourse.GetSlopePoints():
        if slopePoint.distance > maxDistance and maxDistance > 0:
            break
        plotDataSlope.append(slopePoint.slope)
        plotDataDistance.append(slopePoint.distance)
    plt.plot(plotDataDistance, plotDataSlope, style)
    plt.show()


def PlotProfile(profile, maxDistance, title = "", style=""):
    NextFigure(title)
    plotDataElevation = []
    plotDataDistance = []
    for index in range(0, profile.GetNumberOfPoints() - 1):
        if profile[index].distance > maxDistance and maxDistance > 0:
            break
        plotDataElevation.append(profile[index].elevation)
        plotDataDistance.append(profile[index].distance)
    plt.ylabel("Elevation (meters)")
    plt.xlabel("Distance (meters)")
    startDistance = profile[0].distance
    totalDistance = profile.GetTotalDistance()
    highestElevation = profile.GetHighestElevation()
    lowestElevation = profile.GetLowestElevation()
    elevationGain = profile.GetElevationGain()
    textX = startDistance
    textY = highestElevation
    profileTextInfo = "Elevation Gain = " + str(int(elevationGain)) + "m\n"
    profileTextInfo += "Total Distance = " + str(int(totalDistance)) + "m\n"
    profileTextInfo += "Lowest Elevation = " + str(int(lowestElevation)) + "m\n"
    profileTextInfo += "Highest Elevation = " + str(int(highestElevation)) + "m"

    plt.text(textX, textY, profileTextInfo, multialignment="left",va="top", ha="left")

    plt.plot(plotDataDistance, plotDataElevation, style)
    plt.show()


def PlotGpx(gpxCourse, maxDistance, title = "", style=""):
    NextFigure(title)
    plotDataEle = []
    plotDataDistance = []
    totalDistance = 0
    plotDataEle.append(gpxCourse[0].elevation)
    plotDataDistance.append(0)
    for index in range(1, gpxCourse.GetNumberOfPoints() - 1):
        totalDistance += GetDistanceBetweenPoints(gpxCourse[index], gpxCourse[index-1])
        if totalDistance > maxDistance and maxDistance > 0:
            break
        plotDataEle.append(gpxCourse[index].elevation)
        plotDataDistance.append(totalDistance)
    plt.plot(plotDataDistance, plotDataEle, style)
    plt.show()



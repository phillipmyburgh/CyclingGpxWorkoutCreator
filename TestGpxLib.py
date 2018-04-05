# (c) 2018 Phillip Myburgh
# Distributed under the MIT Licence

import unittest

from GpxLib import *


class GpxCourseInfo:
    def __init__(self, filename, expectedDistance, expectedElevationGain):
        self.gpxCourse = ParseGpxFile(filename)
        self.expectedDistance = expectedDistance
        self.expectedElevationGain = expectedElevationGain


def CreateTestGpxCourse():
    gpxPoints = []
    # This is just the first few points of the 94.7 course
    # we have some duplicate points to make sure the code copes well with this
    gpxPoints.append(GpxPoint(-25.9598389, 28.022995591, 1372.899))
    gpxPoints.append(GpxPoint(-25.958237602, 28.022840023, 1375.028))
    gpxPoints.append(GpxPoint(-25.958237602, 28.022840023, 1375.028))
    gpxPoints.append(GpxPoint(-25.958230344, 28.022842467, 1375.098))
    gpxPoints.append(GpxPoint(-25.958230344, 28.022842467, 1375.098))
    gpxPoints.append(GpxPoint(-25.95613466, 28.023548126, 1392.439))
    gpxPoints.append(GpxPoint(-25.95613466, 28.023548126, 1392.439))
    return GpxCourse(gpxPoints)


# Most online apps give different values for the expected distance between points. I used the values
# from Garmin Connect and http://www.trackreport.net which seem to be the most correct because they use the correct
# radius of earth in their calculation.
# We can nit pick and realise that the elevation differences between the points are far greater than the
# differences between the estimations of the earth's radius.
# Most of the values have just been taken exactly the way the GpxLib calculates them. I'm not using the
# unit tests to validate my formula. I am mostly using this to do regression testing.
class TestGpxLib(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Get the test case data from the 94.7 Race
        # This course was plotted using Garmin Connect, and this is the expected distance
        # The elevation gain wasn't the Garmin Connect value because I suspect they do a bit of filtering
        # which makes the number a bit lower.
        cls.courseInfo1 = GpxCourseInfo("./TestData/94.7Race.gpx", 93.94e3, 1434)


    def test_DegToRad(self):
        self.assertAlmostEqual(DegreesToRadians(65), 1.13446, 3)


    def test_RadToDeg(self):
        self.assertAlmostEqual(RadiansToDegrees(2), 114.592, 3)


    def test_Haversine(self):
        # Note, this radius of earth differs from what is used in the lib under test. The radius in the lib
        # seems to be the more accurate version
        radiusOfEarth = 6371.0 * 1000.0
        self.assertAlmostEqual(Haversine(36.12, -86.67,  33.94, -118.40, radiusOfEarth), 2886444.4428, 3)
        self.assertAlmostEqual(Haversine(38.898556, -77.037852, 38.897147, -77.043934, radiusOfEarth), 549.15579, 3)


    def test_ConvertGpxPointsToPolyLineEncoding(self):
        # We are using the test case from https://developers.google.com/maps/documentation/utilities/polylinealgorithm
        gpxPoints = [GpxPoint(38.5, -120.2, 0), GpxPoint(40.7, -120.95, 0), GpxPoint(43.252, -126.453, 0)]
        expectedString = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
        actualString = ConvertGpxPointsToPolyLineEncoding(gpxPoints)
        self.assertEquals(expectedString, actualString)

        # And another section that gave me issues (because some point diffs were 0), where I used validated using:
        # https://google-developers.appspot.com/maps/documentation/utilities/polyline-utility/polylineutility
        gpxPoints = [GpxPoint(-25.9871650022, 28.0767660867, 0),
                     GpxPoint(-25.9872958437, 28.0767756421, 0),
                     GpxPoint(-25.9880580101, 28.0768343993, 0),
                     GpxPoint(-25.9889261238, 28.0768310465, 0),
                     GpxPoint(-25.9897983447, 28.0767186452, 0)]
        expectedString = "xrr}CyvjjDXAvCIlD?lDT"
        actualString = ConvertGpxPointsToPolyLineEncoding(gpxPoints)
        self.assertEquals(expectedString, actualString)


    def test_GetDistanceBetweenPoints(self):
        self.assertAlmostEqual(GetDistanceBetweenPoints(GpxPoint(36.12, -86.67, 0), GpxPoint(33.94, -118.40, 0)), 2889661.1679, 3)
        self.assertAlmostEqual(GetDistanceBetweenPoints(GpxPoint(38.898556, -77.037852, 0), GpxPoint(38.897147, -77.043934, 0)), 549.7677, 3)


    def test_GetMiddlePoint(self):
        startPoint = GpxPoint(45.678, 5.4321, 0)
        endPoint = GpxPoint(46.810, 5.1015, 1000)
        middlePoint = GetMiddlePoint(startPoint, endPoint)
        self.assertAlmostEqual(middlePoint.latitude, 46.244119, 3)
        self.assertAlmostEqual(middlePoint.longitude, 5.268505, 3)
        self.assertAlmostEqual(middlePoint.elevation, 500.0, 3)


    def test_InterpolateBetweenPoints(self):
        #TODO: I still need a nice test for this function
        self.assertTrue(True)


    def test_GetDistanceAtIndex(self):
        # Check the distance at start, and second index
        self.assertEqual(self.courseInfo1.gpxCourse.GetDistanceAtIndex(0), 0)
        self.assertAlmostEqual(self.courseInfo1.gpxCourse.GetDistanceAtIndex(1), 178.9333, 3)


    def test_CourseGetTotalDistance(self):
        totalDistance = self.courseInfo1.gpxCourse.GetTotalDistance()
        # Here we just want to be within 10m of Garmin Connect
        self.assertAlmostEqual(totalDistance, self.courseInfo1.expectedDistance, delta=10)


    def test_CourseGetElevationAtDistance(self):
        # Check the elevation at start
        self.assertEqual(self.courseInfo1.gpxCourse.GetElevationAtDistance(0), 1372.899)
        self.assertAlmostEqual(self.courseInfo1.gpxCourse.GetElevationAtDistance(5000), 1518.2241, 3)



    def test_CourseRemoveAllDuplicateGpxPoints(self):
        # Simple test. We would want the total distance to be the same, and the distance between any points should
        # not be zero
        newGpxPoints = self.courseInfo1.gpxCourse.RemoveAllDuplicateGpxPoints()
        totalDistance = self.courseInfo1.gpxCourse.GetTotalDistance()
        self.assertAlmostEqual(totalDistance, self.courseInfo1.expectedDistance, delta=10)

        for index in range(1, newGpxPoints.GetNumberOfPoints() - 1):
            distance = GetDistanceBetweenPoints(newGpxPoints[index], newGpxPoints[index - 1])
            self.assertGreater(distance, 0)


    def test_CoursePruneDistance(self):
        # Shorten the distance to max 5000m and assert that it is actually less than 5000
        newGpxCourse = self.courseInfo1.gpxCourse.PruneDistance(5000)
        self.assertLessEqual(newGpxCourse.GetTotalDistance(), 5000)
        self.assertGreater(newGpxCourse.GetTotalDistance(), 0)


    def test_CourseCreateProfile(self):
        profile = self.courseInfo1.gpxCourse.CreateProfile()

        # The total distance should still be the same as the gpxPoint array, which is also the real distance
        self.assertAlmostEqual(profile.GetTotalDistance(), self.courseInfo1.expectedDistance, delta=10)



    def test_ProfileGetElevationGain(self):
        profile = self.courseInfo1.gpxCourse.CreateProfile()
        elevationGain = profile.GetElevationGain()
        self.assertAlmostEqual(elevationGain, self.courseInfo1.expectedElevationGain, delta=1)


    def test_ProfileGetElevationAtDistance(self):
        profile = self.courseInfo1.gpxCourse.CreateProfile()
        self.assertEqual(profile.GetElevationAtDistance(0), 1372.899)
        self.assertAlmostEqual(profile.GetElevationAtDistance(5000), 1518.2241, 3)


    def test_ProfileGetAverageDistanceBetweenPoints(self):
        # Test both the profile with duplicates and the equidistant profile
        profileCourse = self.courseInfo1.gpxCourse.CreateProfile()
        equidistantProfileCourse = self.courseInfo1.gpxCourse.CreateEquidistantProfile(10)
        self.assertAlmostEqual(profileCourse.GetAverageDistanceBetweenPoints(), 89.2109, 3)
        self.assertAlmostEqual(equidistantProfileCourse.GetAverageDistanceBetweenPoints(), 10, 1)


    def test_CreateEquidistantProfile(self):
        # create a profile with distance gaps of 10m
        gap = 10
        profilePoints = self.courseInfo1.gpxCourse.CreateEquidistantProfile(gap)

        # The total distance should still be the same as the gpxPoint array, which is also the real distance
        self.assertAlmostEqual(profilePoints.GetTotalDistance(), self.courseInfo1.expectedDistance, delta=10)


    def test_ProfileGetSlopeCourse(self):
        slopeCourse = CreateTestGpxCourse().CreateProfile().CreateSlopeCourse()
        # TODO: Add a test for this....


    def test_SlopeGetAverageDistanceBetweenPoints(self):
        # Test both the profile with duplicates and the equidistant profile
        slopeCourse = self.courseInfo1.gpxCourse.CreateProfile().CreateSlopeCourse()
        equidistanceSlopeCourse = self.courseInfo1.gpxCourse.CreateEquidistantProfile(10).CreateSlopeCourse()
        # TODO: See why this is different than the test_ProfileGetAverageDistanceBetweenPoints
        #self.assertAlmostEqual(slopeCourse.GetAverageDistanceBetweenPoints(), 89.2109, 3)
        #self.assertAlmostEqual(equidistanceSlopeCourse.GetAverageDistanceBetweenPoints(), 10, 1)


if __name__ == '__main__':
    unittest.main()
# Screen detector
This code handles detecting a screen in a feed from a pair of gaze-tracking glasses, and then maps the gaze of the user within this image to a normalised value corresponding to the persons gaze position on the screen. If the user is n:ot looking at the screen the value returned by the screen transformation will be outside of this range. This makes it easy for us to check if the user is looking at the screen.

TODO: Need to create mermaid graph of inputs and outputs of this function here!

## Longer explanation:
In our robotic system, a user will be wearing some gaze-tracking glasses. The glasses have two outputs (that we care about): the outward facing camera feed captured by the glasses, and the users current gaze position on that feed. We want to map the raw gaze position of the user within the camera feed to the point on the screen that the user is staring at.

To do this, we put four aruco tags on the corner of the screen. Once we have detected the locations of these four aruco tags, we can use cv2.getPerspectiveTransform to create a transform matrix between the position of the screen in the image and the content that is displayed on the screen.

Effectively this operation is the inverse of placing an image in 3D space using a
perspective transform.

## Assumptions: 
- Camera distortions have been accounted for/Not significant.
- All four corner ARUCO's have been detected in the image (might be able to relax this
one in future updates!)
- 


## current issues:
1. **Screen capture can crash image detection:** Our screen detection can crash when multiple instances of the same aruco are seen by the image.
**STEPS TO FIX:** Need to figure out what type we are actually grabbing in line 98 of src/ScreenDetector.
2. **Brittle ARUCO detection:** Aruco detection seems to be extremely noise and motion sensitive, with ARUCO tag detection dropping if screen moves or if aruco tag is at an angle. 
**Fixes:**
Quick and easy fix: See how converting image into a greyscale image affects ARUCO detection rates.
Slightly more involved fix: read into how ARUCOs might be detected in moving frames.
More detailed fix: Might have to do accelerometer based velocity model localisation (avoid if at all possible, although this would increase reliability of screen localisation with non-detected ARUCOS!).

## TODOs:
1. Implement "is_user_looking_at_screen" function that takes in an image and a
location and returns a bool and a location of gaze centre (this wont be used
for our experiment but will be cool!.) 
2. find out how to turn this into a ROS2 package.

## Tests:
1. **Screen Gaze Detection Test:** This function essentially acts as a button,
with a mode on the robot toggling when someone is actively looking at the
screen. We want to make sure that this system toggles on and off effectively.

**Test Plan:** Create stationary point, move camera around, change screen
colour if point is over screen. See how this implementation reacts to rapid
head movement, edge-of-screen detections and other factors.

**TOBI Glasses test** Need to test ability of software to work with outward facing TOBI camera. To test this we can check for detection failiures with head movement, where the screen is moving in the frame, and check that screen is almost always visible during normal operation.

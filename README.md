# appdaemon_apps_public
App Daemon Apps

# App Daemon room_control.py
This class controls room lighting and room fans based on presence detection binary sensors.  It can call any number of scenes based on either on/off or modes throughout the day, or modes based on brightness.  The class doesnt care to figure out things like how bright it is or what time of day, but it follows a simple text sensor to tell it which scene to call.

If can handle on/off fans, or fans with speed

This is still a work in progress and requires some additional elements to be added to Home Assistant

Use at your own risk
import hassapi as hass


#
# App to control a room major functions
#
# 
#
# Args:
#
# debug: str, default to off, use true if deugging
# trigger_binary_sensor: list, List of binary sensors to listen to for "on" events to trigger room
# fan: str, Fan entity to control with the room
# fan_on_threshold: str, input_number The min temp to turn the fan on defaults to 60
# fan_medium_threshold: str, input_number The temp that if above fan turns on medium defaults to 70
# fan_high_threshold: str, input_number the temp that if above the fan turns on high defaults to 80
# temperature_sensor: str, Sensor entity to use for the room temperature
# mode: str, entity to use for sensing modes
# occupied: str, switch to use for room occupancy
# sleep: str, state entity to use to trigger sleep mode
# scene_prefix: str, the text name that prefixes mode names in the scene names, such as "living_room_night" would be "living_room_" 
# there should be matching scenes for each mode, if you dont specify a mode it defaults to <scene_prefix>_on and off
# special_scene_boolean: str, an entity that if on will always trigger a special scene for the room no matter what the scene will be on
# special_scene_name: str, the name of the special scene
# wake_scene: str, the name of the scene to be called when sleep is turning off, this is used in conjunction with sleep_transition to slowly bring up the lights when waking up
# ha_uptime_sensor: int, minutes sensor that HASS has been up.  this gets around issues where the api is available but components are not
# delay: amount of time after turning on to turn off again. If not specified defaults to 60 seconds.
# transitions are in seconds, edit the defaults below if you dont want to specify for each room
# 

class room_control(hass.Hass):
    def initialize(self):

        self.off_handle = None
        self.transition_handle = None

        self.uptime_threshold_minutes = 5
        default_on_transition = 1
        default_off_transition = 30
        default_mode_transition = 60
        default_sleep_transition = 200
        default_delay = 60

        #setvars and defaults
        if "debug" in self.args:
            self.debug = self.args["debug"]
        else:
            self.debug = False  

        if self.debug:
            self.log("Debugging enabled")

        if "delay" in self.args:
            self.delay = self.args["delay"]
        else:
            self.delay = default_delay

        if "on_transition" in self.args:
            self.on_transition = self.args["on_transition"]
        else:
            self.on_transition = default_on_transition

        if "off_transition" in self.args:
            self.off_transition = self.args["off_transition"]
        else:
            self.off_transition = default_off_transition

        if "mode_transition" in self.args:
            self.mode_transition = self.args["mode_transition"]
        else:
            self.mode_transition = default_mode_transition

        if "sleep_transition" in self.args:
            self.sleep_transition = self.args["sleep_transition"]
        else:
            self.sleep_transition = default_sleep_transition

        if "ha_uptime_sensor" in self.args:
            self.ha_uptime_sensor = self.args["ha_uptime_sensor"]
        else:
            self.ha_uptime_sensor = "sensor.hass_rooms_uptime"

        if "fan" in self.args:
            self.fan = self.args["fan"]
        else:
            self.fan = False

        if "fan_on_threshold" in self.args:
            self.fan_on_threshold = self.args["fan_on_threshold"]
        else:
            self.fan_on_threshold = False

        if "fan_medium_threshold" in self.args:
            self.fan_medium_threshold = self.args["fan_medium_threshold"]
        else:
            self.fan_medium_threshold = False

        if "fan_high_threshold" in self.args:
            self.fan_high_threshold = self.args["fan_high_threshold"]
        else:
            self.fan_high_threshold = False

        if "temperature_sensor" in self.args:
            self.temperature_sensor = self.args["temperature_sensor"]
        else:
            self.temperature_sensor = None 

        if "mode" in self.args:
            self.mode = self.args["mode"]
        else:
            self.mode = False

        if "manual" in self.args:
            self.manual = self.args["manual"]
        else:
            self.manual = False

        if "occupied" in self.args:
            self.occupied = self.args["occupied"]
        else:
            self.log("ERROR: Occupancy switch not entered, but required")
        
        if "sleep" in self.args:
            self.sleep = self.args["sleep"]
        else:
            self.sleep = False

        if "scene_prefix" in self.args:
            self.scene_prefix = self.args["scene_prefix"]
        else:
            self.log("ERROR: scene_prefix required")

        if "special_scene_boolean" in self.args:
            self.special_scene_boolean = self.args["special_scene_boolean"]
        else:
            self.special_scene_boolean = False

        if "special_scene_name" in self.args:
            self.special_scene_name = self.args["special_scene_name"]
        else:
            self.special_scene_name = False

        if "wake_scene" in self.args:
            self.wake_scene = self.args["wake_scene"]
        else:
            self.wake_scene = False


        # Subscribe to sensors
        if "trigger_binary_sensor" in self.args:
            if type(self.args["trigger_binary_sensor"]) is list:
                for trigger_binary_sensor in self.args["trigger_binary_sensor"]:
                    self.listen_state(self.room_on_motion, trigger_binary_sensor)
                    self.log("Subscribing to trigger_binary_sensor: {} ".format(trigger_binary_sensor))
            else:
                self.listen_state(self.room_on_motion, self.args["trigger_binary_sensor"])
                self.log("Subscribing to trigger_binary_sensor: {} ".format(self.args["trigger_binary_sensor"]))
        else:   
            self.log("No sensor specified, doing nothing")

        if self.mode:
            self.listen_state(self.room_on_state, self.mode)
            self.log("Subscribing to mode: {}".format(self.mode))

        if self.temperature_sensor:
            self.listen_state(self.fan_on, self.temperature_sensor)
            self.log("Subscribing to temperature_sensor: {}".format(self.temperature_sensor))

        if self.fan_on_threshold:
            self.listen_state(self.fan_on, self.fan_on_threshold)
            self.log("Subscribing to fan_on_threshold: {}".format(self.fan_on_threshold))

        if self.fan_medium_threshold:
            self.listen_state(self.fan_on, self.fan_medium_threshold)
            self.log("Subscribing to fan_medium_threshold: {}".format(self.fan_medium_threshold))

        if self.fan_high_threshold:
            self.listen_state(self.fan_on, self.fan_high_threshold)
            self.log("Subscribing to fan_high_threshold: {}".format(self.fan_high_threshold))

        if self.sleep:
            self.listen_state(self.room_on_state, self.sleep)
            self.log("Subscribing to sleep: {} ".format(self.sleep))

        if self.special_scene_boolean:
            self.listen_state(self.room_on_state, self.special_scene_boolean)
            self.log("Subscribing to special_scene_boolean: {}".format(self.special_scene_boolean))

    def room_on_motion(self, entity, attribute, old, new, kwargs):
        if self.debug:
            self.log("room_on_motion Triggered by: {}".format(entity))

        if not self.blocked():
            if new == "on":
                if self.get_state(self.occupied) == "off":
                        self.lights_on(self.on_transition, False, False) #use transition when entering a room
                else:
                    self.lights_on(self.on_transition, False, False) #hope to remove, but continually try to turn the lights on in case one was missed
                    #turn on lights with transition time, not turning on from sleep
                self.turn_on(self.occupied)
                self.fan_on(self.fan, "state", "off", "on", "anone")
        else:
            if self.debug:
                self.log("room_on_motion Blocked")
        self.cancel_timer(self.off_handle)
        self.off_handle = self.run_in(self.room_off, self.delay)
        #always restart timer

    def room_on_state(self, entity, attribute, old, new, kwargs):
        if self.debug:
            self.log("room_on_state Triggered by: {}".format(entity))

        if not self.blocked():
            if entity == self.mode:
                if self.get_state(self.occupied) == "on":
                    self.lights_on(self.mode_transition, False, False)
                    if self.debug:
                        self.log("room_on_state Changing Mode")
            if entity == self.special_scene_boolean:
                self.lights_on(self.on_transition, False, False)
                if self.debug:
                    self.log("room_on_state Special")
            if entity == self.sleep:
                if new == "off":
                    self.lights_on(self.sleep_transition, True, True)
                    if self.debug:
                        self.log("room_on_state Sleep Off")
                else:
                    self.lights_on(self.off_transition, True, False)
                    if self.debug:
                        self.log("room_on_state Sleep On")




    def room_off(self, kwargs):

        we_are_blocked = False

        if self.blocked():
            we_are_blocked = True

        if "stay_on_if_on" in self.args:
            if type(self.args["stay_on_if_on"]) is list:
                for stay_on_if_on_check in self.args["stay_on_if_on"]:
                    if self.get_state(stay_on_if_on_check) == "on":   
                        we_are_blocked = True
                        if self.debug:
                            self.log("room_off Blocked by {}".format(stay_on_if_on_check))
                        break
            else: 
                if self.get_state(self.args["stay_on_if_on"]) == "on":
                    if self.debug:
                        self.log("room_off Blocked by {}".format(self.args["stay_on_if_on"]))
                    we_are_blocked = True

        if self.special_scene_boolean:
            if self.get_state(self.special_scene_boolean) == "on":
                if self.debug:
                        self.log("room_off Blocked by {}".format(self.special_scene_boolean))
                we_are_blocked = True

        if self.sleep:
            if self.get_state(self.sleep) == "on":
                if self.debug:
                        self.log("room_off Blocked by {}".format(self.sleep))
                we_are_blocked = True

        if we_are_blocked:
            self.cancel_timer(self.off_handle)
            self.off_handle = self.run_in(self.room_off, self.delay)  
            if self.debug:
                self.log("Ignoring room_off because we are blocked")               
        else:
            self.turn_off(self.occupied)
            self.fan_off()
            self.lights_off()
            
    def lights_on(self, transition_length, transition_with_manual, from_sleep):
        if from_sleep:
            self.call_service("scene/turn_on", entity_id = self.wake_scene, transition = transition_length)
            self.turn_on(self.manual)
            self.cancel_timer(self.transition_handle)
            self.transition_handle = self.run_in(self.turn_off_manual, transition_length)  
            if self.debug:
                self.log("Turning wake scene on with transition: {}".format(transition_length))
        else:
            scene_name = self.determine_scene("on")
            if self.debug:
                self.log("Turning {} on".format(scene_name))

            if transition_with_manual:
                if self.debug:
                    self.log("Transitioning for {}".format(transition_length))

                self.call_service("scene/turn_on", entity_id = scene_name, transition = transition_length)
                if self.debug:
                    self.log("Turning on scene: {}".format(scene_name))
                self.turn_on(self.manual)
                self.cancel_timer(self.transition_handle)
                self.transition_handle = self.run_in(self.turn_off_manual, transition_length)  
            else:
                if self.debug:
                    self.log("Not Transitioning")
                self.call_service("scene/turn_on", entity_id = scene_name, transition = transition_length)
                if self.debug:
                    self.log("Turning on scene: {}".format(scene_name))

    def lights_off(self):
        scene_name = self.determine_scene("off")
     
        if self.debug:
            self.log("Turning {} on".format(scene_name))
        self.call_service("scene/turn_on", entity_id = scene_name, transition = self.off_transition)


    def fan_on(self, entity, attribute, old, new, kwargs):
        fan_type = "unk"
        if self.fan:
            if "switch." in self.fan:
                fan_type = "switch"
            else:
                fan_type = "fan"
        else:
            return
        if self.get_state(self.occupied) == "on":
            if fan_type == "switch":
                if float(self.get_state(self.temperature_sensor)) > float(self.get_state(self.fan_on_threshold)):
                    if self.debug:
                        self.log("Turning on fan {}".format(self.fan))
                    self.turn_on(self.fan)
                else:
                    if self.debug:
                        self.log("Turning off fan {} because room occupied but below threshold".format(self.fan))
                    self.fan_off()
            
            if fan_type == "fan":
                if float(self.get_state(self.temperature_sensor)) > float(self.get_state(self.fan_on_threshold)):
                    if float(self.get_state(self.temperature_sensor)) < float(self.get_state(self.fan_medium_threshold)):
                        if self.debug:
                            self.log("Setting fan {} to low".format(self.fan))
                        self.turn_on(self.fan, speed = "low")
                    if float(self.get_state(self.temperature_sensor)) > float(self.get_state(self.fan_medium_threshold)) and float(self.get_state(self.temperature_sensor)) < float(self.get_state(self.fan_high_threshold)):
                        if self.debug:
                            self.log("Setting fan {} to medium".format(self.fan))
                        self.turn_on(self.fan, speed = "medium")
                    if float(self.get_state(self.temperature_sensor)) > float(self.get_state(self.fan_high_threshold)):
                        if self.debug:
                            self.log("Setting fan {} to high".format(self.fan))
                        self.turn_on(self.fan, speed = "high")
                else:
                    if self.debug:
                        self.log("Turning off fan {} because room occupied but below threshold".format(self.fan))
                    self.fan_off()
   
        

    def fan_off(self):
        if self.fan:
            if self.debug:
                self.log("Turning off fan {}".format(self.fan))
            self.turn_off(self.fan)


    def determine_scene(self, turning):
        scene = "unk"

        if self.special_scene_boolean:
            if self.get_state(self.special_scene_boolean) == "on":
                scene = self.special_scene_name
            else:
                if self.mode:
                    if turning == "on":
                        if self.sleep:
                            if self.get_state(self.sleep) == "on":
                                scene = self.scene_prefix + "sleep"
                            else:
                                scene = self.scene_prefix + self.get_state(self.mode)
                        else:
                            scene = self.scene_prefix + self.get_state(self.mode)
                    else: #turning off
                        if self.get_state(self.mode) == "evening" or self.get_state(self.mode) == "night" or self.get_state(self.mode) == "morning":
                            scene = self.scene_prefix + "dark"
                        else:
                            scene = self.scene_prefix + "off"
                else:
                    if turning == "on":
                        scene = self.scene_prefix + "on"
                    else:
                        scene = self.scene_prefix + "off"      
        else: 
            if self.mode:
                if turning == "on":
                    if self.sleep:
                        if self.get_state(self.sleep) == "on":
                            scene = self.scene_prefix + "sleep"
                        else:
                            scene = self.scene_prefix + self.get_state(self.mode)
                    else:
                        scene = self.scene_prefix + self.get_state(self.mode)
                else: #turning off
                    if self.get_state(self.mode) == "evening" or self.get_state(self.mode) == "night" or self.get_state(self.mode) == "morning":
                        scene = self.scene_prefix + "dark"
                    else:
                        scene = self.scene_prefix + "off"
            else:
                if turning == "on":
                    scene = self.scene_prefix + "on"
                else:
                    scene = self.scene_prefix + "off"


        if scene == "unk":
            self.log("WARN: unable to resolve scene")
        return scene


    def turn_off_manual(self, kwargs):
        self.turn_off(self.manual)
        if self.debug:
            self.log("Turning Off Manual")

    def blocked(self):
        if float(self.get_state(self.ha_uptime_sensor)) > self.uptime_threshold_minutes:
            if self.manual:
                if self.get_state(self.manual) == "off":
                    blocked = False
                else:
                    blocked = True
                    if self.debug:
                        self.log("Blocked by: manual")        
            else:
                blocked = False
        else:
            blocked = True
            if self.debug:
                self.log("Blocked by: uptime_threshold")
        return blocked

    def cancel(self):
        self.cancel_timer(self.off_handle)
        self.cancel_timer(self.transition_handle)
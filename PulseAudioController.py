#!/usr/bin/env python3
import os
import sys
import subprocess
from MouseDaemon import MouseEventResponder, MouseDaemon
from Led import Led

mouse_file = "/dev/input/mice"
response_led_file = "/sys/class/leds/status:red:fault/trigger"
switch_user = True
max_vol = 100
min_vol = 35
sink = 0
user_name = "pulse"
group_name = "pulse"

class PulseAudioMouseEventResponder(MouseEventResponder):
    def __init__(self, sink, max_vol, min_vol, led):
        self.sink = sink
        self.max_vol = max_vol
        self.min_vol = min_vol
        self.led = led
    
    def pulseaudio_set_volume(self, vol):
        vol = str(vol).split("%")[0] #remove % sign if present
        if vol[0] in ["+", "-"]: #delta volume specified
            current_volume = self.pulseaudio_get_volume()
            new_volume = current_volume + int(vol)
            if new_volume < self.min_vol:
                self.pulseaudio_write_volume(str(self.min_vol))
            elif new_volume > self.max_vol:
                self.pulseaudio_write_volume(str(self.max_vol))
            else:
                self.pulseaudio_write_volume(vol)
        else:
            if int(vol) >= self.min_vol and int(vol) <= self.max_vol:
                self.pulseaudio_write_volume(vol)
    
    def pulseaudio_write_volume(self, vol):
        #do not call this directly!
        subprocess.call(["pactl", "--", "set-sink-volume", str(self.sink), str(vol) + "%"], stderr=subprocess.DEVNULL)
    
    def pulseaudio_toggle_mute(self):
        subprocess.call(["pactl", "set-sink-mute", str(self.sink), "toggle"], stderr=subprocess.DEVNULL)
        self.led.set_value(self.pulseaudio_get_muted())
   
    def pulseaudio_get_volume(self):
        try:
            sinkinfo = subprocess.Popen(["pactl", "list", "sinks"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).communicate()[0]
            volumes = subprocess.Popen(["grep", "Volume: 0:"], stdout=subprocess.PIPE, stdin=subprocess.PIPE).communicate(input=sinkinfo)[0].split(b"\n")
            volume = volumes[self.sink][9:]
            #volume will be something like b' 12'
            volume = volume[2:].split(b'%')[0]
            
            return int(volume)
        except Exception as e:
            #Fallback if something went terribly wrong
            print("pulseaudio_get_volume failed:", e, file=sys.stderr)
            return int((max_vol + min_vol) / 2)
        
    def pulseaudio_get_muted(self):
        try:
            sinkinfo = subprocess.Popen(["pactl", "list", "sinks"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).communicate()[0]
            muteinfo = subprocess.Popen(["grep", "Mute:"], stdout=subprocess.PIPE, stdin=subprocess.PIPE).communicate(input=sinkinfo)[0].split(b"\n")
            muted = b"yes" in muteinfo[self.sink]
            
            return muted
        except Exception as e:
            print("pulseaudio_get_muted failed:", e, file=sys.stderr)
            return False
    
    def respond(self, button):
        """ Decides what to do on mouse button/wheel events """
        
        led_value = self.led.get_value()
        self.led.set_value(not led_value)
        keep_led = False
        
        if (button == 0):   #button 1 (left)
            self.pulseaudio_set_volume("-10")
        elif (button == 1): #button 2 (right)
            self.pulseaudio_set_volume("+10")
        elif (button == 2): #button 3 (middle)
            self.pulseaudio_toggle_mute()
            keep_led = True
        elif (button == 3): #button 4
            self.pulseaudio_set_volume(str(self.min_vol))
        elif (button == 4): #button 5
            self.pulseaudio_set_volume(str(self.max_vol))
        elif (button == 5): #mouse wheel down
            self.pulseaudio_set_volume("-5")
        elif (button == 6): #mouse wheel up
            self.pulseaudio_set_volume("+5")
        else:
            print("Invalid event number", button, file=sys.stderr)
        
        if not keep_led:
            self.led.set_value(led_value)

if __name__ == '__main__':
    try:
        #get file descriptor to led file before possible privilege drop
        led = None
        if response_led_file != "":
            try:
                led = Led(os.open(response_led_file, os.O_WRONLY))
            except:
                raise OSError("Response led file could not be opened")
            led.set_value(False)
            print("Response led file opened")
        else:
            print("No response led file given, feature disabled")
        
        daemon = MouseDaemon(mouse_file=mouse_file, switch_user=switch_user, user=user_name, group=group_name)
        
        responder = PulseAudioMouseEventResponder(sink, max_vol, min_vol, led)
        daemon.handleEvents(responder)
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)

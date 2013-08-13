#!/usr/bin/env python3
import sys
import subprocess
from MouseDaemon import MouseEventResponder, MouseDaemon

mouse_file = "/dev/input/mice"
switch_user = True
user_name = "pulse"
group_name = "pulse"

class PulseAudioMouseEventResponder(MouseEventResponder):
    def pulseaudio_set_volume(self, vol):
        subprocess.call(["pactl", "--", "set-sink-volume", "0", vol], stderr=subprocess.DEVNULL)
    
    def pulseaudio_toggle_mute(self):
        subprocess.call(["pactl", "set-sink-mute", "0", "toggle"], stderr=subprocess.DEVNULL)
    
    def respond(self, button):
        """ Decides what to do on mouse button/wheel events """
        if (button == 0):   #button 1 (left)
            self.pulseaudio_set_volume("-10%")
        elif (button == 1): #button 2 (right)
            self.pulseaudio_set_volume("+10%")
        elif (button == 2): #button 3 (middle)
            self.pulseaudio_toggle_mute()
        elif (button == 3): #button 4
            print("Button 4 received. Nothing to do.")
        elif (button == 4): #button 5
            print("Button 5 received. Nothing to do.")
        elif (button == 5): #mouse wheel down
            self.pulseaudio_set_volume("-5%")
        elif (button == 6): #mouse wheel up
            self.pulseaudio_set_volume("+5%")
        else:
            print("Invalid event number", button, file=sys.stderr)

if __name__ == '__main__':
    try:
        daemon = MouseDaemon(mouse_file=mouse_file, switch_user=switch_user, user=user_name, group=group_name)
        daemon.handleEvents(PulseAudioMouseEventResponder())
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)
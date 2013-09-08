import os
import time

class Led:
    def __init__(self, descriptor):
        self.led = descriptor
        self.state = b"none"
    
    def blink(self):
        if self.led is None:
            return
        
        state = self.state == b"default-on"
        self.set_value(not state)
        time.sleep(1/50)
        self.set_value(state)
    
    def set_value(self, value):
        if self.led is None:
            return
        state = b"default-on" if value else b"none"
        
        os.write(self.led, state)
        self.state = state
    
    def get_value(self):
        if self.led is None:
            return False
        return self.state == b"default-on"
    
    def toggle(self):
        if self.led is None:
            return
        
        state = self.state == b"default-on"
        self.set_value(not state)

    def __del__(self):
        if self.led is not None:
            os.close(self.led)
            print("Led file closed")
            
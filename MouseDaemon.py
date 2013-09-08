import os
import sys
from Mouse import MouseData, Mouse, MouseException
from UnixHelper import drop_privileges

class MouseEventResponder:
    def respond(self, event):
        raise NotImplementedError()

class MouseDaemon:
    def __init__(self, mouse_file="/dev/input/mice", switch_user=False, user="nobody", group="nogroup"):
        try:
            self.mouse_file = os.open(mouse_file, os.O_RDWR)
        except:
            raise OSError("Mouse file could not be opened")
        print("Mouse device opened")
        
        if switch_user:
            if drop_privileges(user, group):
                print("Privileges dropped")
            else:
                raise OSError("Privilege dropping failed")
        else:
            print("Privilege dropping is disabled")
        
        self.mouse = Mouse(self.mouse_file)
        
        if self.mouse.protocol == Mouse.INTELLI_MOUSE:
            mode = "IntelliMouse"
        elif self.mouse.protocol == Mouse.EXPLORER_MOUSE:
            mode = "Explorer Mouse"
        else:
            mode = "default"
        
        print("Found mouse in {} mode".format(mode))
        
        if self.mouse.protocol == Mouse.DEFAULT_MOUSE:
            #try switching to IntelliMouse protocol
            if self.mouse.setProtocol(Mouse.INTELLI_MOUSE):
                print("Mouse switched to IntelliMouse protocol")
                print("Mouse wheel support enabled")
            else:
                print("Mouse could not be switched to IntelliMouse protocol")
                print("Mouse wheel support disabled")
                print("Buttons 4 and 5 disabled")
        
        if self.mouse.protocol == Mouse.INTELLI_MOUSE:
            #try switching to Explorer Mouse protocol
            if self.mouse.setProtocol(Mouse.EXPLORER_MOUSE):
                print("Mouse switched to Explorer Mouse protocol")
                print("Buttons 4 and 5 enabled")
            else:
                print("Mouse could not be switched to Explorer Mouse protocol")
                print("Buttons 4 and 5 disabled")
        
    def handleEvents(self, event_responder):
        """ Main loop, catches events and sends them to given event_responder """
        
        #Each button's state is locked from firing events until it is released again.
        btn1 = btn2 = btn3 = btn4 = btn5 = False
        
        #track x and y movement. This will have to be queried manually
        self.x = self.y = 0
        
        while True:
            try:
                data = self.mouse.getMouseState()
            
                #fire only one event at a time
                if   (data.btn1 and data.btn1 != btn1):
                    event_responder.respond(0)
                elif (data.btn2 and data.btn2 != btn2):
                    event_responder.respond(1)
                elif (data.btn3 and data.btn3 != btn3):
                    event_responder.respond(2)
                elif (data.btn4 and data.btn4 != btn4):
                    event_responder.respond(3)
                elif (data.btn5 and data.btn5 != btn5):
                    event_responder.respond(4)
                elif data.wheel > 0:
                    event_responder.respond(5)
                elif data.wheel < 0:
                    event_responder.respond(6)
                
                #print(data)
                
                #current implementation: don't register move when overflow bit set
                if not data.xovfl:
                    self.x += data.x
                if not data.yovfl:
                    self.y += data.y
                
                #save data for next run
                btn1, btn2, btn3, btn4, btn5 = data.btn1, data.btn2, data.btn3, data.btn4, data.btn5
            except MouseException:
                continue #ignore invalid data received from mouse
    
    def __del__(self):
        os.close(self.mouse_file)
        print("Mouse device closed")

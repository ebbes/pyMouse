import collections
import os

MouseData = collections.namedtuple("MouseData", "x, y, xovfl, yovfl, btn1, btn2, btn3, btn4, btn5, wheel")

class MouseException(Exception):
    pass

class Mouse:
    COMMAND_IMPS2 = b'\xf3\xc8\xf3d\xf3P'
    COMMAND_IMEX  = b'\xf3\xc8\xf3\xc8\xf3P'
    
    COMMAND_READ_MOUSE_ID = b'\xf2'
    COMMAND_STREAM_MODE = b'\xea'
    
    DEFAULT_MOUSE = 0
    INTELLI_MOUSE = 3
    EXPLORER_MOUSE = 4
    
    MOUSE_ACK = 0xfa
    
    def __init__(self, descriptor):
        self.mouse = descriptor
        
        if not self._setStreamMode():
            raise MouseException("Failed to set mouse to stream mode.")
        
        self.protocol = self.getProtocol()
    
    def _sendSimpleCommand(self, command):
        if os.write(self.mouse, command) != len(command):
            return False
        buf = os.read(self.mouse, 1)
        return len(buf) == 1 and buf[0] == self.MOUSE_ACK
    
    def getProtocol(self):
        """ Returns ID of currently used mouse protocol """
        if os.write(self.mouse, self.COMMAND_READ_MOUSE_ID) != len(self.COMMAND_READ_MOUSE_ID):
            return self.DEFAULT_MOUSE
        buf = os.read(self.mouse, 2)
        if len(buf) == 2 and buf[0] == self.MOUSE_ACK:
            self.protocol = buf[1]
        else:
            self.protocol = self.DEFAULT_MOUSE
        return self.protocol
    
    def setProtocol(self, protocol):
        """ Tries to set mouse protocol, returns True on success. """
        if protocol == self.INTELLI_MOUSE:
            command = self.COMMAND_IMPS2
        elif protocol == self.EXPLORER_MOUSE:
            command = self.COMMAND_IMEX
        else:
            raise NotImplementedError("Protocol not implemented")
        
        success = self._sendSimpleCommand(command)
        if success:
            self.protocol = protocol
        return success
    
    def _setStreamMode(self):
        return self._sendSimpleCommand(self.COMMAND_STREAM_MODE)
    
    def getMouseState(self):
        """ Blocks until mouse sends a status packet and returns its decoded
            values as a MouseData tuple.
            
            Mouse protocol uses 3 byte packets and 4 byte packets if additional
            protocol is activated:
        
            Default 3 bytes:
            
              Byte | Bit 7 | Bit 6 | Bit 5 | Bit 4 | Bit 3 | Bit 2 | Bit 1 | Bit 0
             ------+-------+-------+-------+-------+-------+-------+-------+-------
                1  | Yovfl | Xovfl |  dy8  |  dx8  |   1   | Btn 3 | Btn 2 | Btn 1
                2  |  dx7  |  dx6  |  dx5  |  dx4  |  dx3  |  dx2  |  dx1  |  dx0
                3  |  dy7  |  dy6  |  dy5  |  dy4  |  dy3  |  dy2  |  dy1  |  dy0
            
            When IntelliMouse mode is enabled:
            
                4  |  dz3  |  dz3  |  dz3  |  dz3  |  dz3  |  dz2  |  dz1  |  dz0
            
            When Explorer Mouse mode is enabled:
            
                4  |   0   |   0   | Btn 5 | Btn 4 |  dz3  |  dz2  |  dz1  |  dz0
            
            Additional protocols (e.g. Typhoon mouse) will _not_ be used.
            
            Source of information: http://www.win.tue.nl/~aeb/linux/kbd/scancodes-13.html
        """
        
        #number of bytes to be read differs based on protocol used
        length = 3 if self.protocol == self.DEFAULT_MOUSE else 4
        
        buf = os.read(self.mouse, length)
        
        if len(buf) != length:
            #this might happen if mouse sends some other response we don't expect.
            raise MouseException("Length of bytes read does not match expected length")
        
        b1, b2, b3 = bool(buf[0] & 1), bool(buf[0] & 2), bool(buf[0] & 4)
        #Buttons 4 and 5 are only available in Explorer Mouse protocol
        b4 = b5 = False
        
        xovfl, yovfl = bool(buf[0] & 64), bool(buf[0] & 128)
        
        x = int(buf[1]) - (buf[0] & 16) * 16
        y = int(buf[2]) - (buf[0] & 32) *  8
        
        #Wheel is only available in IntelliMouse or Explorer mouse protocol
        bWheel = 0
        
        if (length == 4):
            #clear all non-wheel related bits regardless of INTELLI_MOUSE or
            #EXPLORER_MOUSE protocol by ANDing with 0b00001111 = 15
            wheel = buf[3] & 15
            
            #wheel data is 4-bit in 2's complement, but we need to convert it manually.
            bWheel = wheel - (wheel & 8) * 2
            #bWheel has now a value in [-8, ..., +7]
            #no further distinguishing between multiple wheels here on purpose.
            
            if self.protocol == self.EXPLORER_MOUSE:
                #check buttons 4 and 5
                b4 = bool(buf[3] & 16)
                b5 = bool(buf[3] & 32)
        
        return MouseData(x, y, xovfl, yovfl, b1, b2, b3, b4, b5, bWheel)


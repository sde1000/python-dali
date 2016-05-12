from dali.command import Command
import dali.frame
import usb.core
import struct
from time import sleep
import logging


# XXX: Adopt to new API


class HassebUsb(object):
    """ Creates a server object which is able to communicate to the Hasseb DALI 
    Master device from http://hasseb.fi/ based on a NXP LPC1343 ARM microprocesor
    with open source firmware.    
    """

    def __init__(self):
        self.ep = None
        self.epRead = None
    
    def _openDevice(self):
        self.interface = 0
        self.vid = 0x04cc
        self.pid = 0x0802
        self.dev = usb.core.find(idVendor=self.vid, idProduct=self.pid)
    
        if self.dev is None:
            raise IOError("Device with VID=%x and PID=%x not found"
                          %(self.vid, self.pid) )
        
        if self.dev.is_kernel_driver_active(self.interface) is True:
            # print "but we need to detach kernel driver"
            self.dev.detach_kernel_driver(self.interface)
    
        self.dev.set_configuration()
        usb.util.claim_interface(self.dev, self.interface)
    
        cfg = self.dev.get_active_configuration()
        intf = cfg[(0,0)]
    
        self.ep = usb.util.find_descriptor(
             intf,
             custom_match = \
             lambda e: \
                 usb.util.endpoint_direction(e.bEndpointAddress) == \
                 usb.util.ENDPOINT_OUT)
    
    
        self.epRead = usb.util.find_descriptor(
             intf,
             custom_match = \
             lambda e: \
                 usb.util.endpoint_direction(e.bEndpointAddress) == \
                 usb.util.ENDPOINT_IN)
        
    def _writeDali(self, a, b, responseExpected=False ):
        """ 
        Sends out a DALI telegram and waits for the response if needed.
        
        @param address 0 <= address <= 255 Address to send (be careful, special modes will be send here too)
        @param cmd 0 <= cmd <= 255 Command to send
        @param responseExpected if True waits for response and returns it 
        
        @return The response or None if nothing requested nor received.
        """
        self.ep.write( struct.pack('BB',a,b))
    
        if responseExpected:
            # print "Reading endpoint ..."
            retryCount = 40
            while True:
                rdData = self.epRead.read(self.epRead.wMaxPacketSize)
                
                if len(rdData) >= 2 and rdData[0] != 0:
                    # Received a valid response
                    break
                
                if retryCount <= 0:
                    rdData = None
                    # TODO: Check if this is ok. 
                    raise IOError("Device does not respond but command needs it.")
                    break
                
                retryCount -= 1            
                sleep(0.015)
                
            # Evaluate the response if there was one
            if rdData is not None:
                # 0: "No Data Available"
                # 1: "No Answer"
                # 2: "OK"
                # 3: "Invalid Answer"
                responseStatus = rdData[0]
                
                if responseStatus == 2:
                    return dali.frame.BackwardFrame(rdData[1])
                elif responseStatus == 3:
                    return dali.frame.BackwardFrameError(255)
                
            return None


    def send(self, command):
        if self.ep is None:
            self._openDevice()

        assert isinstance(command, Command)
        
        needsResponse = command.response is not None
        a, b = command.frame.as_byte_sequence
        
        # print(u" SEND: a=0x%x b=0x%x"%(a,b))
        
        backward = self._writeDali( a, b, needsResponse)
        if command._response:
            response = command._response(backward)
        else:
            response = None

        if response:
            logging.debug(u"  -> {0}".format(response))

        return response

__all__ = ["HassebUsb"]
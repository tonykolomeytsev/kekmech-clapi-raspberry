import json
import os
import time

import serial as s
import struct
import math
import sys

from asynclapi import *


BAUD_RATE = 115200
KEKMECH_VERSION = '1.2.2'
CMD_HANDSHAKE = 0x13

debug = False
core = None



def start():
    """ Set up connection with all connected devices """
    global core
    core = Core()

def status():
    print('Core version {}'.format(KEKMECH_VERSION))
    for dev in core.devices:
        print(dev)


class Core:
    """
    Сore object stores a list of devices and adds 
    links to devices to Clapi module attributes
    """

    def __init__(self):
        """
        Trying to connect with all connected devices and
        get a list of devices connected via USB.
        Chineese arduino: /dev/ttyUSB###
        Arduino and STM32: /dev/ttyACM###
        """
        devices = ['/dev/ttyACM' + str(i) for i in range(0, 4)] + ['/dev/ttyUSB' + str(i) for i in range(0, 4)]
        activeDevices = map(lambda e: Device(e) if os.path.exists(e) else None, devices)
        clapiModule = sys.modules[__name__]
        self.devices = list()
        for d in activeDevices:
            if hasattr(d,'id'):
                setattr(clapiModule, str(d.id), d)
                self.devices.append(d)



class Device:
    """
    The Device instance is trying to communicate over the protocol 
    with the deviceId (for example "/dev/ttyUSB0") that it was given
    """

    def __init__(self, deviceId):
        self.serial = SerialWrapper(s.Serial(deviceId, BAUD_RATE), deviceId)
        self.task_pool = TaskPool(self.serial)
        # handshake is an attempt to establish a connection with the device
        self.data = self.serial.handshake()
        
        if (self.data is not None):
            self.id = self.data.get('device_id', 'unnamed')
    
    def push(self, code:int, *args):
        self.serial.push(code, args)
    
    def pull(self):
        return json.loads(self.serial.pull())
    
    def request(self, code:int, *args):
        self.serial.push(code, args)
        return json.loads(self.serial.pull())
    
    def push_async(self, code:int, *args):
        task = Push(code, *args)
        task._executor = self.task_pool.push_task
        return task
    
    def request_async(self, code:int, *args):
        task = Request(code, *args)
        task._executor = self.task_pool.push_task
        return task
        
    def long_poll_async(self, code:int, *args):
        task = LongPoll(code, *args)
        task._executor = self.task_pool.push_task
        return task

    def reset(self):
        self.task_pool.reset()

    def __str__(self):
        response =  '(Device \"{}\": '.format(self.id)
        response += str(self.task_pool)
        response += ')'
        return response



class SerialWrapper:
    """ Convenient wrapper for Serial. Also used for testing """

    def __init__(self, serial, deviceId):
        """ Don't create serial instance here, get in outside """
        self.serial = serial
        self.deviceId = deviceId

    def decompose(self, number):
        """ Convert float to byte array """
        return bytes(struct.pack('f', number))

    def push(self, code:int, args):
        """ Send message to device """
        if debug: 
            print('push', self.deviceId, '>>', {'code': code, 'args': args})
        argsCount = len(args)
        bytesToSend = bytes([code, argsCount])
        for arg in args:
            bytesToSend += self.decompose(arg)
        self.serial.write(bytesToSend)

    def request(self, code:int, args):
        self.push(code, args)
        return self.pull()

    def flush(self):
        self.serial.flush()

    def clear_input(self):
        self.serial.reset_input_buffer()

    def pull(self):
        """ Get a message from the device """
        response = self.serial.readline().decode('ascii').rstrip()
        if debug:
            print('pull', self.deviceId, '<<', response)
        return response

    def inWaiting(self):
        return self.serial.inWaiting()

    def handshake(self):
        """ Set up connection """
        if not self.serial.inWaiting():
            self.push(CMD_HANDSHAKE,[])
        line = self.pull()
        return json.loads(line)

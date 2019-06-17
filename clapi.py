import json
import os
import time

import serial as s
import struct
import math
import sys

from asynclapi import *


BAUD_RATE = 115200
KEKMECH_VERSION = '1.1'
CMD_HANDSHAKE = 0x13

debug = False
core = None



def start():
    global core
    core = Core()

def status():
    print('Core version {}'.format(KEKMECH_VERSION))
    for dev in core.devices:
        print(dev)


class Core:

    # Связываемся со всеми подключенными ардуинками
    def __init__(self):
        # получаем список подключённых по USB устройств
        # для UNO dev/ttyACM + для NANO dev/ttyUSB
        devices = ['/dev/ttyACM' + str(i) for i in range(0, 4)] + ['/dev/ttyUSB' + str(i) for i in range(0, 4)]
        # пытаемся подключиться к ним, как к ардуине и получаем список ардуин
        activeDevices = map(lambda e: Device(e) if os.path.exists(e) else None, devices)
        clapiModule = sys.modules[__name__]
        self.devices = list()
        for d in activeDevices:
            if hasattr(d,'id'):
                setattr(clapiModule, str(d.id), d)
                self.devices.append(d)



class Device:

    # Экземпляр ардуинки пытается связаться по протоколу с тем deviceId, что ей дали
    def __init__(self, deviceId):
        self.serial = SerialWrapper(s.Serial(deviceId, BAUD_RATE), deviceId)
        self.task_pool = TaskPool(self.serial)
        # рукопожатие (попытка соединиться с устройством)
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



# обёртка для Serial
class SerialWrapper:

    # просто получаем значения извне. dependency injection
    def __init__(self, serial, deviceId):
        self.serial = serial
        self.deviceId = deviceId

    # перевод дробного числа в массив байт
    def decompose(self, number):
        return bytes(struct.pack('f', number))

    # отправка стандартного сообщения на Arduino
    def push(self, code:int, args):
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

    # принять сообщение от Arduino
    def pull(self):
        response = self.serial.readline().decode('ascii').rstrip()
        if debug:
            print('pull', self.deviceId, '<<', response)
        return response

    def inWaiting(self):
        return self.serial.inWaiting()

    # установка соединения с Arduino
    def handshake(self):
        if not self.serial.inWaiting():
            self.push(CMD_HANDSHAKE,[])
        line = self.pull()
        return json.loads(line)



if __name__=="__main__":
    import tui
    tui.start(sys.modules[__name__])
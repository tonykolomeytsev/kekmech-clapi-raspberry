import json
import os
import time

import serial as s
import struct
import math
import sys

from asynclapi import *


BAUD_RATE = 115200

debug = True
core = 0



def start():
    core = Core()



class Core:

    # Связываемся со всеми подключенными ардуинками
    def __init__(self):
        # получаем список подключённых по USB устройств
        # для UNO dev/ttyACM + для NANO dev/ttyUSB
        devices = ['/dev/ttyACM' + str(i) for i in range(0, 4)] + ['/dev/ttyUSB' + str(i) for i in range(0, 4)]
        # пытаемся подключиться к ним, как к ардуине и получаем список ардуин
        activeDevices = map(lambda e: Device(e) if os.path.exists(e) else None, devices)
        clapiModule = sys.modules[__name__]
        for d in activeDevices:
            if hasattr(d,'id'):
                setattr(clapiModule, str(d.id), d)



class Device:

    task_pool = None

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
        return self.serial.pull()
    
    def request(self, code:int, *args):
        self.serial.push(code, args)
        return self.serial.pull()
    
    def push_async(self, code:int, *args, **kwargs):
        task = Push(code, args)
        task.is_infinite = kwargs.get('is_infinite', False)
        self.task_pool.push_task(task)
    
    def request_async(self, code:int, *args, **kwargs):
        callback = kwargs.get('callback', None)
        task = Request(callback, code, args)
        task.is_infinite = kwargs.get('is_infinite', False)
        self.task_pool.push_task(task)

    def reset(self):
        self.task_pool.reset()



# обёртка для Serial
class SerialWrapper:

    # просто получаем значения извне. dependency injection
    def __init__(self, serial, deviceId):
        self.serial = serial
        self.deviceId = deviceId

    # перевод дробного числа в массив байт
    def decompose(self, number):
        print(number)
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

    # установка соединения с Arduino
    def handshake(self):
        line = self.pull()
        return json.loads(line)

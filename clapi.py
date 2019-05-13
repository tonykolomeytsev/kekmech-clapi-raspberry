import json
import os
import time

import serial as s
import struct
import math

from threading import Thread

BAUD_RATE = 115200

debug = True



class Core:
    # лист кортежей (Поток, Ардуино)
    routines = []

    # Связываемся со всеми подключенными ардуинками
    def __init__(self):
        # получаем список подключённых по USB устройств
        # для UNO dev/ttyACM + для NANO dev/ttyUSB (TODO не подключается NANO)
        devices = ['/dev/ttyACM' + str(i) for i in range(0, 4)] + ['/dev/ttyUSB' + str(i) for i in range(0, 4)]
        # пытаемся подключиться к ним, как к ардуине и получаем список ардуин
        activeDevices = map(lambda e: Arduino(e) if os.path.exists(e) else None, devices)
        arduinoDevices = filter(lambda e: e is not None, activeDevices)
        # отбрасываем те ардуинки, которые прислали неверные протокольные данные для подключения
        self.arduino = list(filter(lambda e: e.data is not None, arduinoDevices))

    def serial(self, device_id):
        return get(device_id).serial
        
    def request(self, device_id, cmd_id: int, args):
        self.arduino[device_id].serial.push(cmd_id, args)
        return self.arduino[device_id].serial.pull()

    # возвращает объект ардуино по её имени device_id
    def get(self, device_id):
        ans = list(filter(lambda x: x.id == device_id, self.arduino))
        if len(ans) == 0:
            print('Can\'t find "', device_id, '" device')
            return None
        else:
            return ans[0]

      

class Arduino:
    # Экземпляр ардуинки пытается связаться по протоколу с тем deviceId, что ей дали
    def __init__(self, deviceId):
        self.serial = SerialWrapper(s.Serial(deviceId, BAUD_RATE), deviceId)
        # рукопожатие (попытка соединиться с устройством)
        self.data = self.serial.handshake()
        
        if (self.data is not None):
            self.id = self.data.get('device_id', 'unnamed')

    def use(self):
        return (self.id, self.serial)



# Удобная обёртка для Serial
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
            print(' push', self.deviceId, '>>', {'code': code, 'args': args})
        argsCount = len(args)
        bytesToSend = bytes([code, argsCount])
        for arg in args:
            bytesToSend += self.decompose(arg)
        self.serial.write(bytesToSend)

    # отправка стандартного сообщения на Arduino
    def push_and_listen(self, code:int, args):
        push(code, args)

        while True:
            self.pull()

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
            print(' pull', self.deviceId, '<<', response)
        return response

    # установка соединения с Arduino
    def handshake(self):
        line = self.pull()
        return json.loads(line)

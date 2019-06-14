from asynclapi import *
import clapi as api
import unittest
import time

# Mock for SerialWrapper
class SerialWrapper_Mock:

    data = None
    last_push = None

    def inWaiting(self):
        return self.data != None 

    # отправка стандартного сообщения на Arduino
    def push(self, code:int, args):
        self.last_push = {"code":code,"args":args} 

    def request(self, code:int, args):
        self.push(code, args)
        return self.pull()

    def flush(self):
        pass

    def clear_input(self):
        pass

    # принять сообщение от Arduino
    def pull(self):
        kek = self.data
        self.data = None
        return kek

    # установка соединения с Arduino
    def handshake(self):
        return {'device_id':'test'}



# Mock for Core
class Core_Mock():
    devices = list()

    # Put devices mocks
    def __init__(self, devices):
        for d in devices:
            if hasattr(d,'id'):
                setattr(api, str(d.id), d)
                self.devices.append(d)



# Mock for device
class Device_Mock(api.Device):

    def __init__(self, id):
        self.serial = SerialWrapper_Mock()
        self.task_pool = TaskPool(self.serial)
        self.id = id


class ClapiTest(unittest.TestCase):
    """ Clapi functions test """

    @classmethod
    def setUpClass(cls):
        print("Set up ClapiTest \n=============================")

    @classmethod
    def tearDownClass(cls):
        print("\n=============================\nTear down ClapiTest")
    
    def setUp(self):
        print("\nSet up for [" + self.shortDescription() + "]")
        # set up our fake devices
        devices = [ 
            Device_Mock("dev1"), 
            Device_Mock("dev2")
        ]
        # instead of api.start():
        api.core = Core_Mock(devices)
    
    def tearDown(self):
        print("Tear down for [" + self.shortDescription() + "]")
        api.core = None
    
    def test_push(self):
        """test push"""
        print(self.id)
        code = 0x42
        args = [1, 2, 3]

        try:
            api.dev1.push(code, *args)
            api.dev2.push(code, *args)
        except:
            self.fail("Something went wrong with sync PUSH")
    
    def test_pull(self):
        """test pull"""
        print(self.id)
        s1 = api.dev1.serial
        s2 = api.dev2.serial

        s1.data = '{"status":200}'
        s2.data = '{"status":300}'

        self.assertEqual(api.dev1.pull(), {"status": 200})
        self.assertEqual(api.dev2.pull(), {"status": 300})

    def test_request(self):
        """test request"""
        print(self.id)
        code = 0x42
        args = [1, 2, 3]

        s1 = api.dev1.serial
        s2 = api.dev2.serial

        s1.data = '{"status":200,"code":%d}'%(code)
        s2.data = '{"status":300,"code":%d}'%(code)
        try:
            r1 = api.dev1.request(code, *args)
            r2 = api.dev2.request(code, *args)
        except:
            self.fail("Something went wrong with sync PUSH")
        
        self.assertEqual(r1, {"status": 200, "code": code})
        self.assertEqual(r2, {"status": 300, "code": code})

    def test_method_chaining(self):
        """test method chaining"""
        print(self.id)
        def simple_callback(kek):
            pass
        
        try:
            l = LongPoll(4)\
                .args(26) \
                .callback(simple_callback)
            r = Request(4) \
                .args(26) \
                .callback(simple_callback)
            p = Push(4) \
                .args(26)
        except:
            self.fail("Something wrong with method chaining")

    def test_async_push(self):
        """test ASYNC push"""
        print(self.id)
        args = [1, 2, 3]
        s1 = api.dev1.serial
        s2 = api.dev2.serial
        tp1 = api.dev1.task_pool
        tp2 = api.dev2.task_pool

        try:
            p1=api.dev1.push_async(98)\
                .args(*args)\
                #.execute()
            p2=api.dev2.push_async(99)\
                .args(*args)
                #.execute()
        except:
            self.fail("Something went wrong with sync PUSH")

        p1.execute()
        p2.execute()

        time.sleep(0.2) # wait main_loop thread of each device
        print(s1.last_push, s2.last_push)
        
        api.dev1.task_pool.running = False
        api.dev2.task_pool.running = False

        time.sleep(0.2) # wait main_loop thread stops

        self.assertEqual({"code":98,"args":args}, s1.last_push)
        self.assertEqual({"code":99,"args":args}, s2.last_push)
        if tp1.main_thread:
            self.assertFalse(tp1.main_thread.isAlive())
        if tp2.main_thread:
            self.assertFalse(tp2.main_thread.isAlive())
        self.assertTrue(len(tp1.tasks) == 0)
        self.assertTrue(len(tp2.tasks) == 0)
        self.assertTrue(len(tp1.subscribers.items()) == 0)
        self.assertTrue(len(tp2.subscribers.items()) == 0)
        


if __name__=="__main__":
    unittest.main()
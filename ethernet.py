import clapi as api
import socket

TCP_IP = '192.168.1.200' # ip of CLAPI server
TCP_PORT = 5005
BUFFER_SIZE = 20 # Normally 1024, but I want fast response

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)

conn, addr = s.accept()
print ('Connection address:', addr)
while 1:
    data = conn.recv(BUFFER_SIZE)
    if not data: break
    print ("received data:", data)
    conn.send(data)  # echo
conn.close()

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
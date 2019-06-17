# Clapi

A library for transferring data between Raspberry Pi, Arduino and STM32 Nucleo using Serial. The library is designed to work with [Clapi Arduino](https://github.com/tonykolomeytsev/kekmech-clapi-arduino) or [Clapi Nucleo](https://github.com/tonykolomeytsev/kekmech-clapi-nucleo).

![alt text](https://raw.githubusercontent.com/tonykolomeytsev/kekmech-clapi-raspberry/master/img.png)

Visit the [wiki](https://github.com/tonykolomeytsev/kekmech-clapi-raspberry/wiki) page to understand how it works.

## Features

* Sending commands in the binary format (quickly parsed on the microcontroller)
* Communication with each device occurs in a separate thread.

## How to install

Clone or [download](https://github.com/tonykolomeytsev/kekmech-clapi-raspberry/archive/master.zip) the project to your local computer (raspberry?) and in the root project folder run the command:

```
sudo python3 setup.py install
```

## Using

Just import the library and call the start() function.

```python
import clapi as api

# setting up a connection with all devices connected via USB
api.start()
api.status() # shows all connected devices
```

After that, you can send commands to microcontrollers. When the connection is established, arduino sends us its **device_id**. If first arduino sent us ```{device_id: 'dev1'}``` and the second arduino sent ```{device_id: 'dev2'}```, then we can control them as follows:

```python
# send the command to the first arduino
# command "1" with two arguments: 2 and 3 
api.dev1.push(1, 2, 3)

answer = api.dev1.pull() # waiting for response from first arduino
print(answer)

answer = api.dev2.request(5) # request to the second arduino
print(answer)
```

## License

```
MIT License

Copyright (c) 2019 Anton Kolomeytsev

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
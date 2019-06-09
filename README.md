# Clapi

A library for transferring data between Raspberry Pi, Arduino and STM32 Nucleo using Serial. The library is designed to work with [Clapi Arduino](https://github.com/tonykolomeytsev/kekmech-clapi-arduino) or [Clapi Nucleo](https://github.com/tonykolomeytsev/kekmech-clapi-nucleo).

![alt text](https://raw.githubusercontent.com/tonykolomeytsev/kekmech-clapi-raspberry/master/img.png)

Visit the wiki page to understand how it works.

## Features

* Sending commands in the binary format (quickly parsed on the microcontroller)

## Using

Just import the library and call the start() function.

```
import clapi as api

# setting up a connection with all devices connected via USB
api.start()
api.status() # shows all connected devices
```

After that, you can send commands to microcontrollers. When the connection is established, arduino sends us its **device_id**. If first arduino sent us ```{device_id: 'test'}``` and the second arduino sent ```{device_id: 'foo'}```, then we can send the command as follows:

```
# send the command to the first arduino
# command "1" with two arguments: 2 and 3 
api.test.push(1, 2, 3)

api.test.pull() # waiting for response from first arduino

api.foo.request(5) # request to the second arduino
```

## Push command

On Arduino you can send a command like: ```[code(1 Byte)][argsCount(1 Byte)] [arg1][arg2]...``` when each argument is a real number takes 4 bytes.

Typical push:
```
api.arduino1.push([code], [arg1], [arg2]...)
# or
api.arduino1.push([code]) # without any args
```

## Pull command

Arduino will send you JSON. You can use any json parsing library.

```
response = api.arduino1.pull()
json.loads(response)
```

## Request command

Request is just push() after which goes pull(). It is just launch two functions in order.

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
from distutils.core import setup

setup(
	name="clapi",
	version="1.2.1",
	description="A simple library for controlling Arduino and STM32 Nucleo via Raspberry Pi using Serial.",
	author="Anton Kolomeytsev",
	author_email="tonykolomeytsev@gmail.com",
	url="https://github.com/tonykolomeytsev/kekmech-clapi-raspberry",
	py_modules=['clapi', 'asynclapi'],
    libraries=['pyserial'],
	license='MIT License',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ])
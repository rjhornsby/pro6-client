from setuptools import setup

setup(
    name='pro6-client',
    version='',
    packages=['pi', 'observer', 'osc', 'pro6'],
    url='',
    license='',
    author='rhornsby',
    author_email='',
    description='', install_requires=['lomond', 'board', 'osc4py3', 'netifaces', 'netaddr', 'scapy', 'zeroconf',
                                      'PyYAML', 'RPi.GPIO', 'adafruit-circuitpython-neopixel', 'smbus']
)


# sudo apt-get install python-dev git scons swig
# git clone https://github.com/jgarff/rpi_ws281x.git
# cd rpi_ws281x
# sudo scons
# cd python
# sudo python3 setup.py build
# sudo python3 setup.py install
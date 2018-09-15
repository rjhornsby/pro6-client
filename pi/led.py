#!/usr/bin/env python3.7
import RPi.GPIO as GPIO
import Adafruit_WS2801
import Adafruit_GPIO.SPI as SPI
import time

PIXEL_COUNT = 10
SPI_PORT = 0
SPI_DEVICE = 0

class LED:
    def __init__(self):

        self.pixels = Adafruit_WS2801.WS2801Pixels(PIXEL_COUNT, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE), gpio=GPIO)

    def green(self):
        self.pixels.clear()
        for i in range(self.pixels.count()):
            self.pixels.set_pixel(i, Adafruit_WS2801.RGB_to_color(0, 255, 0))

        self.pixels.show()

    def yellow(self, time_remaining):
        count = int(time_remaining.total_seconds())
        self.pixels.clear()
        for i in range(count):
            self.pixels.set_pixel(i, Adafruit_WS2801.RGB_to_color(255, 255, 0))

        self.pixels.show()

    def red(self, time_remaining):
        count = int(time_remaining.total_seconds())
        self.pixels.clear()
        for i in range(count):
            self.pixels.set_pixel(i, Adafruit_WS2801.RGB_to_color(255, 0, 0))

        self.pixels.show()

    def clear(self):
        self.pixels.clear()
        self.pixels.show()


    # Define the wheel function to interpolate between different hues.
    def wheel(self, pos):
        if pos < 85:
            return Adafruit_WS2801.RGB_to_color(pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return Adafruit_WS2801.RGB_to_color(255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return Adafruit_WS2801.RGB_to_color(0, pos * 3, 255 - pos * 3)

    # Define rainbow cycle function to do a cycle of all hues.
    def rainbow_cycle_successive(self, wait=0.1):
        for i in range(pixels.count()):
            # tricky math! we use each pixel as a fraction of the full 96-color wheel
            # (thats the i / strip.numPixels() part)
            # Then add in j which makes the colors go around per pixel
            # the % 96 is to make the wheel cycle around
            pixels.set_pixel(i, self.wheel(((i * 256 // pixels.count())) % 256))
            pixels.show()
            if wait > 0:
                time.sleep(wait)

    def rainbow_cycle(self, wait=0.005):
        for j in range(256):  # one cycle of all 256 colors in the wheel
            for i in range(pixels.count()):
                pixels.set_pixel(i, self.wheel(((i * 256 // pixels.count()) + j) % 256))
            self.pixels.show()
            if wait > 0:
                time.sleep(wait)

    def rainbow_colors(self, wait=0.05):
        for j in range(256):  # one cycle of all 256 colors in the wheel
            for i in range(pixels.count()):
                pixels.set_pixel(i, self.wheel(((256 // pixels.count() + j)) % 256))
            pixels.show()
            if wait > 0:
                time.sleep(wait)

    def brightness_decrease(self, wait=0.01, step=1):
        for j in range(int(256 // step)):
            for i in range(pixels.count()):
                r, g, b = pixels.get_pixel_rgb(i)
                r = int(max(0, r - step))
                g = int(max(0, g - step))
                b = int(max(0, b - step))
                pixels.set_pixel(i, Adafruit_WS2801.RGB_to_color(r, g, b))
            pixels.show()
            if wait > 0:
                time.sleep(wait)

    def blink_color(self, blink_times=5, wait=0.5, color=(255, 0, 0)):
        for i in range(blink_times):
            # blink two times, then wait
            pixels.clear()
            for j in range(2):
                for k in range(pixels.count()):
                    pixels.set_pixel(k, Adafruit_WS2801.RGB_to_color(color[0], color[1], color[2]))
                pixels.show()
                time.sleep(0.08)
                pixels.clear()
                pixels.show()
                time.sleep(0.08)
            time.sleep(wait)

    def appear_from_back(self, color=(255, 0, 0)):
        pos = 0
        for i in range(pixels.count()):
            for j in reversed(range(i, pixels.count())):
                pixels.clear()
                # first set all pixels at the begin
                for k in range(i):
                    pixels.set_pixel(k, Adafruit_WS2801.RGB_to_color(color[0], color[1], color[2]))
                # set then the pixel at position j
                pixels.set_pixel(j, Adafruit_WS2801.RGB_to_color(color[0], color[1], color[2]))
                pixels.show()
                time.sleep(0.02)



if __name__ == "__main__":
    # Clear all the pixels to turn them off.

    led_strip = LED()
    pixels = led_strip.pixels
    pixels.clear()
    pixels.show()  # Make sure to call show() after changing any pixels!

    led_strip.rainbow_cycle_successive(wait=0.1)
    led_strip.rainbow_cycle(wait=0.01)

    led_strip.brightness_decrease()

    led_strip.appear_from_back()

    for i in range(3):
        led_strip.blink_color(blink_times=1, color=(255, 0, 0))
        led_strip.blink_color(blink_times=1, color=(0, 255, 0))
        led_strip.blink_color(blink_times=1, color=(0, 0, 255))

        led_strip.rainbow_colors()

        led_strip.brightness_decrease()
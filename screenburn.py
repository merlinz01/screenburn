#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# The MIT License (MIT)

# Copyright (c) 2024 Merlin Zimmerman

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""This script adjusts the color temperature of the screen based on the altitude of the Sun above the horizon.
It also turns the screen off for a short period every 20 minutes to promote taking breaks.

Set it as an autostart program in your window manager to run it automatically when you log in.
"""

import math
from datetime import datetime, timedelta
import time
from typing import NewType

Radians = NewType("Radians", float)
Degrees = NewType("Degrees", float)

# Constants
EARTH_AXIS_TILT = Degrees(23.44)  # Earth's axial tilt in degrees

def solar_declination(date: datetime) -> Degrees:
    """Calculates the solar declination for a given day of the year."""
    return Degrees(EARTH_AXIS_TILT * math.sin(math.radians((date.timetuple().tm_yday - 81) * 360 / 365)))

def equation_of_time(date:datetime) -> float:
    """Calculates the equation of time to adjust solar time."""
    # See https://en.wikipedia.org/wiki/Equation_of_time
    D = 6.24 + 0.0172 * (365.25 * (date.year - 2000) + date.timetuple().tm_yday)
    return -7.659 * math.sin(D) + 9.863 * math.sin(2 * D + 3.5932)

def time_correction(longitude: Degrees, equation_of_time: float) -> float:
    """Calculates time correction factor to adjust for longitude and equation of time."""
    # The Earth rotates 360 degrees in 24 hours, so 1 degree corresponds to 4 minutes
    return 4 * longitude + equation_of_time

def solar_hour_angle(time: datetime, time_correction: float) -> Degrees:
    """Calculates the solar hour angle in degrees."""
    solar_time = (time.hour * 60 + time.minute + time_correction) / 60
    return Degrees((solar_time - 12) * 15)  # 15 degrees per hour

def solar_altitude(latitude: Degrees, declination: Degrees, hour_angle: Degrees) -> float:
    """Calculates the altitude of the Sun based on latitude, declination, and hour angle."""
    latitude_rad = math.radians(latitude)
    declination_rad = math.radians(declination)
    hour_angle_rad = math.radians(hour_angle)

    altitude = math.asin(
        math.sin(latitude_rad) * math.sin(declination_rad) +
        math.cos(latitude_rad) * math.cos(declination_rad) * math.cos(hour_angle_rad)
    )
    
    return math.degrees(altitude)

def sun_altitude(latitude: Degrees, longitude: Degrees, now: datetime) -> float:
    """Returns the altitude of the Sun above the horizon for a given location and time."""

    # Calculate solar declination (angle of the Sun above the equator)
    declination = solar_declination(now)
    
    # Equation of time (in minutes)
    eq_time = equation_of_time(now)
    
    # Time correction for longitude (in minutes)
    time_corr = time_correction(longitude, eq_time)
    
    # Solar hour angle
    hour_angle = solar_hour_angle(now, time_corr)
    
    # Altitude of the Sun
    altitude = solar_altitude(latitude, declination, hour_angle)
    
    return altitude

if __name__ == "__main__":
    import subprocess

    latitude = Degrees(43.94)
    longitude = Degrees(-70.91)

    min_temp = 3200
    max_temp = 3500

    relief_period = timedelta(minutes=20)
    relief_duration = 20 # seconds
    monitors = subprocess.run(['xrandr', '--listactivemonitors'], capture_output=True, text=True).stdout
    monitor = monitors.splitlines()[1].split()[3]
    print(f"Using monitor {monitor}")

    last_relief = datetime.now()
    while True:
        if datetime.now() - last_relief > relief_period:
            print("Taking a break")
            subprocess.run(['xrandr', '--output', monitor, '--off'])
            time.sleep(relief_duration)
            subprocess.run(['xrandr', '--output', monitor, '--auto'])
            last_relief = datetime.now()
            time.sleep(0.25)
        now = datetime.now()
        altitude = sun_altitude(latitude, longitude, now)
        temp = min_temp + (max_temp - min_temp) * (altitude + 90) / 180
        print(f"Sun altitude: {altitude:.2f}°, Temp: {temp:.2f} K")
        subprocess.run(['sct', str(temp)])
        time.sleep(60)


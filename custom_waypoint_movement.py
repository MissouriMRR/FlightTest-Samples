#!/usr/bin/env python3

import typing
import asyncio

from mavsdk import System
import mavsdk as sdk
import logging
import math

async def run():
    """
    This function allows the user to enter in any amount of waypoints with their
    respective latitude,longitude and altitude and then moves the drone to each
    waypoint and eventually returns to the home location and lands
    """
    
    """
    Some example waypoints at the S&T golf course are as follows:
    Waypoint 1:
    Lattitude: 37.9487007
    Longitude: -91.7842494
    Altitude: 50

    Waypoint 2:
    Latitude: 37.9486118
    Longitude: -91.7840774
    Altitude: 100
    """
    lats: [float] = []
    longs: [float] = []
    altitudes: [float] = []

    waypoints: int = int(input("Enter number of waypoints:"))
    for i in range(waypoints):
        #loop stores each user entered longitude,latitude and altitude
        num1: float =float(input("Enter a Latitude:"))
        num2: float =float(input("Enter a Longitude:"))
        num3: float =float(input("Enter an Altitude:"))
        num3 = num3 * .3048 #converts feet to meters since the drone takes in meters
        lats.append(num1)
        longs.append(num2)
        altitudes.append(num3)

    #create a drone object
    drone: System = System()
    await drone.connect(system_address="udp://:14540")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone discovered!")
            break

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok:
            print("Global position estimate ok")
            break

    print("Fetching amsl altitude at home location....")
    async for terrain_info in drone.telemetry.home():
        absolute_altitude = terrain_info.absolute_altitude_m
        break

    print("-- Arming")
    await drone.action.arm()

    print("-- Taking off")
    await drone.action.takeoff()

    await asyncio.sleep(20)
    # To fly drone 20m above the ground plane
    flying_alt: float = absolute_altitude + 20.0
    # goto_location() takes Absolute MSL altitude

    #Loop to move through waypoints
    for point in range(waypoints): 
        await drone.action.goto_location(lats[point], longs[point], altitudes[point]+absolute_altitude, 0)
        location_reached: bool=False

        #Loops until the waypoint is reached
        while(not location_reached):
            print("Going to waypoint: "+str(point+1))
            async for position in drone.telemetry.position():
                #continuously checks current latitude, longitude and altitude of the drone
                drone_lat: float=position.latitude_deg
                drone_long: float=position.longitude_deg
                drone_alt: float=position.relative_altitude_m

                #checks if location is reached and moves on if so
                if ((round(drone_lat,1)==round(lats[point],1)) and 
                (round(drone_long,1)==round(longs[point],1)) and 
                (round(drone_alt,1)==round(altitudes[point],1))):
                    location_reached=True
                    print("arrived, moving on")
                    break

            await asyncio.sleep(2)
    
    print("Last waypoint reached")
    print("Returning to home")
    await drone.action.return_to_launch()
    while True:
        print("Staying connected, press Ctrl-C to exit")
        await asyncio.sleep(1)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
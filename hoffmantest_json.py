"""
Main driver code for moving drone to each waypoint
"""

import asyncio
import json
from mavsdk import System
import mavsdk as sdk
import logging
import math
import typing
from typing import Dict, List
from avoidance import rrt_flight_test


def waypoint_parsing(filename: str) -> List[Dict[str,float]]:
    """
    Parses the json file for all mission-critical waypoints
    Args:
        filename (str): name of the json file

    Returns:
        Waypoint_Locs ([Dict[str,float]]): List of dictionaries containing 
        a string identifier and float for lattitude, longitude and altitude
    """
    with open(filename, 'r') as f:
        data_set = json.load(f)
    # print(data_set)

    waypoint_Locs: List[Dict[str,float]] = []

    for i in range(0, len(data_set["waypoints"])):
        waypoint_Locs.append(data_set["waypoints"][i])

    return waypoint_Locs


def stationary_obstacle_parsing(filename: str) -> List[Dict[str, float]]:
    """
    Opens passed JSON file and extracts the Stationary obstacle attributes
    Parameters
    ----------
        filename: str
            String of JSON file name and file type
    Returns
    -------
        List[Dict[str, float]]
            list of dictionaries containing latitude, longitude, radius, and height of obstacles
    """
    with open(filename, 'r') as f:
        data_set: Dict[str, List] = json.load(f)

    stationary_obs: List[Dict[str, float]] = [obs for obs in data_set["stationaryObstacles"]]

    return stationary_obs


async def move_to(drone: System, latitude: float, longitude: float, altitude: float) -> None:
    """
    This function takes in a latitude, longitude and altitude and autonomously
    moves the drone to that waypoint. This function will also auto convert the altitude
    from feet to meters.

    Parameters
    ----------
    drone: System 
        a drone object that has all offboard data needed for computation
    latitude: float 
        a float containing the requested latittude to move to
    longitude: float 
        a float containing the requested longitude to move to
    altitude: float 
        a float contatining the requested altitude to go to (in feet)

    Returns
    -------
    None
    """
    

    #converts feet into meters
    altitude = altitude * .3048

    #get current altitude
    async for terrain_info in drone.telemetry.home():
        absolute_altitude: float = terrain_info.absolute_altitude_m
        break

    await drone.action.goto_location(latitude,longitude, altitude+absolute_altitude, 0)
    location_reached: bool=False

    #Loops until the waypoint is reached
    while(not location_reached):
        print("Going to waypoint")
        async for position in drone.telemetry.position():
            #continuously checks current latitude, longitude and altitude of the drone
            drone_lat: float=position.latitude_deg
            drone_long: float=position.longitude_deg
            drone_alt: float=position.relative_altitude_m

            #checks if location is reached and moves on if so
            if ((round(drone_lat,4)==round(latitude,4)) and 
                (round(drone_long,4)==round(longitude,4)) and 
                (round(drone_alt,1)==round(altitude,1))):
                location_reached=True
                print("arrived")
                break

        await asyncio.sleep(1)
    return


async def run() -> None:
    """
    This function is just a driver to test the goto function.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    #Put all latitudes, longitudes and altitudes into seperate arrays
    lats: List[float]=[]
    longs: List[float]=[]
    altitudes: List[float]=[]
    waypoints: List[Dict[str,float]] = waypoint_parsing("test_data.json")
    stationary_obs: List[Dict[str, float]] = stationary_obstacle_parsing("test_data.json")
    for i in waypoints:
        for key,val in i.items():
            if(key=="latitude"):
                lats.append(val)
            if(key=="longitude"):
                longs.append(val)
            if(key=="altitude"):
                altitudes.append(val)

    #create a drone object
    drone: System = System()
    await drone.connect(system_address="udp://:14540")

    #connect to the drone
    logging.info("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            logging.info("Drone discovered!")
            break

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok:
            logging.info("Global position estimate ok")
            break

    print("-- Arming")
    await drone.action.arm()

    print("-- Taking off")
    await drone.action.takeoff()

    #wait for drone to take off
    await asyncio.sleep(20)

    #move to each waypoint in mission
    for point in range(len(waypoints)):
        await move_to(drone,lats[point],longs[point],altitudes[point])

    #return home
    print("Last waypoint reached")
    print("Returning to home")
    await drone.action.return_to_launch()
    print("Staying connected, press Ctrl-C to exit")

    #infinite loop till forced disconnect
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())


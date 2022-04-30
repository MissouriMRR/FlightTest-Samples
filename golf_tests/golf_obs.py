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
import sys
from typing import Dict, List
from avoidance import rrt_flight_test


def boundary_parsing(filename: str) -> List[Dict[str, float]]:
    """
    Parses the json file for all mission-critical waypoints
    Args:
        filename (str): name of the json file

    Returns:
        Waypoint_Locs ([Dict[str,float]]): List of dictionaries containing
        a string identifier and float for lattitude, longitude and altitude
    """
    f = open(filename, )
    data_set = json.load(f)
    # print(data_set)
    f.close()

    boundary_Locs: List[Dict[str, float]] = []

    for i in range(0, len(data_set["boundaryPoints"])):
        boundary_Locs.append(data_set["boundaryPoints"][i])

    return boundary_Locs


def waypoint_parsing(filename: str) -> List[Dict[str, float]]:
    """
    Parses the json file for all mission-critical waypoints
    Args:
        filename (str): name of the json file

    Returns:
        Waypoint_Locs ([Dict[str,float]]): List of dictionaries containing
        a string identifier and float for lattitude, longitude and altitude
    """
    f = open(filename, )
    data_set = json.load(f)
    # print(data_set)
    f.close()

    waypoint_Locs: List[Dict[str, float]] = []

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
    with open(filename) as f:
        try:
            data_set: Dict[str, List] = json.load(f)
        except:
            f.close()
    f.close()

    stationary_obs: List[Dict[str, float]] = [obs for obs in data_set["stationaryObstacles"]]

    return stationary_obs


async def move_to(drone: System, latitude: float, longitude: float, altitude: float, fast_mode: bool) -> None:
    """
    This function takes in a latitude, longitude and altitude and autonomously
    moves the drone to that waypoint. This function will also auto convert the altitude
    from feet to meters.

    Parameters
    ----------
    drone: System 
        a drone object that has all offboard data needed for computation
    latitude: float 
        a float containing the requested latitude to move to
    longitude: float 
        a float containing the requested longitude to move to
    altitude: float 
        a float contatining the requested altitude to go to (in feet)
    fast_mode: bool
        a boolean that determines if the drone will take less time checking its precise location
        before moving on to another waypoint. If its true, it will move faster, if it is false,
        it will move at normal speed
    """

    #converts feet into meters
    altitude = altitude * .3048

    #get current altitude
    async for terrain_info in drone.telemetry.home():
        absolute_altitude: float = terrain_info.absolute_altitude_m
        break

    await drone.action.goto_location(latitude,longitude, altitude+absolute_altitude, 0)
    location_reached: bool=False
    #First determine if we need to move fast through waypoints or need to slow down at each one
    #Then loops until the waypoint is reached
    if (fast_mode==True):
        while(not location_reached):
            logging.info("Going to waypoint")
            async for position in drone.telemetry.position():
                #continuously checks current latitude, longitude and altitude of the drone
                drone_lat: float=position.latitude_deg
                drone_long: float=position.longitude_deg
                drone_alt: float=position.relative_altitude_m

                #roughly checks if location is reached and moves on if so
                if ((round(drone_lat,4)==round(latitude,4)) and 
                    (round(drone_long,4)==round(longitude,4))):
                    location_reached=True
                    logging.info("arrived")
                    break

            #tell machine to sleep to prevent contstant polling, preventing battery drain
            await asyncio.sleep(1)
    else:
        while(not location_reached):
            logging.info("Going to waypoint")
            async for position in drone.telemetry.position():
                #continuously checks current latitude, longitude and altitude of the drone
                drone_lat: float=position.latitude_deg
                drone_long: float=position.longitude_deg
                drone_alt: float=position.relative_altitude_m

                #accurately checks if location is reached and moves on if so
                if ((round(drone_lat,6)==round(latitude,6)) and 
                    (round(drone_long,6)==round(longitude,6)) and 
                    (round(drone_alt,1)==round(altitude,1))):
                    location_reached=True
                    logging.info("arrived")
                    break

            #tell machine to sleep to prevent contstant polling, preventing battery drain 
            await asyncio.sleep(1)
    return


async def run() -> None:
    """
    This function is just a driver to test the goto function
    """
    #Prints out logging statements and records them
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Put all latitudes, longitudes and altitudes into seperate arrays
    lats: List[float] = []
    longs: List[float] = []
    altitudes: List[float] = []
    waypoints: List[Dict[str, float]] = waypoint_parsing("golf_data.json")
    stationary_obs: List[Dict[str, float]] = stationary_obstacle_parsing("golf_data.json")
    boundary: List[Dict[str, float]] = boundary_parsing("golf_data.json")
    new_path = rrt_flight_test.rrt_flight_test(stationary_obs, waypoints, boundary)
    for i in waypoints:
        for key, val in i.items():
            if (key == "latitude"):
                lats.append(val)
            if (key == "longitude"):
                longs.append(val)
            if (key == "altitude"):
                altitudes.append(val)

    # create a drone object
    drone: System = System()
    await drone.connect(system_address="udp://:14540")

    # connect to the drone
    logging.info("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            logging.info("Drone discovered!")
            break

    logging.info("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok:
            logging.info("Global position estimate ok")
            break

    logging.info("-- Arming")
    await drone.action.arm()

    logging.info("-- Taking off")
    await drone.action.takeoff()

    # wait for drone to take off
    await asyncio.sleep(10)

    # move to each waypoint in mission
    i=0
    for point in new_path:
        await move_to(drone, point[0], point[1], 100, False)
        i=i+1

    # return home
    logging.info("Last waypoint reached")
    logging.info("Returning to home")
    await drone.action.return_to_launch()
    logging.info("Staying connected, press Ctrl-C to exit")

    # infinite loop till forced disconnect
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    #Main driver of drone
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        print("Program ended")
        sys.exit(0)

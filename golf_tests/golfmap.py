"""
Main driver code for moving drone to each waypoint
"""

import asyncio
from mavsdk import System
import mavsdk as sdk
import logging
import sys
from typing import Dict, List, Tuple
from mapping import map_functions


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

    # converts feet into meters
    altitude = altitude * .3048

    # get current altitude
    async for terrain_info in drone.telemetry.home():
        absolute_altitude: float = terrain_info.absolute_altitude_m
        break

    await drone.action.goto_location(latitude, longitude, altitude + absolute_altitude, 0)
    location_reached: bool = False
    # First determine if we need to move fast through waypoints or need to slow down at each one
    # Then loops until the waypoint is reached
    if (fast_mode == True):
        while (not location_reached):
            logging.info("Going to waypoint")
            async for position in drone.telemetry.position():
                # continuously checks current latitude, longitude and altitude of the drone
                drone_lat: float = position.latitude_deg
                drone_long: float = position.longitude_deg
                drone_alt: float = position.relative_altitude_m

                # roughly checks if location is reached and moves on if so
                if ((round(drone_lat, 4) == round(latitude, 4)) and
                        (round(drone_long, 4) == round(longitude, 4))):
                    location_reached = True
                    logging.info("arrived")
                    break

            # tell machine to sleep to prevent contstant polling, preventing battery drain
            await asyncio.sleep(1)
    else:
        while (not location_reached):
            logging.info("Going to waypoint")
            async for position in drone.telemetry.position():
                # continuously checks current latitude, longitude and altitude of the drone
                drone_lat: float = position.latitude_deg
                drone_long: float = position.longitude_deg
                drone_alt: float = position.relative_altitude_m

                # accurately checks if location is reached and moves on if so
                if ((round(drone_lat, 6) == round(latitude, 6)) and
                        (round(drone_long, 6) == round(longitude, 6)) and
                        (round(drone_alt, 1) == round(altitude, 1))):
                    location_reached = True
                    logging.info("arrived")
                    break

            # tell machine to sleep to prevent contstant polling, preventing battery drain
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

    # Prints out logging statements and records them
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Set map center, height & camera focal length
    lat: float = 37.9481747
    long: float = -91.7833502
    map_height: float = 600.0
    altitude: int = 150
    focal_length: int = 9

    # Generate waypoints to fly through for mapping
    map_path: List[Tuple[float, float]] = map_functions.map(((lat, long), map_height), altitude, focal_length)

    # create a drone object
    drone: System = System()
    await drone.connect(system_address="serial:///dev/ttyUSB0:921600")

    # Drone configurations
    await drone.action.set_maximum_speed(20)

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

    # Mapping Flight Path
    for point in map_path:
        await move_to(drone, point[0], point[1], altitude, False)

    # return home
    logging.info("Last waypoint reached")
    logging.info("Returning to home")
    await drone.action.return_to_launch()
    logging.info("Staying connected, press Ctrl-C to exit")

    # infinite loop till forced disconnect
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    # Main driver of drone
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        print("Program ended")
        sys.exit(0)
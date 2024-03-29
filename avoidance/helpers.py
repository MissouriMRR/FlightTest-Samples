from typing import Tuple
import utm
from shapely.geometry import Point, Polygon
from typing import List, Dict


def latlon_to_utm(coords: dict) -> dict:
    """
    Converts latlon coordinates to utm coordinates and adds the data to the dictionary
    Args:
        coords (dict): A dictionary containing lat long coordinates
    Returns:
        dict: An updated dictionary with additional keys and values with utm data
    """
    utm_coords = utm.from_latlon(coords["latitude"], coords["longitude"])
    coords["utm_x"] = utm_coords[0]
    coords["utm_y"] = utm_coords[1]
    coords["utm_zone_number"] = utm_coords[2]
    coords["utm_zone_letter"] = utm_coords[3]
    return coords


def all_latlon_to_utm(list_of_coords: List[Dict[float, float]]) -> List[Dict[float, float]]:
    """
    Converts a list of dictionarys with latlon data to add utm data
    Args:
        list_of_coords (list[dict]): A list of dictionaries that contain lat long data
    Returns:
        list[dict]: An updated list of dictionaries with added utm data
    """
    for i in range(len(list_of_coords)):
        list_of_coords[i] = latlon_to_utm(list_of_coords[i])
    return list_of_coords


def coords_to_shape(coords):
    poly_coords = [(point["utm_x"], point["utm_y"]) for point in coords]
    shape = Polygon(poly_coords)
    return shape


def circles_to_shape(circles):
    circle_shapes = []
    for circle in circles:
        x = circle["utm_x"]
        y = circle["utm_y"]
        radius = circle["radius"]
        circle_shape = Point(x, y).buffer(radius).boundary
        circle_shapes.append(circle_shape)
    return circle_shapes


def coords_to_points(coords):
    points = []
    for coord in coords:
        points.append(Point(coord["utm_x"], coord["utm_y"]))
    return points


def all_feet_to_meters(obstacles):
    for obstacle in obstacles:
        obstacle["radius"] *= 0.3048  # covert feet to meters
    return obstacles


def path_to_latlon(path, zone_num, zone_char):
    gps_path = []
    for point in path:
        gps_path.append(utm.to_latlon(point.x, point.y, zone_num, zone_char))
    return gps_path


def get_zone_info(boundary):
    # todo handle multiple zones
    return boundary[0]["utm_zone_number"], boundary[0]["utm_zone_letter"]
from avoidance import rrt
from avoidance import helpers
from avoidance import plotter
import time
from typing import Dict, List

flyZones = {
    "altitudeMin": 100.0,
    "altitudeMax": 750.0,
    "boundaryPoints": [
        {"latitude": 38.1462694444444, "longitude": -76.4281638888889},
        {"latitude": 38.151625, "longitude": -76.4286833333333},
        {"latitude": 38.1518888888889, "longitude": -76.4314666666667},
        {"latitude": 38.1505944444444, "longitude": -76.4353611111111},
        {"latitude": 38.1475666666667, "longitude": -76.4323416666667},
        {"latitude": 38.1446666666667, "longitude": -76.4329472222222},
        {"latitude": 38.1432555555556, "longitude": -76.4347666666667},
        {"latitude": 38.1404638888889, "longitude": -76.4326361111111},
        {"latitude": 38.1407194444444, "longitude": -76.4260138888889},
        {"latitude": 38.1437611111111, "longitude": -76.4212055555556},
        {"latitude": 38.1473472222222, "longitude": -76.4232111111111},
        {"latitude": 38.1461305555556, "longitude": -76.4266527777778},
        {"latitude": 38.1462694444444, "longitude": -76.4281638888889},
    ],
}

waypoints = [
    {"latitude": 38.1446916666667, "longitude": -76.4279944444445, "altitude": 200.0},
    {"latitude": 38.1461944444444, "longitude": -76.4237138888889, "altitude": 300.0},
    {"latitude": 38.1438972222222, "longitude": -76.42255, "altitude": 400.0},
    {"latitude": 38.1417722222222, "longitude": -76.4251083333333, "altitude": 400.0},
    {"latitude": 38.14535, "longitude": -76.428675, "altitude": 300.0},
    {"latitude": 38.1508972222222, "longitude": -76.4292972222222, "altitude": 300.0},
    {"latitude": 38.1514944444444, "longitude": -76.4313833333333, "altitude": 300.0},
    {"latitude": 38.1505333333333, "longitude": -76.434175, "altitude": 300.0},
    {"latitude": 38.1479472222222, "longitude": -76.4316055555556, "altitude": 200.0},
    {"latitude": 38.1443333333333, "longitude": -76.4322888888889, "altitude": 200.0},
    {"latitude": 38.1433166666667, "longitude": -76.4337111111111, "altitude": 300.0},
    {"latitude": 38.1410944444444, "longitude": -76.4321555555556, "altitude": 400.0},
    {"latitude": 38.1415777777778, "longitude": -76.4252472222222, "altitude": 400.0},
    {"latitude": 38.1446083333333, "longitude": -76.4282527777778, "altitude": 200.0},
]

obstacles = [
    {"latitude": 38.146689, "longitude": -76.426475, "radius": 150.0, "height": 750.0},
    {"latitude": 38.142914, "longitude": -76.430297, "radius": 300.0, "height": 300.0},
    {"latitude": 38.149504, "longitude": -76.43311, "radius": 100.0, "height": 750.0},
    {"latitude": 38.148711, "longitude": -76.429061, "radius": 300.0, "height": 750.0},
    {"latitude": 38.144203, "longitude": -76.426155, "radius": 50.0, "height": 400.0},
    {"latitude": 38.146003, "longitude": -76.430733, "radius": 225.0, "height": 500.0},
]


def rrt_flight_test(obstacles: List[Dict[str, float]], waypoints: List[Dict[str, float]],
                    boundary: List[Dict[str, float]]):
    
    # Add utm coordinates to all
    boundary = helpers.all_latlon_to_utm(boundary)
    obstacles = helpers.all_latlon_to_utm(obstacles)
    waypoints = helpers.all_latlon_to_utm(waypoints)
    
    # print(obstacles)
    # print(waypoints)
    # print(boundary)

    zone_num = helpers.get_zone_info(boundary)

    # Convert silly units to proper units
    obstacles = helpers.all_feet_to_meters(obstacles)

    # Create shapely representations of everything for use in algorithm
    boundary_shape = helpers.coords_to_shape(boundary)
    obstacle_shapes = helpers.circles_to_shape(obstacles)
    waypoints_points = helpers.coords_to_points(waypoints)
    
    # plotter.plot(obstacles, boundary, path=waypoints_points)

    final_route = []

    start_time_final_route = time.time()

    # run rrt on each pair of waypoints
    for i in range(len(waypoints_points) - 1):
        print(f"finding path between waypoints {i} and {i+1}")
        start = waypoints_points[i]
        goal = waypoints_points[i + 1]
        start_time = time.time()
        G, ellr, informed_boundary = rrt.RRT_star(start, goal, boundary_shape, obstacle_shapes)
        print(f"rrt runtime = {(time.time()-start_time):.3f}s")

        if G.success:
            path = rrt.dijkstra(G)
            path = rrt.relax_path(path, obstacle_shapes)
            for p in path:
                final_route.append(p)
        else:
            print("major error! could not find a path!")
    
    print(f"Total solving runtime = {(time.time()-start_time_final_route):.3f}s")
    
    # plotter.plot(obstacles, boundary, path=final_route)
    
    # last step converting back to lat lon
    final_route = helpers.path_to_latlon(final_route, zone_num)

    print(final_route)
    
    return final_route

from references import parameters as para
from utility_functions import geometrical_functions as g_f
from references import global_variables as g_v

import time

WEIGHT_OF_ANGLE_SCOUT = para.WEIGHT_OF_ANGLE_SCOUT
BIAS_OF_ANGLE_SCOUT = para.BIAS_OF_ANGLE_SCOUT
WEIGHT_OF_DISTANCE_SCOUT = para.WEIGHT_OF_DISTANCE_SCOUT
BIAS_OF_DISTANCE_SCOUT = para.BIAS_OF_DISTANCE_SCOUT
WEIGHT_OF_ANGLE_OFF = para.WEIGHT_OF_ANGLE_OFF
BIAS_OF_ANGLE_OFF = para.BIAS_OF_ANGLE_OFF
WEIGHT_OF_DISTANCE_OFF = para.WEIGHT_OF_DISTANCE_OFF
BIAS_OF_DISTANCE_OFF = para.BIAS_OF_DISTANCE_OFF
FRAMES_PER_SECOND = para.FRAMES_PER_SECOND

SLEEP_THREADS = para.SLEEP_THREADS


def cover(waypoint_array, plane_pos, off_axis=False):
    """Finds a path that covers all waypoints in list on a map"""
    t5 = time.time()
    initial_array_size = len(waypoint_array)

    path = list()
    cell_array = [way.pos for way in waypoint_array]
    if len(waypoint_array) == 0:
        return path

    # start with an edge
    if plane_pos is not None:
        last_pos_2 = plane_pos
        edge_cells = list()
        min_x = min(cell.pos[0] for cell in waypoint_array)
        max_x = max(cell.pos[0] for cell in waypoint_array)
        min_y = min(cell.pos[1] for cell in waypoint_array)
        max_y = max(cell.pos[1] for cell in waypoint_array)

        def check_edge(x):
            f_q = g_f.float_eq
            return (f_q(x[0], min_x) or f_q(x[0], max_x)
                    or f_q(x[1], min_y) or f_q(x[1], max_y))

        edge_cells.extend(filter(check_edge, cell_array))
        dis = g_f.distance_2d
        last_pos = min(edge_cells, key=lambda x: dis(x, plane_pos))

    else:
        last_pos = min(cell_array, key=lambda x: x[0])
        last_pos_2 = last_pos

    start_time = time.time()

    # add closest cell to list of cells to travel
    # then delete it from array
    index = 0
    len_array = len(waypoint_array)
    while index < len_array:

        if SLEEP_THREADS:
            # sleep to allow other threads to run
            if (time.time() - start_time) > 0.4 / FRAMES_PER_SECOND:
                time.sleep(1/FRAMES_PER_SECOND)
            start_time = time.time()

        # update screen percentage
        completion = 100 * (index/initial_array_size)
        g_v.gui.layers["system status"].cover_percentage = completion

        # pre-check before full cell cost computation
        found_cell = False
        next_cell = None
        extra = []
        # if index > 0 and not off_axis:
        #
        #     # if they have the two previous cells
        #     # have the same y position
        #     if g_f.float_eq(last_pos[1], last_pos_2[1]):
        #
        #         # get cells with same y pos
        #         sub_array = filter(
        #             lambda x: g_f.float_eq(last_pos[1], x.pos[1]), waypoint_array)
        #         # get the ones that are on the side of
        #         # the current cell in the x direction
        #         if last_pos[0] > last_pos_2[0]:
        #             sub_array_2 = list(filter(
        #                 lambda x: x.pos[0] > last_pos[0], sub_array))
        #             # get the closest one
        #             if len(sub_array_2) > 0:
        #                 sub_array_2.sort(key=lambda x: x.pos[0])
        #                 extra = sub_array_2
        #                 found_cell = True
        #         else:
        #             sub_array_2 = list(filter(
        #                 lambda x: x.pos[0] < last_pos[0], sub_array))
        #             # get the closest one
        #             if len(sub_array_2) > 0:
        #                 sub_array_2.sort(key=lambda x: x.pos[0], reverse=True)
        #                 extra = sub_array_2
        #                 found_cell = True
        #
        #     # if they have the two previous cells have the same x position
        #     if g_f.float_eq(last_pos[0], last_pos_2[0]):
        #         # get cells with same x pos
        #         sub_array = filter(lambda x: g_f.float_eq(
        #             last_pos[0], x.pos[0]), waypoint_array)
        #         # get the ones that are on the side of the
        #         # current cell in the y direction
        #         if last_pos[1] > last_pos_2[1]:
        #             sub_array_2 = list(filter(
        #                 lambda x: x.pos[1] > last_pos[1], sub_array))
        #             # get the closest one
        #             if len(sub_array_2) > 0:
        #                 sub_array_2.sort(key=lambda x: x.pos[1])
        #                 extra = sub_array_2
        #                 found_cell = True
        #         else:
        #             sub_array_2 = list(filter(
        #                 lambda x: x.pos[1] < last_pos[1], sub_array))
        #             # get the closest one
        #             if len(sub_array_2) > 0:
        #                 sub_array_2.sort(key=lambda x: x.pos[1], reverse=True)
        #                 extra = sub_array_2
        #                 found_cell = True
        #
        #     if not found_cell:
        #         def check_cross(p1, p2, p):
        #             if p2[0] > p1[0] and p1[0] < p[0]:
        #                 return False
        #             if p2[1] > p1[1] and p1[1] < p[1]:
        #                 return False
        #             c1 = (p[1] - p1[1]) * (p2[0] - p1[0])
        #             c2 = (p2[1] - p1[1]) * (p[0] - p1[0])
        #             g_f.float_eq(c1 - c2, 0)
        #
        #         # get cells with same movement ratio
        #         sub_array = list(filter(lambda x: check_cross(
        #             last_pos, x.pos, last_pos_2), waypoint_array))
        #         # get the ones that are on the side of the
        #         # current cell in the x direction
        #         if len(sub_array) > 0:
        #
        #             # filter to only keep the cells with
        #             # the right positioning
        #             if last_pos[0] > last_pos_2[0]:
        #                 sub_array_2 = list(filter(
        #                     lambda x: x.pos[0] > last_pos[0], sub_array))
        #                 # get the closest one
        #                 if len(sub_array_2) > 0:
        #                     sub_array_2.sort(key=lambda x: x.pos[0])
        #                     extra = sub_array_2
        #                     found_cell = True
        #             else:
        #                 sub_array_2 = list(filter(
        #                     lambda x: x.pos[0] < last_pos[0], sub_array))
        #                 # get the closest one
        #                 if len(sub_array_2) > 0:
        #                     sub_array_2.sort(key=lambda x: x.pos[0], reverse=True)
        #                     extra = sub_array_2
        #                     found_cell = True

        # add all extra elements
        for element in extra:
            path.append(element)
            waypoint_array.remove(element)
            last_pos_2 = last_pos
            last_pos = element.pos
            index += 1

        if len(waypoint_array) == 0:
            break

        # full cell cost computation
        next_cell = min(waypoint_array, key=lambda x: cell_cost(
            last_pos_2, last_pos, x.pos, off_axis))

        path.append(next_cell)
        waypoint_array.remove(next_cell)
        last_pos_2 = last_pos
        last_pos = next_cell.pos
        index += 1

    print(time.time() - t5)
    return path


def cell_cost(cell_0, cell_1, cell_2, off_axis):
    """Finds the 'cost' of going into a cell
    considering the two previous cells"""

    if not off_axis:
        a = WEIGHT_OF_ANGLE_SCOUT
        b = BIAS_OF_ANGLE_SCOUT
        c = WEIGHT_OF_DISTANCE_SCOUT
        d = BIAS_OF_DISTANCE_SCOUT
    else:
        a = WEIGHT_OF_ANGLE_OFF
        b = BIAS_OF_ANGLE_OFF
        c = WEIGHT_OF_DISTANCE_OFF
        d = BIAS_OF_DISTANCE_OFF

    cell_0 = cell_0
    cell_1 = cell_1
    cell_2 = cell_2

    distance_to_cell = g_f.distance_2d(cell_1, cell_2)

    cell_0_to_1 = g_f.sub_vectors(cell_1, cell_0)
    cell_1_to_2 = g_f.sub_vectors(cell_2, cell_1)

    if (g_f.float_eq_2d(cell_0_to_1, (0, 0))
            or g_f.float_eq_2d(cell_1_to_2, (0, 0))):
        angle_change = 0
    else:
        angle_change = g_f.find_angle(cell_0_to_1, cell_1_to_2)

    return (a * abs(angle_change) + c) * (b * distance_to_cell + d)

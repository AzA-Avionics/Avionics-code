from avionics_code.helpers import geometrical_functions as g_f, parameters as para
from avionics_code.helpers import global_variables as g_v

import pygame
import os
import time
import threading

DASHBOARD_SIZE = para.DASHBOARD_SIZE
WAYPOINT_SIZE = para.WAYPOINT_SIZE * (DASHBOARD_SIZE / 650)
FRAMES_PER_SECOND = para.FRAMES_PER_SECOND


def gui_input_manager_loop(g_u_i):
    """Check for interface inputs and update the mission profile"""

    d_m_s = g_u_i.default_map_scaling

    last_time = time.time()
    while True:
        # keep the frame rate under or equal to FRAMES_PER_SECOND
        new_time = time.time()
        time.sleep(abs(1/FRAMES_PER_SECOND - (new_time - last_time)))
        last_time = time.time()

        # check interface inputs
        for event in pygame.event.get():
            # if the user starts clicking, add the object or delete
            # the object they want, or record their input
            if event.type == pygame.MOUSEBUTTONDOWN:
                # get position of the cursor
                cur_pos = pygame.mouse.get_pos()
                cursor_on_map = g_u_i.map_projection(cur_pos)

                # for moving screen
                if g_u_i.input_type == -1:
                    if not g_u_i.moving_map:
                        g_u_i.moving_map = True
                        g_u_i.input_position = g_u_i.screen_center
                        g_u_i.input_position_2 = cur_pos

                # Check if the user is selecting a certain object type
                # to input (left click) or trying to delete all instances
                # of the object type (right click), or changing display mode
                d_s = DASHBOARD_SIZE
                dict1 = g_u_i.input_type_dict
                dict3 = g_u_i.mission_state_display_dict
                # reversed dictionaries to check which buttons has what type or what status
                input_type_dict_rev = {dict1[key]: key for key in dict1}
                mission_state_display_dict_rev = {dict3[key]: key for key in dict3}

                # left click actions for buttons
                left_button_actions = {
                    "Generate button": g_v.ms.launch_generate,
                    "Compute button": g_v.mc.launch_compute_path,
                    "Upload mission button": g_v.rf.launch_upload_mission,
                    "Start mission button": g_v.rf.launch_start_mission,
                    "Pause mission button": g_v.rf.launch_pause_mission,
                    "land button": g_v.mc.land_request,
                    #"drop authorization button": g_v.rf.authorize_airdrop
                }

                # right click actions for buttons
                right_button_actions = {
                    "Waypoint button": g_v.mp.clear_waypoints,
                    "Obstacle button": g_v.mp.clear_obstacles,
                    "Border button": g_v.mp.clear_border,
                    "Search area button": g_v.mp.clear_search,
                    "Airdrop button": g_v.mp.clear_airdrop,
                    "Airdrop goal button": g_v.mp.clear_airdrop_goal,
                    "lost comms button": g_v.mp.clear_lostcomms,
                    "Off axis obj button": g_v.mp.clear_offaxis_obj,
                    "Emergent obj button": g_v.mp.clear_emergent_obj,
                    "Mapping area button": g_v.mp.clear_mapping_area,
                }

                # Check that cursor in in the control panel
                if cur_pos[0] > d_s:
                    g_u_i.inputing = 0

                    # run over all buttons to check if one was click
                    for key in g_u_i.buttons:
                        button = g_u_i.buttons[key]
                        button_pos = (d_s * button[1], button[2] * d_s / 15)
                        # check if the cursor is inside the button
                        if g_f.distance_2d(cur_pos, button_pos) < (button[3] * WAYPOINT_SIZE):
                            # check for left click
                            if pygame.mouse.get_pressed()[0]:
                                # change input type if the button does that
                                if key in input_type_dict_rev.keys():
                                    if g_u_i.input_type != input_type_dict_rev[key]:
                                        g_u_i.input_type = input_type_dict_rev[key]
                                    else:
                                        g_u_i.input_type = -1
                                    g_u_i.to_draw["user interface"] = True
                                # change mission state input type if there is one
                                if key in mission_state_display_dict_rev.keys():
                                    index = mission_state_display_dict_rev[key]
                                    var = g_u_i.mission_state_display[index]
                                    g_u_i.mission_state_display[index] = (var + 1) % 2
                                    g_u_i.to_draw["user interface"] = True
                                    g_u_i.to_draw["mission profile"] = True
                                    g_u_i.to_draw["mission state"] = True
                                    g_u_i.to_draw["path"] = True
                                # do a left click actions if the button has one
                                if key in left_button_actions.keys():
                                    left_button_actions[key]()
                            # or else right click
                            elif pygame.mouse.get_pressed()[2]:
                                # do a right click actions if the button has one
                                if key in right_button_actions.keys():
                                    if key in input_type_dict_rev.keys():
                                        if g_u_i.is_displayed[input_type_dict_rev[key]] == 1:
                                            right_button_actions[key]()
                                    else:
                                        right_button_actions[key]()
                            # or middle click
                            elif pygame.mouse.get_pressed()[1]:
                                if key in input_type_dict_rev.keys():
                                    g_u_i.is_displayed[input_type_dict_rev[key]] += 1
                                    g_u_i.is_displayed[input_type_dict_rev[key]] %= 2
                                    g_u_i.to_draw["mission profile"] = True

                # if the user is not interacting with the input menu,
                # then add whatever they want to input (left click)
                # or delete whatever they are trying to
                # delete (right click)
                else:
                    # check if the user is using the mouse wheel

                    # wheel up
                    old_scale = g_u_i.map_scaling
                    if event.button == 4:
                        g_u_i.map_scaling *= 4/3
                        g_u_i.map_scaling = min(g_u_i.map_scaling, d_m_s * ((4/3) ** 5))
                    # wheel down
                    elif event.button == 5:
                        g_u_i.map_scaling *= 3/4
                        g_u_i.map_scaling = max(g_u_i.map_scaling, d_m_s)

                    if event.button == 4 or event.button == 5:
                        new_scale = g_u_i.map_scaling
                        diff = old_scale - new_scale

                        new_cen_x = g_u_i.screen_center[0] + cursor_on_map[0] * diff
                        new_cen_y = g_u_i.screen_center[1] - cursor_on_map[1] * diff

                        scaling_ratio = g_u_i.zoom()
                        new_map_size = DASHBOARD_SIZE * scaling_ratio

                        new_x = max(new_cen_x, DASHBOARD_SIZE - new_map_size / 2)
                        new_x = min(new_x, + new_map_size / 2)
                        new_y = max(new_cen_y, DASHBOARD_SIZE - new_map_size / 2)
                        new_y = min(new_y, + new_map_size / 2)

                        g_u_i.screen_center = (new_x, new_y)

                        for key in g_u_i.to_draw:
                            g_u_i.to_draw[key] = True
                    # to check if the user is clicking on the map with nothing
                    # on its way (need nothing in the way
                    # to create an obstacle/waypoint/border vertex)
                    contact = False

                    # dictionary of map_objects that can be interacted with in the map
                    map_objects_dict = {
                        0: g_v.mp.mission_waypoints,
                        1: g_v.mp.obstacles,
                        2: g_v.mp.border.vertices,
                        3: g_v.mp.search_area.vertices
                    }
                    W_S = WAYPOINT_SIZE * g_u_i.zoom()
                    s = g_u_i.selection
                    gen1 = range(len(g_v.mp.mission_waypoints))
                    gen2 = range(len(g_v.mp.border.vertices))
                    gen3 = range(len(g_v.mp.search_area.vertices))
                    map_objects_size_dict = {
                        0: [W_S * (1.5 if (s[0] == i or s[0] == (i - 1) % len(gen1)) else 1) for i in gen1],
                        1: [o.r * g_u_i.map_scaling for o in g_v.mp.obstacles],
                        2: [W_S * (1.5 if (s[2] == i or s[2] == (i - 1) % len(gen2)) else 1) for i in gen2],
                        3: [W_S * (1.5 if (s[2] == i or s[2] == (i - 1) % len(gen3)) else 1) for i in gen3]
                    }
                    # dictionary of functions to delete those map_objects
                    delete_func_dict = {
                        0: lambda x: g_v.mp.delete_waypoint(x),
                        1: lambda x: g_v.mp.delete_obstacle(x),
                        2: lambda x: g_v.mp.delete_border_vertex(x),
                        3: lambda x: g_v.mp.delete_search_vertex(x)
                    }
                    # go over all map objects that can be interacted with
                    for delete_type in range(4):
                        # get the list of map objects
                        map_objects = map_objects_dict[delete_type]
                        i = 0
                        # iterate over list of map objects
                        while i < len(map_objects):
                            map_object_dash_xy = g_u_i.dashboard_projection(map_objects[i])
                            cursor_to_map_object = g_f.distance_2d(cur_pos, map_object_dash_xy)
                            # check if cursor is inside map object
                            if cursor_to_map_object < map_objects_size_dict[delete_type][i]:
                                contact = True
                                # select object
                                d_t = delete_type
                                if pygame.mouse.get_pressed()[0]:
                                    if g_u_i.input_type == d_t and g_u_i.is_displayed[d_t] == 1:
                                        g_u_i.selection[d_t] = i % max(len(map_objects), 1)
                                    i += 1
                                # delete object
                                elif pygame.mouse.get_pressed()[2]:
                                    if g_u_i.input_type == d_t and g_u_i.is_displayed[d_t] == 1:
                                        delete_func_dict[d_t](i)
                                        g_u_i.selection[d_t] -= 1
                                        g_u_i.selection[d_t] %= max(len(map_objects), 1)
                                    else:
                                        i += 1
                                else:
                                    i += 1
                            else:
                                i += 1
                    # if the user is click on the map, add the object they want to add
                    if not contact and pygame.mouse.get_pressed()[0]:

                        # add waypoint
                        if g_u_i.input_type == 0 and g_u_i.is_displayed[0] == 1:
                            mission_waypoints = g_v.mp.mission_waypoints
                            a_b = g_u_i.altitude_box
                            g_v.mp.add_waypoint(g_u_i.selection[0] + 1, cursor_on_map, a_b)
                            g_u_i.selection[0] += 1
                            g_u_i.selection[0] %= max(1, len(mission_waypoints))
                            if len(mission_waypoints) == 2:
                                g_u_i.selection[0] = 1

                        # start inputing of obstacle
                        elif g_u_i.input_type == 1 and g_u_i.is_displayed[1] == 1:
                            g_u_i.inputing = 1
                            g_u_i.input_position = cur_pos

                        # add border vertex
                        elif g_u_i.input_type == 2 and g_u_i.is_displayed[2] == 1:
                            vertices = g_v.mp.border.vertices
                            g_v.mp.add_border_vertex(g_u_i.selection[2] + 1, cursor_on_map)
                            g_u_i.selection[2] += 1
                            g_u_i.selection[2] %= max(1, len(vertices))
                            if len(vertices) == 2:
                                g_u_i.selection[2] = 1

                        # add search border vertex
                        elif g_u_i.input_type == 3 and g_u_i.is_displayed[3] == 1:
                            vertices = g_v.mp.search_area.vertices
                            g_v.mp.add_search_vertex(g_u_i.selection[3] + 1, cursor_on_map)
                            g_u_i.selection[3] += 1
                            g_u_i.selection[3] %= max(1, len(vertices))
                            if len(vertices) == 2:
                                g_u_i.selection[3] = 1

                        # change location of airdrop position
                        elif g_u_i.input_type == 4 and g_u_i.is_displayed[4] == 1:
                            g_v.mp.set_airdrop(cursor_on_map)

                        # change location of airdrop goal
                        elif g_u_i.input_type == 5 and g_u_i.is_displayed[5] == 1:
                            g_v.mp.set_airdrop_goal(cursor_on_map)

                        # change location of lost comms position
                        elif g_u_i.input_type == 6 and g_u_i.is_displayed[6] == 1:
                            g_v.mp.set_lostcomms(cursor_on_map)

                        # change location of off axis object position
                        elif g_u_i.input_type == 7 and g_u_i.is_displayed[7] == 1:
                            g_v.mp.set_offaxis_obj(cursor_on_map)

                        # change location of emergent object last known position
                        elif g_u_i.input_type == 8 and g_u_i.is_displayed[8] == 1:
                            g_v.mp.set_emergent_obj(cursor_on_map)

                        # change map area by inputing the top and bottom point
                        elif g_u_i.input_type == 9 and g_u_i.is_displayed[9] == 1:
                            if g_u_i.inputing == 0:
                                g_u_i.inputing = 1
                                g_u_i.input_position = cursor_on_map
                            else:
                                g_u_i.inputing = 0
                                g_v.mp.set_mapping_area(g_u_i.input_position, cursor_on_map)

                        # change map area by inputing the top and bottom point
                        elif g_u_i.input_type == 10:
                            map_pos = g_u_i.map_projection(cur_pos)
                            g_v.rf.launch_go_to(map_pos, g_u_i.altitude_box)

            # When user releases click, add the input made to map info if it was an obstacle
            elif event.type == pygame.MOUSEBUTTONUP:
                # stop moving map
                if g_u_i.moving_map:
                    g_u_i.moving_map = False
                    g_u_i.input_position = None

                # shortcut for functions
                proj = g_u_i.map_projection
                # get cursor position
                cur_pos = pygame.mouse.get_pos()

                # if inputing obstacle, add it
                if g_u_i.inputing == 1 and g_u_i.input_type == 1:
                    g_u_i.inputing = 0
                    Dis = g_f.distance_2d(proj(g_u_i.input_position), proj(cur_pos))
                    if Dis > 10:
                        g_v.mp.add_obstacle((proj(g_u_i.input_position), Dis))

            # When user types altitude
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    g_u_i.altitude_box = float(int(g_u_i.altitude_box/10))
                    g_u_i.to_draw["user interface"] = True
                else:
                    if event.unicode.isdigit():
                        g_u_i.altitude_box = 10 * g_u_i.altitude_box + int(event.unicode)
                        g_u_i.to_draw["user interface"] = True
            # Close dashboard if prompted to, and quit the program
            if event.type == pygame.QUIT:
                g_v.gui.close_request = True
                g_v.rf.close_request = True
                g_v.mc.close_request = True

                def closing():
                    time.sleep(1)
                    os._exit(1)

                threading.Thread(target=closing).start()

        if g_u_i.inputing == 1 and g_u_i.input_type == 1:
            g_u_i.to_draw["mission profile"] = True

        # check if map is being moved
        if g_u_i.moving_map:
            cur_pos = pygame.mouse.get_pos()
            diff = g_f.sub_vectors(cur_pos, g_u_i.input_position_2)
            new_x = g_u_i.input_position[0] + diff[0]
            new_y = g_u_i.input_position[1] + diff[1]

            scaling_ratio = g_u_i.zoom()
            new_map_size = DASHBOARD_SIZE * scaling_ratio
            new_x = max(new_x, DASHBOARD_SIZE - new_map_size/2)
            new_x = min(new_x, + new_map_size/2)
            new_y = max(new_y, DASHBOARD_SIZE - new_map_size/2)
            new_y = min(new_y, + new_map_size/2)

            g_u_i.screen_center = (new_x, new_y)

            for key in g_u_i.to_draw:
                g_u_i.to_draw[key] = True

        # updating the display by executing the drawing requests
        drawing_dict = {
            "user interface": g_u_i.draw_user_interface,
            "system status": g_u_i.draw_system_status,
            "mission profile": g_u_i.draw_mission_profile,
            "mission state": g_u_i.draw_mission_state,
            "telemetry": g_u_i.draw_telemetry,
            "path": g_u_i.draw_path,
        }
        to_draw = g_u_i.to_draw
        drawing_needed = False
        # check if a drawing request is active
        for key in to_draw:
            if to_draw[key] or g_u_i.moving_map:
                to_draw[key] = False
                drawing_dict[key]()
                drawing_needed = True
        # if any requests were executed, update display
        if drawing_needed:
            g_u_i.display_update()
        pygame.display.update()
        if g_u_i.close_request:
            with open("extra files/settings.txt", "w") as file:
                for i in range(len(g_u_i.mission_state_display)):
                    file.write(str(g_u_i.mission_state_display[i]))
            pygame.quit()
            break

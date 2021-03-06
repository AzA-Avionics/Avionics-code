from communications import rf_communications as rf_c
from communications import server_communications as s_c
from mission import mission_control as m_c, mission_state as m_s, mission_profile as m_p
from avionics_gui import avionics_gui as a_g
from pygui import input_manager as i_m
from references import global_variables as g_v
from flight import telemetry_objects as t_o

import asyncio
import os
import threading


def main():
    """Launches the Avionics code"""

    try:
        """Graphical User Interface object that allows to visualize
        the progress of the mission along with adding info to the
        mission profile for testing purposes, or issuing drop authorizations
        and emergency landing orders for real missions"""
        g_v.gui = a_g.AvionicsGUI()

        """This Server communications object handles communication with
        the auvsi suas server. It downloads the mission info to make a
        mission profile, then keeps uploading telemetry. In the future,
        it must also upload deliverables of the Computer vision team
        and download other planes' telemetry"""
        g_v.sc = s_c.ServerComs()

        """This RF communications object handles communication with
        the plane's Pixhawk and ground vehicle. It downloads plane
        status information (position, velocity, attitude etc), and
        uploads the mission plan to the Pixhawk. It also has a loop 
        to call for the server comms to upload telemetry and the 
        mission controller to refresh the mission state or land
        if telemetry is not received."""
        g_v.rf = rf_c.RFComs(asyncio.get_event_loop())

        """This Mission profile object stores all the mission info
        provided by the competition's server (border, waypoint,
        obstacles, etc)."""
        g_v.mp = m_p.MissionProfile()

        """Mission state object storing the waypoints that the plane needs
        to go through in order to accomplish the entire mission (mission
        waypoints, UGV drop, scouting for pictures, etc). Has a generation
        function to generate these true mission waypoints along with
        landing functions in case of timeout or emergency that change
        the plan to landing"""
        g_v.ms = m_s.MissionState()

        """Mission control object that handles refreshing of mission state
        based on new plane status info, path recomputation/export and its
        conditions, along with timeout landing"""
        g_v.mc = m_c.MissionControl()

        """telemetry history list that keeps track of all the telemetry packages
        that are received from the pixhawk or plan"""
        g_v.th = t_o.TelemetryHistory()

        """initialization commands"""
        # activate GUI
        i_m.activate(g_v.gui)

        # connect to server
        g_v.sc.connect()
        # get mission from server
        g_v.sc.get_mission()

        # connect to pixhawk and subscribe to telemetry
        g_v.rf.launch_connect()

        # start plane controller
        g_v.mc.launch_controller()

        # run io loops
        asyncio.get_event_loop().run_forever()

    except KeyboardInterrupt:
        with threading.Lock():
            g_v.gui.save_settings()
            asyncio.get_event_loop().close()
            os._exit(0)


if __name__ == '__main__':
    # Start the main function
    main()

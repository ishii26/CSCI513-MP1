"""This file is the main controller file.

Here, you will design the controller for your for the adaptive cruise control system.
"""

from mp1_simulator.simulator import Observation, Mode

from typing import Tuple


# NOTE: Very important that the class name remains the same
class Controller:
    def __init__(self, distance_threshold: float):
        self.distance_threshold = distance_threshold

    def run_step(self, obs: Observation) -> Tuple[float, Mode]:
        """This is the main run step of the controller.

        Here, you will have to read in the observations `obs`, process it, and output an
        acceleration value and the operation mode.
        
        The acceleration value must be some value between -10.0 and 10.0.

        For the operation mode output True when "following" and False when "cruising".

        Note that the acceleration value is really some control input that is used
        internally to compute the throttle an brake values of the car.

        Below is some example code where the car just outputs the control value 10.0
        """

        ego_velocity = obs.ego_velocity
        desired_speed = obs.desired_speed
        dist_to_lead = obs.distance_to_lead

        # Do your magic...

        return (-10.0, Mode.FOLLOWING)

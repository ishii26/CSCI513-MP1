"""This file is the main controller file.

Here, you will design the controller for your for the adaptive cruise control system.
"""
#
#from mp1_simulator.simulator import Observation, Mode
#
#from typing import Tuple
#
#
## NOTE: Very important that the class name remains the same
#class Controller:
#    def __init__(self, distance_threshold: float):
#        self.distance_threshold = distance_threshold
#
#    def run_step(self, obs: Observation) -> Tuple[float, Mode]:
#        """This is the main run step of the controller.
#
#        Here, you will have to read in the observations `obs`, process it, and output an
#        acceleration value and the operation mode.
#        
#        The acceleration value must be some value between -10.0 and 10.0.
#
#        For the operation mode output True when "following" and False when "cruising".
#
#        Note that the acceleration value is really some control input that is used
#        internally to compute the throttle an brake values of the car.
#
#        Below is some example code where the car just outputs the control value 10.0
#        """
#
#        ego_velocity = obs.ego_velocity
#        desired_speed = obs.desired_speed
#        dist_to_lead = obs.distance_to_lead
#
#        # Do your magic...
#
#        return (-10.0, Mode.FOLLOWING)

"""Main controller for the adaptive cruise control system.

Work division:

Person 1:
- Implement CRUISING mode and speed-control logic.
- Design mode-switching logic with hysteresis.
- Analyze scenarios 1–5.
- Tune acceleration to satisfy reachTargetWhenNotFollowing.
- Review Person 2's FOLLOWING implementation.

Person 2:
- Implement FOLLOWING mode, safe-distance logic, and braking.
- Analyze scenarios 6–15.
- Tune braking and distance margins to satisfy safeFollowing.
- Review Person 1's CRUISING implementation.
"""

from typing import Tuple
import math

from mp1_simulator.simulator import Observation, Mode


# NOTE: The class name and method signatures must remain unchanged.
class Controller:
    def __init__(self, distance_threshold: float):
        self.distance_threshold = distance_threshold

        # Store the previous mode so mode switching can use hysteresis.
        self.current_mode = Mode.FOLLOWING

        # TODO (Person 1):
        # Tune these mode-switching margins.
        self.enter_following_distance = distance_threshold
        self.enter_cruising_distance = distance_threshold + 5.0

        # TODO (Person 1):
        # Add and tune parameters for cruise-speed control.
        self.cruise_kp = 1.0

        # TODO (Person 2):
        # Add and tune parameters for following and braking.
        self.following_speed_kp = 1.0
        self.distance_kp = 1.0

    def select_mode(self, dist_to_lead: float) -> Mode:
        """Select the operating mode using hysteresis.

        Person 1 owns the initial implementation of this method.
        Both team members should test and review its behavior.
        """

        # If the lead vehicle is no longer detected, cruise normally.
        if not math.isfinite(dist_to_lead):
            return Mode.CRUISING

        # Switch to FOLLOWING when the gap becomes sufficiently small.
        if self.current_mode == Mode.CRUISING:
            if dist_to_lead <= self.enter_following_distance:
                return Mode.FOLLOWING

        # Switch back to CRUISING only after the gap becomes sufficiently large.
        elif self.current_mode == Mode.FOLLOWING:
            if dist_to_lead >= self.enter_cruising_distance:
                return Mode.CRUISING

        return self.current_mode

    def cruising_control(
        self,
        ego_velocity: float,
        desired_speed: float,
    ) -> float:
        """Calculate the control input while cruising.

        Person 1:
        - Implement the cruise-speed controller.
        - Tune it to reach the desired speed quickly without instability.
        - Test reachTargetWhenNotFollowing.
        """

        speed_error = desired_speed - ego_velocity

        # TODO (Person 1): Replace or tune this initial proportional controller.
        acceleration = self.cruise_kp * speed_error

        return acceleration

    def following_control(
        self,
        ego_velocity: float,
        desired_speed: float,
        dist_to_lead: float,
    ) -> float:
        """Calculate the control input while following.

        Person 2:
        - Implement safe-distance control and braking.
        - Tune the distance margin and braking behavior.
        - Test safeFollowing and dontStopUnlessLeadStops.
        """

        distance_error = dist_to_lead - self.distance_threshold

        # TODO (Person 2):
        # Replace this placeholder with the following-mode controller.
        #
        # Possible inputs to consider:
        # - Distance error
        # - Ego velocity
        # - Desired speed
        # - Estimated closing rate, if stored across successive calls
        acceleration = (
            self.distance_kp * distance_error
            + self.following_speed_kp * (desired_speed - ego_velocity)
        )

        return acceleration

    @staticmethod
    def clamp_control(acceleration: float) -> float:
        """Restrict the controller output to the required range."""
        return max(-10.0, min(10.0, acceleration))

    def run_step(self, obs: Observation) -> Tuple[float, Mode]:
        """Process one observation and return the control input and mode.

        The returned control input must be between -10.0 and 10.0.
        """

        ego_velocity = obs.ego_velocity
        desired_speed = obs.desired_speed
        dist_to_lead = obs.distance_to_lead

        # Person 1 implements the initial mode-selection behavior.
        self.current_mode = self.select_mode(dist_to_lead)

        if self.current_mode == Mode.CRUISING:
            # Person 1 owns the initial implementation.
            acceleration = self.cruising_control(
                ego_velocity,
                desired_speed,
            )
        else:
            # Person 2 owns the initial implementation.
            acceleration = self.following_control(
                ego_velocity,
                desired_speed,
                dist_to_lead,
            )

        acceleration = self.clamp_control(acceleration)

        return acceleration, self.current_mode

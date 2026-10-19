Mini-Project 1: Adaptive Cruise Control in CARLA
=================================================

## Overview

In this homework, we will design an adaptive cruise control (ACC) system. An ego car (host car) equipped with ACC typically has a sensor, such as radar, that estimates the distance to the vehicle in front (lead car) of the same lane.

The basic operation of ACC is as follows: the driver sets a desired cruise speed `desired_speed` that is assumed to be constant across this project. If the distance between the host car and the lead car is greater than a certain threshold, then the host car attempts to travel at the desired cruise speed. If the distance between the host car and the lead car is less than that, then the host car tries to maintain at least a safe distance `distance_threshold` from the lead car.

The inputs to the ACC are the desired cruise speed for the host car, the estimated distance between the lead car and the host car, and the host car's velocity. The output of the ACC-based controller is the control signal for throttle/brakes of the host car and the current operation mode: either "cruising" or "following".

## Task

You are given a project with the structure:
```
csci513-miniproject1/
├── Carla.def
├── Carla.Dockerfile
├── HPC-Instructions.md
├── imgs/
│   ├── OnDemandDashboard.PNG
│   └── terminal.PNG
├── Makefile
├── mp1_controller/
│   ├── controller.py
│   └── __init__.py
├── mp1_evaluation/
│   ├── __init__.py
│   └── __main__.py
├── mp1_simulator/
│   ├── __init__.py
│   ├── __main__.py
│   ├── misc.py
│   ├── render.py
│   └── simulator.py
├── test_data/
│   ├── scenario1_0.json
│   ├── ...
│   └── scenario3_9.json
├── pyproject.toml
├── README.md
├── setup.cfg
└── setup.py
```

To get started, we are providing a skeleton of a closed loop system in this package.
The files in `mp1_simulator` interfaces with CARLA to simulate the ego and lead cars.
The primary control logic for the ego car is contained within the `mp1_controller` directory.

To assist in your control design, the `controller.py` contains a template of a controller. Your task is to edit the `Controller` class in `controller.py` such that the `run_step` function takes in an `Observation` (consisting of the desired cruise speed for the host car, estimated distance between the lead car and the host car, and the host car's velocity), and outputs a tuple with the acceleration control value between `-10.0` and `10.0` (in unit-less control inputs) and the operation mode enum. The acceleration control input is internally used to set the throttle and brakes for the ego vehicle.


## Setup

There are two ways to setup the project. The first method uses direct system installation, and the second method uses Docker. Both of these methods require a GPU. If you dont have access to a GPU, refer to [HPC instructions](HPC-Instructions.md) to use HPC for working on the project.

For local installations, follow the instructions below:

These instructions assume you have some Linux device. If you are using Windows, check out [Windows Subsystem for
Linux](https://docs.microsoft.com/en-us/windows/ai/directml/gpu-cuda-in-wsl).


In all instances, you need to have the following prerequisite packages installed:

1. Python >= 3.8
2. GNU Make


### The direct way

You will need to install CARLA (version 0.9.15). Follow the [instructions](https://carla.readthedocs.io/en/0.9.15/start_quickstart/) in the linked page for your specific platform.
You will also need its [additional assets](https://carla.readthedocs.io/en/0.9.15/start_quickstart/#import-additional-assets).

*IMPORTANT:* Remember to verify that you are installing version 0.9.15


### The Docker way

1. Install [Docker](https://docs.docker.com/get-docker/).
2. Install [`nvidia-docker2`][nvidia-docker2] container runtime to allow `docker` to use GPUs during execution.
3. Install GNU Make
4. Run `make build` to build the Docker image.

  *NOTE:* Docker requires root privileges, so keep an eye out for the `sudo` prompt.

[nvidia-docker2]: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#installation-guide

### Common for both of the above

From the current project directory, run

```shell
$ pip install -e .
```
This command will install the project dependencies, and allow you to run the simulations easily. If this command fails with an error similar to `ERROR: Could not find a version that satisfies the requirement carla==0.9.15 (from versions: 0.9.5)` you must first update pip with `pip install --upgrade pip` or `conda update pip`

## Running the simulations.

To run the simulations, you will need to have 2 terminals opened.

1. In the first terminal window, start the Carla server:
  - *Docker way:*
    - simply run `make run-carla`.

  - *Direct way:*
    - Change directory to the CARLA root folder  
    - Run  
    ```shell
    $ ./CarlaUE4.sh -RenderOffScreen
    ```

2. In the other terminal, go to the project root folder to start the controller:
```shell
$ python3 -m mp1_simulator test_data/*
```

You can also run the following to see what options you have for the controller.
```shell
$ python3 -m mp1_simulator --help
```

When you run the script, it will save a CSV file in the `logs/` directory for every episode.
These CSV files (or _traces_) are a recording of the simulation consisting of only the state variables we deem necessary for evaluating your design.
For every episode you will also have a video recorded by the on-board camera saved in `vids/` directory. You can use these to better understand the behavior of your controller.

## Evaluating your design

In this assignment, we will use Signal Temporal Logic (STL) requirements to ensure the
correctness of the controller. To do this, we use the [RT-AMT][rtamt] package (installed
automatically) to define offline monitors for your controller.

[rtamt]: https://github.com/nickovic/

To evaluate the traces you've captured for your controller, simply run the following
command:
```shell
$ python3 -m mp1_evaluation <list of log files>
```
where `<list of log files>` is a placeholder for all the CSV files you need to evaluate.
An example (assuming you are saving the files in `logs/` directory) would be:
```shell
$ python3 -m mp1_evaluation logs/*
```
which will evaluate all the files in that directory.

### Requirements being checked

The evaluator checks the following five requirements on every trace. In the table, `d` is the distance to the lead car, `v` is the ego velocity, `v_lead` is the lead car velocity, `v_des` is the desired cruise speed (20 m/s), and `mode` is the operation mode your controller reports (`FOLLOWING` = 1, `CRUISING` = 0). Each episode is 20 seconds long (200 steps of 0.1 s).

| Name | Requirement in words | Formal (STL) |
|---|---|---|
| `safeFollowing` | The ego car always keeps at least 4 m from the lead car. | `G (d >= 4)` |
| `forwardProgress` | The ego car never moves backwards. | `G (v >= 0)` |
| `dontStopUnlessLeadStops` | After t = 3 s, the ego car does not come to a stop (v < 0.1 m/s) while the lead car is still moving. | `G[3,3] not((v_lead > 0.1) U[0,20] (v < 0.1))` |
| `notFollowWhenFarAway` | Whenever the lead car is more than 40 m away, the controller switches to `CRUISING` within 2 s (unless the gap closes first). | `G[0,18] ((d > 40) -> F[0,2] (mode = CRUISING or d < 40))` |
| `reachTargetWhenNotFollowing` | Whenever the controller is in `CRUISING` mode, the ego car reaches within 2 m/s of `v_des` within 6 s (unless it switches to `FOLLOWING` first). | `G[0,14] (mode = CRUISING -> F[0,6] (abs(v - v_des) < 2 or mode = FOLLOWING))` |

**Important notes:**

- The distance `d` is measured **between the centers** of the two cars, not bumper to bumper. Since both cars are roughly 4.5 to 5 m long, a center-to-center distance of 4 m already means a collision. In practice, a collision ends the episode and sets `d` to 0, which fails `safeFollowing`. Design your controller with a comfortable margin.
- If the lead car leaves the lane (lateral offset of 2 m or more), `d` is reported as `inf`. Your controller should handle this gracefully.
- The lead car is always stationary at the start of an episode, and the ego car starts at rest.
- The exact definitions are in `mp1_evaluation/__main__.py`. Do not modify that file; the autograder uses its own copy.

### Grading

Your controller will be graded by running it on the **15 scenarios provided in `test_data/`** and checking the five requirements above on each resulting trace. This is exactly what `python3 -m mp1_simulator test_data/*` followed by `python3 -m mp1_evaluation logs/*` does, so you can compute your own score before submitting.

- Each requirement is worth **20%** of the controller grade.
- The score for a requirement is the fraction of the 15 scenarios on which it is satisfied, i.e. the `Fraction satisfied` value printed at the end of the evaluator output.
- A controller that satisfies all five requirements on all 15 scenarios receives full marks.

For example, if your controller satisfies `safeFollowing`, `forwardProgress`, `notFollowWhenFarAway`, and `reachTargetWhenNotFollowing` on every scenario, but `dontStopUnlessLeadStops` on only 12 of 15, your controller score is `4 x 20% + 20% x 12/15 = 96%`.

### What to submit

Submit **only** your `mp1_controller/controller.py`. The autograder copies your file into a clean copy of this project, so:

- Do not rename the `Controller` class or change the signature of `__init__` or `run_step`.
- Do not rely on changes to any other file in the project; they will not be present during grading.
- Do not import packages beyond those installed by `pip install -e .` (the standard library, `numpy`, and `scipy` are all fine).
- Your controller must run on all 15 scenarios without raising an exception. A crash on a scenario counts as failing all five requirements on that scenario.

Keep your `run_step` reasonably fast. The simulator calls it 200 times per episode in lockstep with CARLA, so a slow controller makes the whole run slow but does not change the physics.# CSCI513-MP1

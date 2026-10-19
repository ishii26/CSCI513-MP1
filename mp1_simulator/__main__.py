#!/usr/bin/env python

import argparse
import csv
import logging
from collections import deque
from pathlib import Path
from typing import NamedTuple

import numpy as np
import json
import os

from mp1_controller.controller import Controller
from mp1_simulator.simulator import CONFIG, Observation, Simulator, Mode

logger = logging.getLogger("SIMULATION")
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mini-Project 1: Adaptive Cruise Control in CARLA",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "test_data",
        nargs="+",
        help="JSON files containing the test data.",
        type=lambda p: Path(p).absolute(),
    )

    parser.add_argument(
        "--log-dir",
        help="Directory to store the simulation trace (defaults to 'logs/' in the current directory)",
        type=lambda p: Path(p).absolute(),
        default=Path.cwd() / "logs",
    )

    parser.add_argument(
        "--vid-dir",
        help="Directory to store camera video of the simulation (defaults to 'vids/' in the current directory)",
        type=lambda p: Path(p).absolute(),
        default=Path.cwd() / "vids",
    )

    parser.add_argument(
        "--render", 
        help="Render the Pygame display", 
        action="store_true"
    )

    return parser.parse_args()


class TraceRow(NamedTuple):
    ego_velocity: float
    target_speed: float
    distance_to_lead: float
    ado_velocity: float
    mode: Mode


def observation_to_trace_row(obs: Observation, sim: Simulator, mode: Mode) -> TraceRow:
    row = TraceRow(
        ego_velocity=obs.ego_velocity,
        target_speed=obs.desired_speed,
        distance_to_lead=obs.distance_to_lead,
        ado_velocity=sim._get_ado_velocity(),
        mode=mode
    )
    
    return row


def run_episode(sim: Simulator, controller: Controller, *, log_file: Path, video_file: Path):
    trace = deque()  # type: deque[TraceRow]
    row = sim.reset()
    trace.append(observation_to_trace_row(row, sim, Mode.CRUISING))
    while True:
        action, mode = controller.run_step(row)
        row = sim.step(action)
        trace.append(observation_to_trace_row(row, sim, mode))

        if sim.completed:
            break
        
    sim.dump_video(str(video_file))
    with open(log_file, "w") as flog:
        csv_stream = csv.writer(flog)
        csv_stream.writerow(
            [
                "timestep",
                "time_elapsed",
                "ego_velocity",
                "desired_speed",
                "distance_to_lead",
                "lead_speed",
                "mode"
            ]
        )

        for i, row in enumerate(trace):
            row = [
                i,
                sim.dt * i,
                row.ego_velocity,
                row.target_speed,
                row.distance_to_lead,
                row.ado_velocity,
                row.mode.value
            ]
            csv_stream.writerow(row)


def main():
    args = parse_args()
    log_dir: Path = args.log_dir
    vid_dir: Path = args.vid_dir
    test_files = args.test_data

    if log_dir.is_dir():
        logger.warning(
            "Looks like the log directory %s already exists. Existing logs may be overwritten.",
            str(log_dir),
        )
    else:
        log_dir.mkdir(parents=True, exist_ok=True)

    if vid_dir.is_dir():
        logger.warning(
            "Looks like the vid directory %s already exists. Existing vids may be overwritten.",
            str(vid_dir),
        )
    else:
        vid_dir.mkdir(parents=True, exist_ok=True)


    sim = Simulator(
        render=args.render,
        log_dir=log_dir
    )


    for test_file in test_files:
        with open(test_file, "r") as file:
            scenario_data = json.load(file)

        initial_ego_state = scenario_data['ego']
        initial_lead_state = scenario_data['lead']
        ado_actions = scenario_data['ado_actions']

        controller = Controller(
            distance_threshold=CONFIG["distance_threshold"],
        )

        logger.info("Running test data: %s", test_file)

        out_file = os.path.splitext(os.path.basename(test_file))[0]
        episode_name = f"episode-{out_file}.csv"
        video_name = f"episode-{out_file}.mp4"

        sim._set_ado_control(ado_actions)
        sim.set_spawn_points(initial_ego_state, initial_lead_state)
        run_episode(sim, controller, log_file=(log_dir / episode_name), video_file=(vid_dir / video_name))

        logger.info("Episode saved in %s", (log_dir / episode_name))

if __name__ == "__main__":
    main()

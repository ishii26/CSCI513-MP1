"""Evaluation script for MP1"""


import argparse
import csv
import logging
import sys
import numpy as np
from collections import defaultdict, deque
from pathlib import Path
from typing import Iterable, List, Mapping, NamedTuple, Sequence, Tuple

import rtamt
from rtamt import STLDenseTimeSpecification

logger = logging.getLogger("EVAL")
# handler = logging.StreamHandler()
# formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
# handler.setFormatter(formatter)
# logger.addHandler(handler)
logger.setLevel(logging.INFO)


class TraceRow(NamedTuple):
    ego_velocity: float
    desired_speed: float
    distance_to_lead: float
    ado_velocity: float
    following: int


Signal = Iterable[Tuple[float, float]]
Trace = Mapping[str, Signal]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="""Evaluation script for Mini-Project 1.

        This script expects a set of CSV trace files (saved from running the
        experiment), and computes the robustness of each trace.
        """,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "tracefiles",
        metavar="tracefile.csv",
        nargs="+",
        help="CSV files containing the traces for experiments.",
        type=lambda p: Path(p).absolute(),
    )

    return parser.parse_args()


def extract_trace(tracefile: Path) -> Trace:
    signals = ["ego_velocity", "desired_speed",
               "distance_to_lead", "lead_speed", "mode"]
    # type: Mapping[str, deque[Tuple[float, float]]]
    trace = defaultdict(list)
    with open(tracefile, "r") as f:
        csv_file = csv.DictReader(f)
        for row in csv_file:
            for signal in signals:
                trace[signal].append(
                    (float(row["time_elapsed"]), float(row[signal])))
                
    return trace


def _prepare_spec() -> STLDenseTimeSpecification:
    spec = STLDenseTimeSpecification()
    spec.set_sampling_period(100, "ms", 0.1)
    spec.declare_const("dsafe", "float", "4")
    spec.declare_const("T", "float", "20.0")

    spec.declare_var("ego_velocity", "float")
    spec.declare_var("desired_speed", "float")
    spec.declare_var("distance_to_lead", "float")
    spec.declare_var("lead_speed", "float")
    spec.declare_var("mode", "float")

    return spec


def _parse_and_eval_spec(
    spec: STLDenseTimeSpecification, trace: Trace
) -> Mapping[float, float]:
    try:
        spec.parse()
    except rtamt.STLParseException as e:
        logger.critical("STL Parse Exception: {}".format(e))
        sys.exit(1)

    return dict(
        spec.evaluate(*trace.items())
    )


def checkSafeFollowing(trace: Trace) -> Mapping[float, float]:
    spec = _prepare_spec()
    spec.name = "Check if the ego maintains safe following distance"

    spec.spec = "always (distance_to_lead >= dsafe)"

    return _parse_and_eval_spec(spec, trace)


def checkForwardProgress(trace: Trace) -> Mapping[float, float]:
    spec = _prepare_spec()
    spec.name = "Check if ego car is never moving backwards"

    spec.spec = "always (ego_velocity >= 0)"

    return _parse_and_eval_spec(spec, trace)


def checkDontStopUnlessLeadStops(trace: Trace) -> Mapping[float, float]:
    spec = _prepare_spec()
    spec.name = "Check if ego car stopped without lead stopping"

    spec.declare_const("reallySmallSpeed", "float", "0.1")
    # Need to "offset the starting point" here since lead vehicle is always initially stationary
    spec.spec = "G[3.:3.] (not((lead_speed > reallySmallSpeed) until[0.:20.] (ego_velocity < reallySmallSpeed)))"

    return _parse_and_eval_spec(spec, trace)


def checkNotFollowWhenFarAway(trace: Trace) -> Mapping[float, float]:
    spec = _prepare_spec()
    spec.name = "Check that cruising mode is triggered when distance to lead is high enough"

    spec.declare_const("followingDistThreshold", "float", "40.")
    spec.spec = "always[0:18.]((distance_to_lead > followingDistThreshold) -> F[0:2.] (mode < 0.5 or distance_to_lead < followingDistThreshold))"

    return _parse_and_eval_spec(spec, trace)


def checkReachTargetWhenNotFollowing(trace: Trace) -> Mapping[float, float]:
    spec = _prepare_spec()
    spec.name = "Check that target speed is being reached in 6 seconds when in cruising mode"

    spec.declare_const("closeEnough", "float", "2.0")

    spec.spec = "G[0:14.](mode < 0.5 -> F[0:6.]( (abs(ego_velocity - desired_speed) < closeEnough) or mode > 0.5) )"
    
    return _parse_and_eval_spec(spec, trace)


def evaluate_tracefile(tracefile: Path):
    trace = extract_trace(tracefile)

    safeFollowing = checkSafeFollowing(trace)[0.0] >= 0
    print("`safeFollowing`               = {}".format(
        'sat' if safeFollowing else 'unsat'))

    forwardProgress = checkForwardProgress(trace)[0.0] >= 0
    print("`forwardProgress`             = {}".format(
        'sat' if forwardProgress else 'unsat'))

    dontStopUnlessLeadStops = checkDontStopUnlessLeadStops(trace)[0.0] >= 0
    print("`dontStopUnlessLeadStops`     = {}".format(
        'sat' if dontStopUnlessLeadStops else 'unsat'))

    notFollowWhenFarAway = checkNotFollowWhenFarAway(trace)[0.0] >= 0
    print("`notFollowWhenFarAway`        = {}".format(
        'sat' if notFollowWhenFarAway else 'unsat'))

    reachTargetWhenNotFollowing = checkReachTargetWhenNotFollowing(trace)[0.0] >= 0
    print("`reachTargetWhenNotFollowing` = {}".format(
        'sat' if reachTargetWhenNotFollowing else 'unsat'))

    return [
        safeFollowing, forwardProgress, dontStopUnlessLeadStops,
        notFollowWhenFarAway, reachTargetWhenNotFollowing
    ]


def main():
    args = parse_args()

    tracefiles = args.tracefiles  # type: List[Path]
    data = []
    for tracefile in tracefiles:
        if str(tracefile)[-4:] == '.csv':
            print("===================================================")
            print("Evaluating trace file: ", str(
                tracefile.relative_to(Path.cwd())))
            data += [evaluate_tracefile(tracefile)]
            print("===================================================")
            print()
    data = np.array(data)
    means = np.mean(data, axis=0)
    print("===================================================")
    print("Fraction satisfied")
    print("Robustness for `safeFollowing`               = {}".format(
        means[0]))
    print("Robustness for `forwardProgress`             = {}".format(
        means[1]))
    print("Robustness for `dontStopUnlessLeadStops`     = {}".format(
        means[2]))
    print("Robustness for `notFollowWhenFarAway`        = {}".format(
        means[3]))
    print("Robustness for `reachTargetWhenNotFollowing` = {}".format(
        means[4]))


if __name__ == "__main__":
    main()

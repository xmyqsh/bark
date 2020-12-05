# Copyright (c) 2020 fortiss GmbH
#
# Authors: Julian Bernhard, Klemens Esterle, Patrick Hart and
# Tobias Kessler
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

import logging
import os

from bark.core.world.agent import Agent
from bark.core.models.behavior import BehaviorStaticTrajectory, BehaviorMobil
from bark.core.models.dynamic import StateDefinition
from bark.core.world.goal_definition import GoalDefinition, GoalDefinitionPolygon
from bark.core.geometry import Point2d, Polygon2d, NormToPI
from bark.runtime.commons.model_json_conversion import ModelJsonConversion
# Interaction dataset tools
from com_github_interaction_dataset_interaction_dataset.python.utils import dataset_reader
from com_github_interaction_dataset_interaction_dataset.python.utils import dict_utils
import numpy as np

from bark.runtime.scenario.interaction_dataset_processing.agent_track_info import AgentTrackInfo


def BarkStateFromMotionState(state, xy_offset, time_offset=0):
    bark_state = np.zeros(int(StateDefinition.MIN_STATE_SIZE))
    bark_state[int(StateDefinition.TIME_POSITION)] = (
        state.time_stamp_ms - time_offset) / 1000.0
    bark_state[int(StateDefinition.X_POSITION)] = state.x + xy_offset[0]
    bark_state[int(StateDefinition.Y_POSITION)] = state.y + xy_offset[1]
    orientation = NormToPI(state.psi_rad)
    if (orientation > np.pi or orientation < -np.pi):
        logging.error(
            "Orientation in Track file is ill-defined: {}".format(state.psi_rad))
    bark_state[int(StateDefinition.THETA_POSITION)] = orientation
    bark_state[int(StateDefinition.VEL_POSITION)] = pow(
        pow(state.vx, 2) + pow(state.vy, 2), 0.5)
    return bark_state.reshape((1, int(StateDefinition.MIN_STATE_SIZE)))


def TrajectoryFromTrack(track, xy_offset, start=0, end=None):
    states = list(dict_utils.get_item_iterator(track.motion_states))
    if end is None:
        end = states[-1][0]
    filtered_motion_states = list(
        filter(lambda s: start <= s[0] <= end, states))
    n = len(filtered_motion_states)
    traj = np.zeros((n, int(StateDefinition.MIN_STATE_SIZE)))
    for i, state in enumerate(filtered_motion_states):
        # TODO: rename start to be the scenario start time!
        traj[i, :] = BarkStateFromMotionState(
            state[1], xy_offset=xy_offset, time_offset=start)
    return traj


def ShapeFromTrack(track, wheelbase=2.7):
    offset = wheelbase / 2.0
    length = track.length
    width = track.width
    pose = [0.0, 0.0, 0.0]
    p1 = [length / 2.0 + offset, -width / 2.0]
    p2 = [length / 2.0 + offset, width / 2.0]
    p3 = [-length / 2.0 + offset, width / 2.0]
    p4 = [-length / 2.0 + offset, -width / 2.0]
    points = [p1, p2, p3, p4, p1]
    poly = Polygon2d(pose, points)
    # TODO(@esterle): also infer wheelbase
    return poly


def InitStateFromTrack(track, xy_offset, start):
    minimum_start = min(track.motion_states)
    if minimum_start > start:
        start = minimum_start
    state = track.motion_states[int(start)]
    bark_state = BarkStateFromMotionState(
        state, xy_offset=xy_offset, time_offset=state.time_stamp_ms)
    return bark_state.reshape((int(StateDefinition.MIN_STATE_SIZE), 1))


def GoalDefinitionFromTrack(track, end, xy_offset):
    goal_size = 12.0
    states = list(dict_utils.get_item_iterator(track.motion_states))
    # Goal position is spatial position of last state
    motion_state = states[-1][1]
    bark_state = BarkStateFromMotionState(motion_state, xy_offset=xy_offset)
    goal_polygon = Polygon2d(np.array([0.5 * goal_size, 0.5 * goal_size, 0.0]),
                             [Point2d(0.0, 0.0),
                              Point2d(goal_size, 0.0),
                              Point2d(goal_size, goal_size),
                              Point2d(0.0, goal_size),
                              Point2d(0.0, 0.0)])
    goal_point = Point2d(bark_state[0, int(StateDefinition.X_POSITION)] - 0.5 *
                         goal_size, bark_state[0, int(StateDefinition.Y_POSITION)] - 0.5 * goal_size)
    goal_polygon = goal_polygon.Translate(goal_point)
    goal_definition = GoalDefinitionPolygon(goal_polygon)
    return goal_definition


def BehaviorFromTrack(track, params, xy_offset, start, end):
    return BehaviorStaticTrajectory(params, TrajectoryFromTrack(track, xy_offset=xy_offset, start=start, end=end))


class InteractionDatasetReader:
    def __init__(self):
        self._track_dict_cache = {}

    def TrackFromTrackfile(self, filename, track_id):
        if filename not in self._track_dict_cache:
            try:
                self._track_dict_cache[filename] = dataset_reader.read_tracks(
                    filename)
            except FileNotFoundError as e:
                logging.error("File {} not found!".format(
                    os.path.abspath(filename)))
                exit(1)
        track = self._track_dict_cache[filename][track_id]
        # TODO: Filter track
        return track

    def AgentFromTrackfile(self, track_params, param_server, scenario_track_info, agent_id):
        if scenario_track_info.GetEgoTrackInfo().GetTrackId() == agent_id:
            agent_track_info = scenario_track_info.GetEgoTrackInfo()
        elif agent_id in scenario_track_info.GetOtherTrackInfos().keys():
            agent_track_info = scenario_track_info.GetOtherTrackInfos()[
                agent_id]
        else:
            raise ValueError("unknown agent id {}".format(agent_id))
        fname = agent_track_info.GetFileName()  # track_params["filename"]
        track_id = agent_track_info.GetTrackId()  # track_params["track_id"]
        agent_id = agent_track_info.GetTrackId()
        track = self.TrackFromTrackfile(fname, track_id)

        xy_offset = scenario_track_info.GetXYOffset()

        start_time = scenario_track_info.GetStartTs()

        if start_time < scenario_track_info.GetEndTs():
          end_time = scenario_track_info.GetEndTs()
        else:
          raise ValueError("Agent cannot start after scenario end")

        behavior_model = track_params["behavior_model"]
        model_converter = ModelJsonConversion()
        if behavior_model is None:
            # each agent need's its own param server
            behavior = BehaviorFromTrack(track, param_server.AddChild(
                "agent{}".format(agent_id)), xy_offset, start_time, end_time)
        else:
            behavior = behavior_model

        try:
            start_time_first_valid = scenario_track_info.GetStartTs() + scenario_track_info.GetOffsetOfAgentMillisec(agent_id)*1000
            initial_state = InitStateFromTrack(track, xy_offset, start_time_first_valid)
        except:
            raise ValueError("Could not retrieve initial state of agent {} at t={}.".format(
                agent_id, scenario_track_info.GetStartTs() + scenario_track_info.GetOffsetOfAgentMillisec(agent_id)*1000))

        try:
            dynamic_model = model_converter.convert_model(
                track_params["dynamic_model"], param_server)
        except:
            raise ValueError("Could not create dynamic_model")

        try:
            execution_model = model_converter.convert_model(
                track_params["execution_model"], param_server)
        except:
            raise ValueError("Could not retrieve execution_model")

        try:
            vehicle_shape = ShapeFromTrack(
                track, param_server["DynamicModel"]["wheel_base", "Wheel base", 2.7])
        except:
            raise ValueError("Could not create vehicle_shape")

        bark_agent = Agent(
            initial_state,
            behavior,
            dynamic_model,
            execution_model,
            vehicle_shape,
            param_server.AddChild("agent{}".format(agent_id)),
            GoalDefinitionFromTrack(track, end_time, xy_offset=xy_offset),
            track_params["map_interface"])
        # set agent id from track
        bark_agent.SetAgentId(track_id)
        return bark_agent

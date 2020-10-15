// Copyright (c) 2020 fortiss GmbH
//
// Authors: Julian Bernhard, Klemens Esterle, Patrick Hart and
// Tobias Kessler
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.

#include <tuple>

#include "bark/models/behavior/rss_behavior/rss_behavior.hpp"
#include "bark/world/observed_world.hpp"

namespace bark {
namespace models {
namespace behavior {

Trajectory RSSBehavior::Plan(
    float min_planning_time, const world::ObservedWorld& observed_world) {
  SetBehaviorStatus(BehaviorStatus::VALID);

  const auto& lane_corr = observed_world.GetLaneCorridor();
  if (!lane_corr) {
    LOG(INFO) << "Agent " << observed_world.GetEgoAgentId()
              << ": Behavior status has expired!" << std::endl;
    SetBehaviorStatus(BehaviorStatus::EXPIRED);
    return GetLastTrajectory();
  }

  // TODO: add evaluator that sets RSSBehaviorStatus
  // auto eval_res = rss_evaluator_.Evaluate(observed_world);
  // if (eval_res) {
  //   rss_behavior_status_ = RSSBehaviorStatus::NORMAL_BEHAVIOR;
  // } else {
  //   rss_behavior_status_ = RSSBehaviorStatus::SAFE_BEHAVIOR;
  // }

  if (rss_behavior_status_ == RSSBehaviorStatus::NORMAL_BEHAVIOR) {
    // execute normal
    behavior_model_->Plan(min_planning_time, observed_world);
    auto last_action = behavior_model_->GetLastAction();
    auto last_traj = behavior_model_->GetLastTrajectory();
    // set values
    SetLastTrajectory(last_traj);
    SetLastAction(last_action);
    return last_traj;

  } else {
    safety_behavior_model_->Plan(min_planning_time, observed_world);
    auto last_action = safety_behavior_model_->GetLastAction();
    auto last_traj = safety_behavior_model_->GetLastTrajectory();
    // set values
    SetLastTrajectory(last_traj);
    SetLastAction(last_action);
    return last_traj;
  }
}


}  // namespace behavior
}  // namespace models
}  // namespace bark

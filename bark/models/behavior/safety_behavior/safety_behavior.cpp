// Copyright (c) 2020 fortiss GmbH
//
// Authors: Julian Bernhard, Klemens Esterle, Patrick Hart and
// Tobias Kessler
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.

#include <tuple>

#include "bark/models/behavior/constant_acceleration/constant_acceleration.hpp"
#include "bark/world/observed_world.hpp"

namespace bark {
namespace models {
namespace behavior {

Trajectory BehaviorSafety::Plan(
    float min_planning_time, const world::ObservedWorld& observed_world) {
  SetBehaviorStatus(BehaviorStatus::VALID);

  const auto& lane_corr = observed_world.GetLaneCorridor();
  if (!lane_corr) {
    LOG(INFO) << "Agent " << observed_world.GetEgoAgentId()
              << ": Behavior status has expired!" << std::endl;
    SetBehaviorStatus(BehaviorStatus::EXPIRED);
    return GetLastTrajectory();
  }


  if (dynamic_pointer_cast<BehaviorIDMLaneTracking>(sub_behavior_model_)) {
    std::shared_ptr<BehaviorIDMLaneTracking> idm_lane_tracking_behavior =
      dynamic_pointer_cast<BehaviorIDMLaneTracking>(sub_behavior_model_);
    
    idm_lane_tracking_behavior->Plan(min_planning_time, observed_world);
    auto last_action = idm_lane_tracking_behavior->GetLastAction();
    auto last_traj = idm_lane_tracking_behavior->GetLastTrajectory();
    
    // set values
    SetLastTrajectory(traj);
    SetLastAction(action);
    return traj;
  }

}


}  // namespace behavior
}  // namespace models
}  // namespace bark

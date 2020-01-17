// Copyright (c) 2019 fortiss GmbH, Julian Bernhard, Klemens Esterle, Patrick Hart, Tobias Kessler
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.


#ifndef MODULES_WORLD_MAP_ROAD_CORRIDOR_HPP_
#define MODULES_WORLD_MAP_ROAD_CORRIDOR_HPP_

#include <map>
#include <vector>
#include <string>
#include <utility>
#include <boost/functional/hash.hpp>
#include "modules/world/opendrive/opendrive.hpp"
#include "modules/world/map/road.hpp"
#include "modules/world/map/lane.hpp"
#include "modules/world/map/lane_corridor.hpp"
#include "modules/geometry/geometry.hpp"


namespace modules {
namespace world {
namespace map {

using modules::geometry::Line;
using modules::geometry::Polygon;
using modules::geometry::Point2d;
using modules::geometry::Within;
using modules::world::opendrive::XodrRoadId;


struct RoadCorridor {
  //! Getter
  RoadPtr GetRoad(const RoadId& road_id) const {
    if (roads_.count(road_id) == 0)
      return nullptr;
    return roads_.at(road_id);
  }
  Roads GetRoads() const {return roads_;}
  Lanes GetLanes(const RoadId& road_id) const {
    return this->GetRoad(road_id)->GetLanes();
  }
  LaneCorridorPtr GetLaneCorridor(const LaneId& lane_id) const {
    if (lane_corridors_.count(lane_id) == 0)
      return nullptr;
    return lane_corridors_.at(lane_id);
  }
  std::vector<LaneCorridorPtr> GetAllLaneCorridors() const {
    return unique_lane_corridors_;
  }
  LaneCorridorPtr GetCurrentLaneCorridor(const Point2d& pt) const {
    for (auto& lane_corr : unique_lane_corridors_) {
      if (Within(pt, lane_corr->GetMergedPolygon()))
        return lane_corr;
    }
    return nullptr;
  }
  std::pair<LaneCorridorPtr, LaneCorridorPtr>
  GetLeftRightLaneCorridor(const Point2d& pt) const {
    LaneCorridorPtr current_lane_corr = GetCurrentLaneCorridor(pt);
    LanePtr left_lane = current_lane_corr->GetCurrentLane(pt)->GetLeftLane();
    LanePtr right_lane = current_lane_corr->GetCurrentLane(pt)->GetRightLane();
    LaneId left_lane_id = 10000000;
    LaneId right_lane_id = 10000000;
    if (left_lane)
      left_lane_id = left_lane->get_id();
    if (right_lane)
      right_lane_id = right_lane->get_id();
    return std::make_pair(
      GetLaneCorridor(left_lane_id),
      GetLaneCorridor(right_lane_id));
  }
  static std::size_t GetHash(
    const std::vector<XodrRoadId>& road_ids) {
    // calculate hash using road_ids
    return boost::hash_range(
      road_ids.begin(),
      road_ids.end());
  }

  //! Setter
  void SetRoads(const Roads& roads) {
    roads_ = roads;
  }
  void SetLaneCorridor(const LaneId& lane_id,
    const LaneCorridorPtr& corr) {
    lane_corridors_[lane_id] = corr;
    unique_lane_corridors_.push_back(corr);
  }

  Roads roads_;
  std::vector<LaneCorridorPtr> unique_lane_corridors_;
  std::map<LaneId, LaneCorridorPtr> lane_corridors_;
};
using RoadCorridorPtr = std::shared_ptr<RoadCorridor>;


}  // namespace map
}  // namespace world
}  // namespace modules

#endif  // MODULES_WORLD_MAP_ROAD_CORRIDOR_HPP_

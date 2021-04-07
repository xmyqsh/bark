# Copyright (c) 2021 fortiss GmbH
#
# Authors: Julian Bernhard, Klemens Esterle, Patrick Hart and
# Tobias Kessler
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.
import math
import numpy as np
import matplotlib.pyplot as plt
from bark.core.geometry import *
from bark.core.models.dynamic import *
from bark.core.world.opendrive import *
from bark.core.world.goal_definition import *
from bark.core.world.renderer import *
from bark.runtime.commons.parameters import ParameterServer
from bark.runtime.viewer.buffered_viewer import BufferedViewer


class BufferedMPViewer(BufferedViewer):
  def __init__(self, params=None, ax=None, **kwargs):
    super().__init__(params=params)
    self._ax = ax or plt.subplots()[1]
    self._vparams = self._params["Visualization"]
    self._view_dx = self._vparams["dx", "view range x", 20]
    self._view_dy = self._vparams["dy", "view range y", 20]
    self._world = None
  
  def drawWorld(self, world, eval_agent_ids=None, scenario_idx=None):
    self._ax.clear()
    super().drawWorld(world, eval_agent_ids, scenario_idx)
    self._world = world
    self.render()
    self._world.renderer.Clear()
    
  def render(self):
    # assert self._world == None, "World has not been drawn yet."
    for type_name, primitives in self._world.renderer.primitives.items():
      if type_name == "EGO_AGENT_STATE":
        self.ProcessEgoState(primitives)
      elif type_name == "MAP_LINE" or type_name == "LINES":
        self.DrawLines(primitives)
      elif type_name == "EGO_AGENT" or type_name == "OTHER_AGENT" \
        or type_name == "POLYGONS":
        self.DrawPolygons(primitives)
      elif type_name == "POINTS":
        self.DrawPoints(primitives)
    plt.pause(0.001)
    
  def ProcessEgoState(self, primitives):
    ego_state = primitives[-1].object
    self._ax.set_xlim(
      [ego_state[1] - self._view_dx, ego_state[1] + self._view_dx])
    self._ax.set_ylim(
      [ego_state[2] - self._view_dy, ego_state[2] + self._view_dy])

  def DrawLines(self, primitives):
    for primitive in primitives:
      np_pts = primitive.object.ToArray()
      color = np.array(primitive.conf["stroke_color"])/255
      self._ax.plot(np_pts[:, 0], np_pts[:, 1], color=color)
      
  def DrawPolygons(self, primitives):
    for primitive in primitives:
      np_poly = primitive.object.ToArray()
      color = np.array(primitive.conf["stroke_color"])/255
      self._ax.plot(np_poly[:, 0], np_poly[:, 1], color=color)

  def DrawPoints(self, primitives):
    for primitive in primitives:
      color = np.array(primitive.conf["stroke_color"])/255
      plt.plot(
        primitive.object.x(), primitive.object.y(), marker='*', color=color)
from multicorn import ForeignDataWrapper, Qual
from multicorn.utils import *

class GeoFDW(ForeignDataWrapper):
  def __init__(self, options, columns, srid = None):
    super(GeoFDW, self).__init__(options, columns)
    self.use_srid(srid)

  def use_srid(self, srid):
    if srid:
      self.srid = int(srid)
    else:
      self.srid = None

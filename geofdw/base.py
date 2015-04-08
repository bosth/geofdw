from multicorn import ForeignDataWrapper, Qual
from multicorn.utils import log_to_postgres
from logging import ERROR, INFO, DEBUG, WARNING, CRITICAL

class GeoFDW(ForeignDataWrapper):
  def __init__(self, options, columns, srid = None):
    super(GeoFDW, self).__init__(options, columns)
    self.use_srid(srid)

  def use_srid(self, srid):
    if srid:
      self.srid = int(srid)
    else:
      self.srid = None

  def log(self, message, level=WARNING):
    log_to_postgres(message, level)

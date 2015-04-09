from multicorn import ForeignDataWrapper, Qual
from multicorn.utils import log_to_postgres
from logging import ERROR, INFO, DEBUG, WARNING, CRITICAL
from geofdw.exception import MissingColumnError, MissingOptionError, OptionTypeError

class GeoFDW(ForeignDataWrapper):
  def __init__(self, options, columns, srid=None):
    super(GeoFDW, self).__init__(options, columns)
    self.use_srid(srid)

  def check_column(self, columns, column):
    if not column in columns:
      raise MissingColumnError(column)

  def get_option(self, options, option, required=True, default=None, option_type=str):
    if required and not option in options:
      raise MissingOptionError(option)
    value = options.get(option, default)
    try:
      return option_type(value)
    except ValueError as e:
      raise OptionTypeError(option, option_type)

  def get_web_service_options(self, options):
    if options.has_key('verify'):
      self.verify = options.get('verify').lower() in ['1', 't', 'true']
    else:
      self.verify = True

    if options.has_key('user') and options.has_key('pass'):
      self.auth = (options.get('user'), options.get('pass'))
    else:
      self.auth = None

  def use_srid(self, srid):
    if srid:
      self.srid = int(srid)
    else:
      self.srid = None

  def log(self, message, level=WARNING):
    log_to_postgres(message, level)

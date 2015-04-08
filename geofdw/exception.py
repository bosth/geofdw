class MissingColumnError(Exception):
  """
  Required column missing from either __init__ or execute (e.g. GeoJSON FDW
  requires a geom column).
  """
  def __init__(self, column):
    message = 'Missing column "%s"' % column
    super(MissingColumnError, self).__init__(message)

class MissingQueryPreciateError(Exception):
  """
  Required query predicate missing from execute (e.g. FGeocode FDW requires a
  predicate named query).
  """
  def __init__(self, pred):
    message = 'Missing query predicate "%s"' % pred
    super(MissingQueryPredicateError, self).__init__(message)

class MissingOptionError(Exception):
  """
  Required option missing from __init__ (e.g. GeoJSON FDW requires a url
  option).
  """
  def __init__(self, key_error):
    message = 'Missing option "%s"' % key_error.args[0]
    super(MissingOptionError, self).__init__(message)

class OptionTypeError(Exception):
  """
  Option has wrong type (e.g. SRID must be an integer).
  """
  def __init__(self, value_error):
    message = 'Incorrect option type: %s' % value_error.message
    super(OptionTypeError, self).__init__(message)

class OptionValueError(Exception):
  """
  Option has an invalid value.
  """
  pass

class InvalidGeometryError(Exception):
  pass

class ValueBoundsError(Exception):
  pass

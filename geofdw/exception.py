class MissingQueryPreciateError(Exception):
  def __init__(self, pred):
    message = 'Missing query predicate "%s"' % pred
    super(MissingQueryPredicateError, self).__init__(message)

class MissingOptionError(Exception):
  def __init__(self, key_error):
    message = 'Missing option "%s"' % key_error.args[0]
    super(MissingOptionError, self).__init__(message)

class OptionTypeError(Exception):
  def __init__(self, value_error):
    message = 'Incorrect option type: %s' % value_error.message
    super(OptionTypeError, self).__init__(message)

class OptionValueError(Exception):
  pass

class InvalidGeometryError(Exception):
  pass

class ValueBoundsError(Exception):
  pass

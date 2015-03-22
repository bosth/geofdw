class MissingQueryPreciateError(Exception):
  def __init__(self, pred):
    message = 'Missing query predicate "%s"' % pred
    super(MissingQueryPredicateError, self)..__init__(message)




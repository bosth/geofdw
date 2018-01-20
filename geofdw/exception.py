from multicorn.utils import log_to_postgres
from logging import ERROR


class GeoFDWError(Exception):
    def __init__(self, message):
        log_to_postgres(message, ERROR)


class MissingColumnError(GeoFDWError):
    """
    Required column missing from either __init__ or execute (e.g. GeoJSON FDW
    requires a geom column).
    """
    def __init__(self, column):
        message = "Missing column '%s'" % column
        super(MissingColumnError, self).__init__(message)


class MissingOptionError(GeoFDWError):
    """
    Required option missing from __init__ (e.g. GeoJSON FDW requires a url
    option).
    """
    def __init__(self, option):
        message = "Missing option '%s'" % option
        super(MissingOptionError, self).__init__(message)


class OptionTypeError(GeoFDWError):
    """
    Option has wrong type (e.g. SRID must be an integer).
    """
    def __init__(self, option, option_type):
        message = "Option %s is not of type %s" % (option, option_type)
        super(OptionTypeError, self).__init__(message)


class OptionValueError(GeoFDWError):
    """
    Option has an invalid value.
    """
    def __init__(self, message):
        super(OptionValueError, self).__init__(message)


class CRSError(GeoFDWError):
    """
    Invalid CRS.
    """
    def __init__(self, crs):
        message = "Bad CRS value of %s" % crs
        super(CRSError, self).__init__(message)


class InvalidGeometryError(GeoFDWError):
    pass


class ValueBoundsError(GeoFDWError):
    pass


class QueryPredicateError(GeoFDWError):
    pass


class MissingQueryPredicateError(GeoFDWError):
    """
    Required query predicate missing from execute (e.g. FGeocode FDW requires a
    predicate named query).
    """
    def __init__(self, message):
        super(MissingQueryPredicateError, self).__init__(message)

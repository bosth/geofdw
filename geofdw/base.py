from multicorn import ForeignDataWrapper, Qual
from multicorn.utils import log_to_postgres
from logging import ERROR, INFO, DEBUG, WARNING, CRITICAL
from geofdw.exception import MissingColumnError, MissingOptionError, OptionTypeError


class GeoFDW(ForeignDataWrapper):
    def __init__(self, options, columns, srid=None):
        super(GeoFDW, self).__init__(options, columns)
        self.options = options
        self.columns = columns
        self.srid = srid

    def check_columns(self, columns):
        for column in columns:
            if column not in self.columns:
                raise MissingColumnError(column)

    def get_option(self, option, required=True, default=None, option_type=str):
        if required and option not in self.options:
            raise MissingOptionError(option)
        value = self.options.get(option, default)
        if value is None:
            return None
        try:
            return option_type(value)
        except ValueError as e:
            raise OptionTypeError(option, option_type)

    def get_request_options(self):
        if "verify" in self.options:
            self.verify = self.options.get("verify").lower() in ["1", "t", "true"]
        else:
            self.verify = True

        if "user" in self.options and "pass" in self.options:
            self.auth = (self.options.get("user"), self.options.get("pass"))
        else:
            self.auth = None

    def log(self, message, level=WARNING):
        log_to_postgres(message, level)

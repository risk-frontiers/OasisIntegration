""" Class containing all custom RF exceptions"""


class RFBaseException(Exception):
    def __init__(self, message):
        super(RFBaseException, self).__init__(message)


class LocationLookupException(RFBaseException):
    def __init__(self, message):
        super(LocationLookupException, self).__init__(message)


class LocationNotModelledException(RFBaseException):
    def __init__(self, message):
        super(LocationNotModelledException, self).__init__(message)


class ArgumentOutOfRangeException(RFBaseException):
    def __init__(self, message):
        super(ArgumentOutOfRangeException, self).__init__(message)

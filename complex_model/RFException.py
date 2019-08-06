""" Class containing all custom RF exceptions"""


class RFBaseException(Exception):
    def __init__(self, message, code):
        super(RFBaseException, self).__init__(message)
        self.error_code = code


class LocationLookupException(RFBaseException):
    def __init__(self, message, error_code=100):
        super(LocationLookupException, self).__init__(message, error_code)


class LocationNotModelledException(RFBaseException):
    def __init__(self, message, error_code=200):
        super(LocationNotModelledException, self).__init__(message, error_code)


class ArgumentOutOfRangeException(RFBaseException):
    def __init__(self, message, error_code=300):
        super(ArgumentOutOfRangeException, self).__init__(message, error_code)


class FileNotFoundException(RFBaseException):
    def __init__(self, message, error_code=400):
        super(FileNotFoundException, self).__init__(message, error_code)
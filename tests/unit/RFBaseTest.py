import unittest

from complex_model.RFException import RFBaseException


class RFBaseTestCase(unittest.TestCase):
    def assertRaisesWithErrorCode(self, error_code, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
            self.fail()
        except RFBaseException as inst:
            self.assertEqual(error_code, inst.error_code)

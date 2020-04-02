import unittest
import utils 
import os

class TestUtils(unittest.TestCase):

    def test_generate_barcode(self):
        with self.assertRaises(TypeError):
            utils.generate_barcode(None)
            utils.generate_barcode(125)
            utils.generate_barcode("125", 125)
            
        with self.assertRaises(ValueError):
            utils.generate_barcode("")
            utils.generate_barcode("bkbla/")
            utils.generate_barcode("125", "codebar")
            
        file = utils.generate_barcode(codebar_payload=125)
        self.assertTrue(os.path.exists(file))
        if os.path.exists(file):
            os.remove(file)
            
        file = utils.generate_barcode(codebar_payload="125", codebar_format="qrcode")
        self.assertTrue(os.path.exists(file))
        if os.path.exists(file):
            os.remove(file)
 
              
    def insert_barcode(self):
        pass

if __name__ == '__main__':
    unittest.main()

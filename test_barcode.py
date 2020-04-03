import unittest
import os
from barcode import BarCodePosition, generate_barcode_image

class TestGenerateBarcode(unittest.TestCase):

    def test_generate_barcode_image(self):
        with self.assertRaises(TypeError):
            generate_barcode_image(None)
            generate_barcode_image(125)
            generate_barcode_image("125", 125)

        with self.assertRaises(ValueError):
            generate_barcode_image("")
            generate_barcode_image("bkbla/")
            generate_barcode_image("125", "barcode")

        file = generate_barcode_image(barcode_payload="125")
        self.assertTrue(os.path.exists(file))
        if os.path.exists(file):
            os.remove(file)

        file = generate_barcode_image(
            barcode_payload="125",
            barcode_format="qrcode")
        self.assertTrue(os.path.exists(file))
        if os.path.exists(file):
            os.remove(file)
            
            
class TestBarcode(unittest.TestCase):
    def test_coordinate(self):
        position_barcode = BarCodePosition(postion = "up_left",
                                           x_margin=10,
                                           y_margin=15,
                                           barcode_width=20,
                                           barcode_heigth=10)
        self.assertTrue((10 == position_barcode.x and 15 == position_barcode.y))
        

        position_barcode = BarCodePosition(postion = "up_right",
                                           x_margin=10,
                                           y_margin=5,
                                           barcode_width=10,
                                           barcode_heigth=10)
        self.assertTrue((190 == position_barcode.x and 5 == position_barcode.y))
        
        
        position_barcode = BarCodePosition(postion = "bottom_left",
                                           x_margin=5,
                                           y_margin=2,
                                           barcode_width=10,
                                           barcode_heigth=10)
        self.assertTrue((5 == position_barcode.x and 285 == position_barcode.y))
        
        position_barcode = BarCodePosition(postion = "",
                                           x_margin=1,
                                           y_margin=2,
                                           barcode_width=10,
                                           barcode_heigth=10)
        self.assertTrue((199 == position_barcode.x and 285 == position_barcode.y))
        
        

        
if __name__ == '__main__':
    unittest.main()

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
        BarCodePosition.page_with = 210
        BarCodePosition.page_height = 297
        
        p = BarCodePosition(postion = "up_left",
                                           x_margin=10,
                                           y_margin=15,
                                           barcode_width=20,
                                           barcode_heigth=10)
       
        self.assertTrue((10 == p.x0 
                         and 30 == p.x1
                         and 15 == p.y0
                         and 25 == p.y1))
        
        p = BarCodePosition(postion = "up_right",
                                           x_margin=10,
                                           y_margin=15,
                                           barcode_width=20,
                                           barcode_heigth=10)
       
        self.assertTrue((180 == p.x0 
                         and 200 == p.x1
                         and 15 == p.y0
                         and 25 == p.y1))
    
        
        
        

        
if __name__ == '__main__':
    unittest.main()

import unittest
import os
import stat
import shutil
import secrets
from mailing.resources.barcode import BarCodePosition, generate_barcode_image


PWD = os.path.dirname(__file__)
TMP_DIR = "".join([PWD, '/temps/'])

    
class TestGenerateBarcode(unittest.TestCase):

    def setUp(self):
        temp_dir = os.path.join(TMP_DIR, secrets.token_hex(8))
        os.makedirs(temp_dir)
        self.job_dir = temp_dir


    def generate_barcode_image(self):
        
        with self.assertRaises(TypeError):
            generate_barcode_image(None, tmp_dir=self.job_dir)
            generate_barcode_image(125, tmp_dir=self.job_dir)
            generate_barcode_image("125", 125, tmp_dir=self.job_dir)

        with self.assertRaises(ValueError):
            generate_barcode_image("", tmp_dir=self.job_dir)
            generate_barcode_image("bkbla/", tmp_dir=self.job_dir)
            generate_barcode_image("125", "barcode", tmp_dir=self.job_dir)

        file = generate_barcode_image(barcode_payload="125", tmp_dir=self.job_dir)
        self.assertTrue(os.path.exists(file))
        

        file = generate_barcode_image(barcode_payload="125",
                                      barcode_format="qrcode", tmp_dir=self.job_dir)
        self.assertTrue(os.path.exists(file))


class TestBarcode(unittest.TestCase):
    def test_coordinate(self):


        p = BarCodePosition(postion="up_left",
                            x_margin=10,
                            y_margin=15,
                            barcode_width=20,
                            barcode_heigth=10,
                            page_with=210,
                            page_height=297)

        self.assertTrue((10 == p.x0
                         and 30 == p.x1
                         and 15 == p.y0
                         and 25 == p.y1))

        p = BarCodePosition(postion="up_right",
                            x_margin=10,
                            y_margin=15,
                            barcode_width=20,
                            barcode_heigth=10,
                            page_with=210,
                            page_height=297)

        self.assertTrue((180 == p.x0
                         and 200 == p.x1
                         and 15 == p.y0
                         and 25 == p.y1))


if __name__ == '__main__':
    unittest.main()


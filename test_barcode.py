import unittest
import os
import barcode

class TestGenerateBarcode(unittest.TestCase):

    def test_generate_image(self):
        with self.assertRaises(TypeError):
            barcode.generate_image(None)
            barcode.generate_image(125)
            barcode.generate_image("125", 125)

        with self.assertRaises(ValueError):
            barcode.generate_image("")
            barcode.generate_image("bkbla/")
            barcode.generate_image("125", "codebar")

        file = barcode.generate_image(codebar_payload="125")
        self.assertTrue(os.path.exists(file))
        if os.path.exists(file):
            os.remove(file)

        file = barcode.generate_image(
            codebar_payload="125",
            codebar_format="qrcode")
        self.assertTrue(os.path.exists(file))
        if os.path.exists(file):
            os.remove(file)
            
            
class TestBarcode(unittest.TestCase):
    pass

if __name__ == '__main__':
    unittest.main()

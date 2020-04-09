import unittest
import os
import secrets
import shutil
from api.utils import merge_pdf

PWD = os.path.dirname(__file__)
TMP_DIR = "".join([PWD, '/temps/'])

    
class TestUtils(unittest.TestCase):

    def setUp(self):
        temp_dir = os.path.join(TMP_DIR, secrets.token_hex(8))
        os.makedirs(temp_dir)
        self.job_dir = temp_dir

    def __copy_static_file(self, file_name:str):
        file_orgine =  os.path.join(PWD, "static/",file_name)
        job_file = os.path.join(self.job_dir, secrets.token_hex(8)+".pdf")
        shutil.copyfile(file_orgine, job_file)
        
    def test_merge_pdf(self):
        with self.assertRaises(IOError):
            merge_pdf(self.job_dir)#empty directory
        
        self.__copy_static_file("do_not_delete.pdf")
        self.__copy_static_file("do_not_delete_0.pdf")
        self.__copy_static_file("do_not_delete_1.pdf") 
        file_merge = merge_pdf(self.job_dir)
        self.assertTrue(os.path.exists(file_merge))

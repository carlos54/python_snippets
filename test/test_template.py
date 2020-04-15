import unittest
import os
from werkzeug.datastructures import FileStorage
from mailing.test import app, pwd


class TestAppTemplateV1(unittest.TestCase):

    def setUp(self):
        self.version = "v1"
        self.current_client = app.test_client() 
                
    def test_get(self):
        #with test_recipients

        r = self.current_client.get(f'/{self.version}/template')
      
        self.assertEqual(r.status_code, 200)
        

if __name__ == '__main__':
   unittest.main()

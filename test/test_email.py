import unittest
import os
from werkzeug.datastructures import FileStorage
from mailing.test import app, pwd


class TestAppEmailV1(unittest.TestCase):

    def setUp(self):
        self.version = "v1"
        self.current_client = app.test_client() 
                
    def test_post(self):
        #with test_recipients
        data =  os.path.join(pwd, "static/","email_data_valide.json")
        file_to_transfer = FileStorage(
            stream=open(data, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
            f'/{self.version}/email',
            data={
                "template_id":"emailtest",
                "respondents": file_to_transfer,
                "test_recipients" : "mail1@statec.lu;mail2@statec.lu"
            },
            content_type="multipart/form-data"
            )

        self.assertEqual(r.status_code, 200)
        

if __name__ == '__main__':
   unittest.main()

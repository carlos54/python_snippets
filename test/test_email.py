import unittest
import os
import shutil
import json
from werkzeug.datastructures import FileStorage
from mailing.test import app, stc_path, app_template_path


class TestAppEmailV1(unittest.TestCase):

    def setUp(self):
        self.template_id = "unittest"
        shutil.copy2(os.path.join(stc_path, f"{self.template_id}.html"), app_template_path)
        
        self.version = "v1"
        self.current_client = app.test_client() 
    
    def tearDown(self):
        os.remove(os.path.join(app_template_path, f"{self.template_id}.html"))
 
 
    
    def test_post_and_get(self):
        # create new email job to test an id to perform the test
        data =  os.path.join(stc_path,"email_data_valide.json")
        file_to_transfer = FileStorage(
            stream=open(data, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
            f'/{self.version}/email',
            data={
                "template_id":self.template_id,
                "respondents": file_to_transfer,
                "test_recipients" : "mail1@statec.lu;mail2@statec.lu"
            },
            content_type="multipart/form-data"
            )

        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        id = data.get("id")

        r_email = self.current_client.get(f'/{self.version}/email/{id}')
        self.assertEqual(r_email.status_code, 200)
      
                  
    def _test_post(self):
        #with test_recipients
        data =  os.path.join(stc_path, "email_data_valide.json")
        file_to_transfer = FileStorage(
            stream=open(data, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
            f'/{self.version}/email',
            data={
                "template_id":self.template_id,
                "respondents": file_to_transfer,
                "test_recipients" : "mail1@statec.lu;mail2@statec.lu"
            },
            content_type="multipart/form-data"
            )

        self.assertEqual(r.status_code, 200)
        

if __name__ == '__main__':
   unittest.main()

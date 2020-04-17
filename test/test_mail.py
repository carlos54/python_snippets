import unittest
import os
import json
import shutil
from werkzeug.datastructures import FileStorage
from mailing.test import app, stc_path, app_template_path



class TestAppMailV1(unittest.TestCase):

    def setUp(self):
        self.template_id = "unittest"
        shutil.copy2(os.path.join(stc_path, f"{self.template_id}_fr.html"), app_template_path)
        shutil.copy2(os.path.join(stc_path, f"{self.template_id}_de.html"), app_template_path)
        shutil.copy2(os.path.join(stc_path, f"{self.template_id}_lu.html"), app_template_path)
        shutil.copy2(os.path.join(stc_path, f"{self.template_id}_en.html"), app_template_path)
       
        self.version = "v1"
        self.current_client = app.test_client() 
    
    def tearDown(self):
        os.remove(os.path.join(app_template_path, f"{self.template_id}_en.html"))
        os.remove(os.path.join(app_template_path, f"{self.template_id}_de.html"))
        os.remove(os.path.join(app_template_path, f"{self.template_id}_lu.html"))
        os.remove(os.path.join(app_template_path, f"{self.template_id}_fr.html"))
        
        
         
    def test_get(self):
        # create new mail job to test an id to perform the test
        data =  os.path.join(stc_path,"mail_data_valide.json")
        file_to_transfer = FileStorage(
            stream=open(data, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
            f'/{self.version}/mail',
            data={
                "template_id": self.template_id ,
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        id = data.get("id")
        
        r_mail = self.current_client.get(f'/{self.version}/mail/{id}')
        self.assertEqual(r_mail.status_code, 200)
      
      
    def test_post(self):
        # no data posted
        r = self.current_client.post( f'/{self.version}/mail')
        self.assertEqual(r.status_code, 403)
        
        data_file =  os.path.join(stc_path,"mail_data_valide.json")
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            content_type="application/json"
        )
        # bad paramater -> template_id
        r = self.current_client.post(
             f'/{self.version}/mail',
            data={
                "template_id_fake":"test",
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 403)
        
        # bad paramater -> respondents file
        r = self.current_client.post(
             f'/{self.version}/mail',
            data={
                "template_id": self.template_id  ,
                "respondents": None,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 403)
        
        
         # not valide schema data file
        data_notvalide =  os.path.join(stc_path ,"mail_data_notvalide.json")
        file_to_transfer = FileStorage(
            stream=open(data_notvalide, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
             f'/{self.version}/mail',
            data={
                "template_id": self.template_id  ,
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 403)
        

        # not corrupt data file
        data =  os.path.join(stc_path,"mail_data_corrupt.json")
        file_to_transfer = FileStorage(
            stream=open(data, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
             f'/{self.version}/mail',
            data={
                "template_id": self.template_id  ,
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 403)
        
        # template (id_temple/lang) not declare (no template test_pt.html)
        data =  os.path.join(stc_path,"mail_data_no_template.json")
        file_to_transfer = FileStorage(
            stream=open(data, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
             f'/{self.version}/mail',
            data={
                "template_id": self.template_id  ,
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 404)
        
        # data respondent not unique id
        data =  os.path.join(stc_path,"mail_data_not_unique.json")
        file_to_transfer = FileStorage(
            stream=open(data, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
             f'/{self.version}/mail',
            data={
                "template_id": self.template_id  ,
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 403)
        
        # ok
        data =  os.path.join(stc_path,"mail_data_valide.json")
        file_to_transfer = FileStorage(
            stream=open(data, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
             f'/{self.version}/mail',
            data={
                "template_id": self.template_id  ,
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 200)

        

if __name__ == '__main__':
   unittest.main()

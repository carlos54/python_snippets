import unittest
import os
from werkzeug.datastructures import FileStorage
from mailing.test import app, pwd



class TestAppMailV1(unittest.TestCase):

    def setUp(self):
        self.version = "v1"
        self.current_client = app.test_client() 
        
    def _test_debug(self):
        print("dedans")
        r = self.current_client.get(f'/{self.version}/debug')
        print(r)
         
    def _test_debug2(self):
        data =  os.path.join(pwd, "static/","mail_data_valide.json")
        file_to_transfer = FileStorage(
            stream=open(data, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
            f'/{self.version}/mail',
            data={
                "template_id":"test",
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 200)
        

      
    def test_post(self):
        # no data posted
        r = self.current_client.post( f'/{self.version}/mail')
        self.assertEqual(r.status_code, 403)
        
        data_file =  os.path.join(pwd, "static/","mail_data_valide.json")
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
                "template_id":"test",
                "respondents": None,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 403)
        
        
         # not valide schema data file
        data_notvalide =  os.path.join(pwd,
                                            "static/","mail_data_notvalide.json")
        file_to_transfer = FileStorage(
            stream=open(data_notvalide, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
             f'/{self.version}/mail',
            data={
                "template_id":"test",
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 403)
        

        # not corrupt data file
        data =  os.path.join(pwd, "static/","mail_data_corrupt.json")
        file_to_transfer = FileStorage(
            stream=open(data, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
             f'/{self.version}/mail',
            data={
                "template_id":"test",
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 403)
        
        # template (id_temple/lang) not declare (no template test_pt.html)
        data =  os.path.join(pwd, "static/","mail_data_no_template.json")
        file_to_transfer = FileStorage(
            stream=open(data, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
             f'/{self.version}/mail',
            data={
                "template_id":"test",
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 404)
        
        # data respondent not unique id
        data =  os.path.join(pwd, "static/","mail_data_not_unique.json")
        file_to_transfer = FileStorage(
            stream=open(data, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
             f'/{self.version}/mail',
            data={
                "template_id":"test",
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 403)
        
        # ok
        data =  os.path.join(pwd, "static/","mail_data_valide.json")
        file_to_transfer = FileStorage(
            stream=open(data, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
             f'/{self.version}/mail',
            data={
                "template_id":"test",
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 200)

        

if __name__ == '__main__':
   unittest.main()

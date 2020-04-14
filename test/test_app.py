
import unittest
import os
import blinker 
from flask_mail import Message, Mail
from werkzeug.datastructures import FileStorage
from api.app import app

PWD = os.path.dirname(__file__)

class TestAppTemplate(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.current_client = app.test_client()

    def _test_get(self):
        r = self.current_client.post('/faketemplate/fr')
        print(r)
        self.assertEqual(r.status_code, 404)


class TestAppEmail(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.current_client = app.test_client()

  
        
    def test_debug(self):
        data =  os.path.join(PWD, "static/","email_data_valide.json")
        file_to_transfer = FileStorage(
            stream=open(data, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
            '/email',
            data={
                "template_id":"email_test",
                "respondents": file_to_transfer,
                "test_recipients" : "mail1@statec.lu;mail2@statec.lu"
            },
            content_type="multipart/form-data"
            )
        print(r)
        #self.assertEqual(r.status_code, 200)
        
    def test_post(self):
        #with test_recipients
        data =  os.path.join(PWD, "static/","email_data_valide.json")
        file_to_transfer = FileStorage(
            stream=open(data, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
            '/email',
            data={
                "template_id":"email_test",
                "respondents": file_to_transfer,
                "test_recipients" : "mail1@statec.lu;mail2@statec.lu"
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 200)

class TestAppMail(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.current_client = app.test_client()

    def _test_debug(self):
        data =  os.path.join(PWD, "static/","mail_data_valide.json")
        file_to_transfer = FileStorage(
            stream=open(data, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
            '/mail',
            data={
                "template_id":"test",
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        print(r)
        #self.assertEqual(r.status_code, 200)
        

      
    def _test_post(self):
        # no data posted
        r = self.current_client.post('/mail')
        self.assertEqual(r.status_code, 403)
        
        data_file =  os.path.join(PWD, "static/","mail_data_valide.json")
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            content_type="application/json"
        )
        # bad paramater -> template_id
        r = self.current_client.post(
            '/mail',
            data={
                "template_id_fake":"test",
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 403)
        
        # bad paramater -> respondents file
        r = self.current_client.post(
            '/mail',
            data={
                "template_id":"test",
                "respondents": None,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 403)
        
        
         # not valide schema data file
        data_notvalide =  os.path.join(PWD,
                                            "static/","mail_data_notvalide.json")
        file_to_transfer = FileStorage(
            stream=open(data_notvalide, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
            '/mail',
            data={
                "template_id":"test",
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 403)
        

        # not corrupt data file
        data =  os.path.join(PWD, "static/","mail_data_corrupt.json")
        file_to_transfer = FileStorage(
            stream=open(data, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
            '/mail',
            data={
                "template_id":"test",
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 403)
        
        # template (id_temple/lang) not declare (no template test_pt.html)
        data =  os.path.join(PWD, "static/","mail_data_no_template.json")
        file_to_transfer = FileStorage(
            stream=open(data, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
            '/mail',
            data={
                "template_id":"test",
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 404)
        
        # data respondent not unique id
        data =  os.path.join(PWD, "static/","mail_data_not_unique.json")
        file_to_transfer = FileStorage(
            stream=open(data, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
            '/mail',
            data={
                "template_id":"test",
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 403)
        
        # ok
        data =  os.path.join(PWD, "static/","mail_data_valide.json")
        file_to_transfer = FileStorage(
            stream=open(data, "rb"),
            content_type="application/json"
        )
        r = self.current_client.post(
            '/mail',
            data={
                "template_id":"test",
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 200)

        

if __name__ == '__main__':
    unittest.main()

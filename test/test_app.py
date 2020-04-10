
import unittest
import os
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


class TestAppMail(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.current_client = app.test_client()

    def _test_debug(self):
        data =  os.path.join(PWD, "static/","data_valide.json")
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
        

      
    def test_post(self):
        # no data posted
        r = self.current_client.post('/mail')
        self.assertEqual(r.status_code, 403)
        
        data_file =  os.path.join(PWD, "static/","data_valide.json")
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
                                            "static/","data_notvalide.json")
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
        data =  os.path.join(PWD, "static/","data_corrupt.json")
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
        data =  os.path.join(PWD, "static/","data_no_template.json")
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
        data =  os.path.join(PWD, "static/","data_not_unique.json")
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
        data =  os.path.join(PWD, "static/","data_valide.json")
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
        
    
        # r = self.current_client.post('/apply_pdf_template/fake_name')
      # self.assertEqual(r.status_code, 404)

        

        """
        # Given
                payload = json.dumps({
                    "email": "paurakh011@gmail.com",
                    "password": "mycoolpassword"
                })

                # When
                response = self.app.post('/api/auth/signup', headers={"Content-Type": "application/json"}, data=payload)

                # Then
                self.assertEqual(str, type(response.json['id']))
                self.assertEqual(200, response.status_code)
                """

        

if __name__ == '__main__':
    unittest.main()

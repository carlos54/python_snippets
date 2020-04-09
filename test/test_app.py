
import unittest
import os
from werkzeug.datastructures import FileStorage


from api.app import app

PWD = os.path.dirname(__file__)


class TestApp(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.current_client = app.test_client()
        
    def test_debug(self):
        data_file =  os.path.join(PWD, "static/","data_valide.json")
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            filename="data_valide.json",
            content_type="application/json"
        )
        r = self.current_client.post(
            '/print',
            data={
                "template_id":"test",
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 200)
        
    def _test_template_get(self):
        r = self.current_client.post('/faketemplate/fr')
        print(r)
        self.assertEqual(r.status_code, 404)
      
    def _test_print_post(self):
        # no data
        r = self.current_client.post('/print')
        self.assertEqual(r.status_code, 403)
        
        data_file =  os.path.join(PWD, "static/","data_valide.json")
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            filename="data_valide.json",
            content_type="application/json"
        )
        # bad paramater -> template_id
        r = self.current_client.post(
            '/print',
            data={
                "template_id_fake":"test",
                "respondents": file_to_transfer,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 403)
        
        # bad paramater -> respondents file
        r = self.current_client.post(
            '/print',
            data={
                "template_id":"test",
                "respondents": None,
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r.status_code, 403)
        
        # ok
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            filename="data_valide.json",
            content_type="application/json"
        )
        r = self.current_client.post(
            '/print',
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

    def tearDown(self):
        # print("tearDown")
        pass




        

if __name__ == '__main__':
    unittest.main()

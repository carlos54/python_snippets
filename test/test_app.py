import unittest
import json

from api.app import app


class TestApp(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.current_client = app.test_client()

    def test_home(self):
        r = self.current_client.get('/apply_pdf_template')
        #print(r.status_code)
        

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
        pass
       # print("tearDown")
        
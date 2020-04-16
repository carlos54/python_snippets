import unittest
import os
import json
import secrets
import shutil
from jsonschema import validate, ValidationError
import string
from werkzeug.datastructures import FileStorage
from mailing.test import app, tps_path, stc_path, app_template_path


class TestAppTemplateV1(unittest.TestCase):

    def setUp(self):
        self.version = "v1"
        self.current_client = app.test_client() 
    
    def test_debug(self):
        pass
            
    def test_template_get(self):
        r = self.current_client.get(f'/{self.version}/template')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertIsInstance(data, list)
        
        with open(os.path.join(stc_path, "validator_template_get_v1.schema")) as f:
            try:
                validate(instance=data, schema=json.loads(f.read()))
            except ValidationError:
                self.assertTrue(False, "not valide data retrun **validator_template_get_v1.schema**")
    
    def test_template_lang_post(self):
        # lang not allowed
        lang = "FRe"
        data_file =  os.path.join(stc_path, "fake_template.html")
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            content_type="text/HTML; charset=utf-8"
        )
        r = self.current_client.post(
            f'/{self.version}/template/{lang}',
            data={
                "template_id": "unittest",
                "html_file": file_to_transfer
            },
            content_type="multipart/form-data"
            )
        self.assertTrue("lang not allowed" in r.data.decode("utf-8"))
        self.assertEqual(r.status_code, 403)
        
        # special charactere in template_id
        lang = "FR"
        data_file =  os.path.join(stc_path, "fake_template.html")
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            content_type="text/HTML; charset=utf-8"
        )
        r = self.current_client.post(
            f'/{self.version}/template/{lang}',
            data={
                "template_id": "unit.test",
                "html_file": file_to_transfer
            },
            content_type="multipart/form-data"
            )
        self.assertTrue("template_id - special character not allowed" in r.data.decode("utf-8"))
        self.assertEqual(r.status_code, 403)
        
        
        # missing file
        lang = "FR"
       
        r = self.current_client.post(
            f'/{self.version}/template/{lang}',
            data={
                "template_id": "testABC",
                "html_file": ""
            },
            content_type="multipart/form-data"
            )
        self.assertTrue("missing data file" in r.data.decode("utf-8"))
        self.assertEqual(r.status_code, 403)
        
         # not html file
        lang = "FR"
        data_file =  os.path.join(stc_path, "do_not_delete.pdf")
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            content_type="text/HTML; charset=utf-8"
        )
        r = self.current_client.post(
            f'/{self.version}/template/{lang}',
            data={
                "template_id": "testABC",
                "html_file": file_to_transfer
            },
            content_type="multipart/form-data"
            )
        self.assertTrue("html_file is not html" in r.data.decode("utf-8"))
        self.assertEqual(r.status_code, 403)
        
        # ok
        lang = "FR"
        template_id = secrets.token_hex(8)
        data_file =  os.path.join(stc_path, "fake_template.html")
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            content_type="text/HTML; charset=utf-8"
        )
        r_valide= self.current_client.post(
            f'/{self.version}/template/{lang}',
            data={
                "template_id":template_id ,
                "html_file": file_to_transfer
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r_valide.status_code, 200)
        data_valide = json.loads(r_valide.data)
        self.assertEqual(data_valide.get('success'), True)
        
        # template existe already (just loaded from previous check)
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            content_type="text/HTML; charset=utf-8"
        )
        r = self.current_client.post(
            f'/{self.version}/template/{lang}',
            data={
                "template_id": template_id,
                "html_file": file_to_transfer
            },
            content_type="multipart/form-data"
            )
        self.assertTrue("template already exist" in r.data.decode("utf-8"))
        self.assertEqual(r.status_code, 403)
        #purge template juste create
        os.remove(os.path.join(app_template_path, data_valide.get('template_name')))
    
    
    
    def test_template_post(self):
        # special charactere in template_id
        data_file =  os.path.join(stc_path, "fake_template.html")
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            content_type="text/HTML; charset=utf-8"
        )
        r = self.current_client.post(
            f'/{self.version}/template',
            data={
                "template_id": "unit. test",
                "html_file": file_to_transfer
            },
            content_type="multipart/form-data"
            )
        self.assertTrue("template_id - special character not allowed" in r.data.decode("utf-8"))
        self.assertEqual(r.status_code, 403)
        
        # missing file
        r = self.current_client.post(
            f'/{self.version}/template',
            data={
                "template_id": "testABC",
                "html_file": ""
            },
            content_type="multipart/form-data"
            )
        self.assertTrue("missing data file" in r.data.decode("utf-8"))
        self.assertEqual(r.status_code, 403)
        
         # not html file
        data_file =  os.path.join(stc_path, "do_not_delete.pdf")
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            content_type="text/HTML; charset=utf-8"
        )
        r = self.current_client.post(
            f'/{self.version}/template',
            data={
                "template_id": "testABC",
                "html_file": file_to_transfer
            },
            content_type="multipart/form-data"
            )
        self.assertTrue("html_file is not html" in r.data.decode("utf-8"))
        self.assertEqual(r.status_code, 403)
        
        # ok
        template_id = secrets.token_hex(8)
        data_file =  os.path.join(stc_path, "fake_template.html")
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            content_type="text/HTML; charset=utf-8"
        )
        r_valide= self.current_client.post(
            f'/{self.version}/template',
            data={
                "template_id":template_id ,
                "html_file": file_to_transfer
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r_valide.status_code, 200)
        data_valide = json.loads(r_valide.data)
        self.assertEqual(data_valide.get('success'), True)
        
        # template existe already (just loaded from previous check)
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            content_type="text/HTML; charset=utf-8"
        )
        r = self.current_client.post(
            f'/{self.version}/template',
            data={
                "template_id": template_id,
                "html_file": file_to_transfer
            },
            content_type="multipart/form-data"
            )
        self.assertTrue("template already exist" in r.data.decode("utf-8"))
        self.assertEqual(r.status_code, 403)
        #purge template juste create
        os.remove(os.path.join(app_template_path, data_valide.get('template_name')))    


    def test_template_lang_delete(self):
        # copy fake template in app dir templates so it can be deleted
        template_id = "1234megafake"
        lang = "fr"
        shutil.copy2(os.path.join(stc_path, f"{template_id}_{lang}.html"), app_template_path)

        ### ok test 
        r = self.current_client.delete(f'/{self.version}/template/{template_id}/{lang}')
        self.assertEqual(r.status_code, 200)
        data_valide = json.loads(r.data)
        self.assertEqual(data_valide.get('success'), True)
       
        ## template doesn't exist
        r = self.current_client.delete(f'/{self.version}/template/fake/{lang}')
        self.assertTrue("template doesn't exist" in r.data.decode("utf-8"))
        self.assertEqual(r.status_code, 403)
       
    
    def test_template_delete(self):
         # copy fake template in app dir templates so it can be deleted
        template_id = "1234megafake"
        shutil.copy2(os.path.join(stc_path, f"{template_id}.html"), app_template_path)

        ### ok test 
        r = self.current_client.delete(f'/{self.version}/template/{template_id}')
        self.assertEqual(r.status_code, 200)
        data_valide = json.loads(r.data)
        self.assertEqual(data_valide.get('success'), True)
       
        ## template doesn't exist
        r = self.current_client.delete(f'/{self.version}/template/fake')
        self.assertTrue("template doesn't exist" in r.data.decode("utf-8"))
        self.assertEqual(r.status_code, 403)
         

    
    def test_template_put(self):
        # copy fake template in app dir templates so it can be updated
        template_id = "1234megafake"
        shutil.copy2(os.path.join(stc_path, f"{template_id}.html"), app_template_path)
     
        #### ok test 
        data_file =  os.path.join(stc_path, "fake_template.html")
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            content_type="text/HTML; charset=utf-8"
        )
        r_valide= self.current_client.put(
            f'/{self.version}/template/{template_id}',
            data={
                "html_file": file_to_transfer
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r_valide.status_code, 200)
        data_valide = json.loads(r_valide.data)
        self.assertEqual(data_valide.get('success'), True)
        
    
    
        # special charactere in template_id
        data_file =  os.path.join(stc_path, "fake_template.html")
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            content_type="text/HTML; charset=utf-8"
        )
        r = self.current_client.put(
            f'/{self.version}/template/abc.abc',
            data={
                "html_file": file_to_transfer
            },
            content_type="multipart/form-data"
            )
        self.assertTrue("template_id - special character not allowed" in r.data.decode("utf-8"))
        self.assertEqual(r.status_code, 403)
        
        # missing file
        r = self.current_client.put(
            f'/{self.version}/template/{template_id}',
            data={
                "html_file": ""
            },
            content_type="multipart/form-data"
            )
        self.assertTrue("missing data file" in r.data.decode("utf-8"))
        self.assertEqual(r.status_code, 403)
        
        # not html file
        data_file =  os.path.join(stc_path, "do_not_delete.pdf")
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            content_type="text/HTML; charset=utf-8"
        )
        r = self.current_client.put(
            f'/{self.version}/template/{template_id}',
            data={
                "html_file": file_to_transfer
            },
            content_type="multipart/form-data"
            )
        self.assertTrue("html_file is not html" in r.data.decode("utf-8"))
        self.assertEqual(r.status_code, 403)
        
        
        
        # template does not existe already (just loaded from previous check)
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            content_type="text/HTML; charset=utf-8"
        )
        r = self.current_client.put(
            f'/{self.version}/template/fake',
            data={
                "html_file": file_to_transfer
            },
            content_type="multipart/form-data"
            )
        self.assertTrue("template doesn't exist" in r.data.decode("utf-8"))
        self.assertEqual(r.status_code, 403)
       
        #purge template juste copied
        os.remove(os.path.join(app_template_path,  f"{template_id}.html"))
    
    def test_template_lang_put(self):
        # copy fake template in app dir templates so it can be updated
        template_id = "1234megafake"
        lang = "fr"
        shutil.copy2(os.path.join(stc_path, f"{template_id}_{lang}.html"), app_template_path)
     
        #### ok test 
        data_file =  os.path.join(stc_path, "fake_template.html")
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            content_type="text/HTML; charset=utf-8"
        )
        r_valide= self.current_client.put(
            f'/{self.version}/template/{template_id}/{lang}',
            data={
                "html_file": file_to_transfer
            },
            content_type="multipart/form-data"
            )
        self.assertEqual(r_valide.status_code, 200)
        data_valide = json.loads(r_valide.data)
        self.assertEqual(data_valide.get('success'), True)

    
    
        # special charactere in template_id
        data_file =  os.path.join(stc_path, "fake_template.html")
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            content_type="text/HTML; charset=utf-8"
        )
        r = self.current_client.put(
            f'/{self.version}/template/abc.abc/{lang}',
            data={
                "html_file": file_to_transfer
            },
            content_type="multipart/form-data"
            )
        self.assertTrue("template_id - special character not allowed" in r.data.decode("utf-8"))
        self.assertEqual(r.status_code, 403)
        
        # missing file
        r = self.current_client.put(
            f'/{self.version}/template/{template_id}/{lang}',
            data={
                "html_file": ""
            },
            content_type="multipart/form-data"
            )
        self.assertTrue("missing data file" in r.data.decode("utf-8"))
        self.assertEqual(r.status_code, 403)
        
        # not html file
        data_file =  os.path.join(stc_path, "do_not_delete.pdf")
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            content_type="text/HTML; charset=utf-8"
        )
        r = self.current_client.put(
            f'/{self.version}/template/{template_id}/{lang}',
            data={
                "html_file": file_to_transfer
            },
            content_type="multipart/form-data"
            )
        self.assertTrue("html_file is not html" in r.data.decode("utf-8"))
        self.assertEqual(r.status_code, 403)
        
        
        
        # template does not existe already (just loaded from previous check)
        file_to_transfer = FileStorage(
            stream=open(data_file, "rb"),
            content_type="text/HTML; charset=utf-8"
        )
        r = self.current_client.put(
            f'/{self.version}/template/fake/{lang}',
            data={
                "html_file": file_to_transfer
            },
            content_type="multipart/form-data"
            )
        self.assertTrue("template doesn't exist" in r.data.decode("utf-8"))
        self.assertEqual(r.status_code, 403)
       
        #purge template juste copied
        os.remove(os.path.join(app_template_path,  f"{template_id}_{lang}.html"))
       
if __name__ == '__main__':
   unittest.main()

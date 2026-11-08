import base64,io,json,unittest
from unittest.mock import Mock
from PIL import Image,PngImagePlugin
from student_photo_ai import Budget,clean_image,interpret

def image():
    b=io.BytesIO();meta=PngImagePlugin.PngInfo();meta.add_text('patient','synthetic-test')
    Image.new('RGB',(20,20),'white').save(b,format='PNG',pnginfo=meta)
    return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()

class AITests(unittest.TestCase):
    def test_metadata_removed(self):
        out=clean_image(image());im=Image.open(io.BytesIO(base64.b64decode(out.split(',')[1])))
        self.assertFalse(im.info);self.assertEqual(im.size,(20,20))
    def test_reject_bad_inputs_before_network(self):
        opener=Mock()
        for value in [None,'https://example.org/photo.png','data:image/png;base64,!!!','data:image/png;base64,YWJj']:
            with self.assertRaises(Exception):interpret(value,'secret','model',opener)
        opener.assert_not_called()
    def test_request_and_output(self):
        result={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'Eğitim taslağı'}]}]}
        def opener(req,timeout):
            self.assertEqual(timeout,60);p=json.loads(req.data)
            self.assertFalse(p['store']);self.assertNotIn('tools',p)
            self.assertEqual(p['input'][0]['content'][1]['detail'],'high')
            self.assertNotIn('synthetic-test',p['input'][0]['content'][1]['image_url'])
            return io.BytesIO(json.dumps(result).encode())
        self.assertEqual(interpret(image(),'secret','gpt-4.1',opener),'Eğitim taslağı')
    def test_incomplete_not_presented_as_report(self):
        with self.assertRaises(ValueError):
            interpret(image(),'s','m',lambda *a,**k:io.BytesIO(b'{"status":"incomplete"}'))
    def test_limits_and_expiry(self):
        b=Budget()
        for i in range(5):self.assertTrue(b.reserve('user',0))
        self.assertFalse(b.reserve('user',1))
        for i in range(25):self.assertTrue(b.reserve(str(i),0))
        self.assertFalse(b.reserve('other',1));self.assertTrue(b.reserve('user',3601))
if __name__=='__main__':unittest.main()

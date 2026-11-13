import base64,io,json,unittest
from unittest.mock import Mock,patch
from types import SimpleNamespace
from PIL import Image,PngImagePlugin
from student_photo_ai import Budget,clean_image,interpret,ai_allowed,render

def image():
    b=io.BytesIO();meta=PngImagePlugin.PngInfo();meta.add_text('patient','synthetic-test')
    Image.new('RGB',(20,20),'white').save(b,format='PNG',pnginfo=meta)
    return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()

class AITests(unittest.TestCase):
    def test_only_admin_can_enable_ai(self):
        config={'enabled':True,'api_key':'test','model':'gpt-4.1'}
        for identity in [None,{}, {'role':'student'}, {'role':'resident'}, {'role':'owner'}]:
            self.assertFalse(ai_allowed(config,identity))
        self.assertTrue(ai_allowed(config,{'role':'admin'}))
        for key,value in [('enabled',False),('api_key',''),('model','')]:
            self.assertFalse(ai_allowed(dict(config,**{key:value}),{'role':'admin'}))
    def test_forged_student_event_never_calls_api(self):
        event={'id':'12345678-1234-1234-1234-123456789012','consent':True,'image':image()}
        st=SimpleNamespace(secrets={'photo_ai':{'enabled':True,'api_key':'test','model':'gpt-4.1'}},
            session_state={'identity':{'username':'learner','role':'student'}},warning=Mock(),caption=Mock())
        widget=Mock(return_value=event)
        with patch('streamlit.components.v1.declare_component',return_value=widget), patch('student_photo_ai.interpret') as api:
            render(st)
        api.assert_not_called()
        self.assertFalse(widget.call_args.kwargs['enabled'])
        st.warning.assert_called_once()
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

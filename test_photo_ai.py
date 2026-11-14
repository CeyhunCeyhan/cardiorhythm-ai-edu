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
    def test_admin_selection_requires_explicit_image_send(self):
        config={'enabled':True,'api_key':'test','model':'gpt-4.1'}
        st=SimpleNamespace(secrets={'photo_ai':config},session_state={'identity':{'username':'teacher','role':'admin'}},
            caption=Mock(),info=Mock(),selectbox=Mock(return_value='gpt-6.1-sol'))
        widget=Mock(return_value=None)
        with patch('streamlit.components.v1.declare_component',return_value=widget), patch('student_photo_ai.interpret') as api:
            render(st)
        api.assert_not_called()
        self.assertEqual(st.selectbox.call_args.args[1],['gpt-4.1','gpt-6.1-sol'])
        self.assertEqual(widget.call_args.kwargs['key'],'photo_ai_widget_gpt-6.1-sol')
        self.assertEqual(config['model'],'gpt-4.1')
    def test_receipt_requires_matching_reply_and_never_resends(self):
        rid='12345678-1234-1234-1234-123456789012'
        state={'identity':{'role':'admin'},'photo_ai_reply':{'id':rid,'trace':'testtrace','text':'private'}}
        st=SimpleNamespace(secrets={},session_state=state,caption=Mock(),selectbox=Mock(return_value='test'))
        events=[{'type':'ack','id':v} for v in ['other',rid,rid]]
        with patch('streamlit.components.v1.declare_component',return_value=Mock(side_effect=events)), patch('student_photo_ai.interpret') as api, patch('builtins.print') as log:
            for _ in events: render(st)
        api.assert_not_called()
        log.assert_called_once_with('photo_ai','testtrace','client_received',flush=True)
        self.assertNotIn('photo_ai_reply',state)

    def test_free_probe_round_trip(self):
        state={'identity':{'role':'admin'}}
        st=SimpleNamespace(secrets={},session_state=state,caption=Mock(),selectbox=Mock(return_value='test'),rerun=Mock())
        nonce='abcd'*9
        widget=Mock(return_value={'type':'ping','id':nonce})
        with patch('streamlit.components.v1.declare_component',return_value=widget), patch('student_photo_ai.interpret') as api:
            render(st);render(st)
        self.assertEqual(widget.call_args.kwargs['pong'],nonce)
        st.rerun.assert_called_once()
        api.assert_not_called()

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
    def test_candidate_request_keeps_prompt_image_and_privacy(self):
        def opener(req,timeout):
            payload=json.loads(req.data)
            self.assertEqual(payload['model'],'gpt-6.1-sol')
            self.assertEqual(payload['reasoning'],{'effort':'high'})
            self.assertEqual(payload['max_output_tokens'],6000)
            self.assertEqual(timeout,120)
            self.assertFalse(payload['store'])
            self.assertNotIn('tools',payload)
            self.assertEqual(payload['input'][0]['content'][1]['detail'],'high')
            return io.BytesIO(b'{"status":"completed","output":[{"type":"message","content":[{"type":"output_text","text":"candidate"}]}]}')
        self.assertEqual(interpret(image(),'test','gpt-6.1-sol',opener),'candidate')
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

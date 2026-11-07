import unittest
from streamlit.testing.v1 import AppTest
from student_cases import CASES,waveform
from student_access import LoginGuard
from security import make_hash
HASH=make_hash('test-only-password-123')
USERS={'learner':{'role':'student','password_hash':HASH},'teacher':{'role':'admin','password_hash':HASH}}
def app(approved=None):
 a=AppTest.from_file('student_app.py',default_timeout=20)
 a.secrets['users']=USERS
 a.secrets['student_edition']={'approved_cases':list(CASES) if approved is None else approved}
 return a.run()
def login(a,name='learner'):
 a.text_input[0].set_value(name);a.text_input[1].set_value('test-only-password-123');return a.button[0].click().run()
class Tests(unittest.TestCase):
 def test_missing_secrets_fails_closed(self):
  a=AppTest.from_file('student_app.py').run();self.assertEqual(len(a.selectbox),0);self.assertTrue(a.error)
 def test_unapproved_hidden(self):
  a=login(app([]));self.assertFalse(a.exception);self.assertEqual(len(a.selectbox),0)
 def test_admin_preview(self):
  a=login(app([]),'teacher');self.assertFalse(a.exception);self.assertEqual(len(a.selectbox[0].options),5)
 def test_all_cases_feedback(self):
  a=login(app())
  for k in CASES:
   a.selectbox[0].select(k).run();a.radio[1].set_value(CASES[k]['answer']);a.button[1].click().run()
   self.assertFalse(a.exception);self.assertTrue(a.success)
  self.assertEqual(len(a.session_state['answers']),5)
 def test_rate_feedback_separate(self):
  a=login(app());a.selectbox[0].select('variable').run()
  a.radio[1].set_value(CASES['variable']['answer']);a.number_input[0].set_value(80)
  a.button[1].click().run()
  self.assertFalse(a.exception)
  text=' '.join(x.value for x in a.markdown)
  self.assertIn('Tahmininiz: 80 /dk',text);self.assertIn('64.6 /dk',text);self.assertIn('+15.4 /dk',text)
 def test_zero_rate_unanswered(self):
  a=login(app());a.radio[1].set_value('Düzenli');a.button[1].click().run()
  self.assertFalse(a.exception)
  self.assertTrue(any('Hız tahmini yanıtlanmadı' in x.value for x in a.warning))
 def test_noise_uncertainty_and_resubmit(self):
  a=login(app());a.selectbox[0].select('noise').run()
  a.radio[1].set_value(CASES['noise']['answer']);a.number_input[0].set_value(80)
  a.checkbox[0].check();a.button[1].click().run()
  self.assertFalse(a.exception);self.assertIsNone(a.session_state['answers']['noise']['rate'])
  self.assertTrue(any('Sayısal tahmininiz değerlendirilmedi' in x.value for x in a.info))
  a.checkbox[0].uncheck();a.number_input[0].set_value(60);a.button[1].click().run()
  self.assertFalse(a.exception);self.assertEqual(a.session_state['answers']['noise']['rate'],60)
  a.selectbox[0].select('regular60').run();self.assertEqual(len(a.checkbox),0)
 def test_isolation_and_logout(self):
  a=login(app());a.radio[1].set_value('Düzenli');a.button[1].click().run()
  b=login(app())
  with self.assertRaises(KeyError): b.session_state['answers']
  a.button[0].click().run()
  with self.assertRaises(KeyError): a.session_state['answers']
  self.assertEqual(len(a.selectbox),0)
 def test_revoked_role(self):
  a=login(app());a.secrets['users']={};a.run();self.assertEqual(len(a.selectbox),0)
 def test_guard(self):
  g=LoginGuard()
  for i in range(5):self.assertIsNone(g.authenticate('learner','bad',USERS,now=i)[0])
  self.assertIsNone(g.authenticate('learner','test-only-password-123',USERS,now=10)[0])
  self.assertIsNotNone(g.authenticate('learner','test-only-password-123',USERS,now=310)[0])
 def test_waveforms(self):
  for k in CASES:
   t,y,b,fs=waveform(k);self.assertEqual(len(t),16*fs);self.assertTrue((b[1:]>b[:-1]).all())
if __name__=='__main__':unittest.main()

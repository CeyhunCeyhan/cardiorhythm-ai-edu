"""Focused integration tests; no patient images or secrets."""
import unittest
from streamlit.testing.v1 import AppTest
from security import make_hash
from student_cases import CASES
class PhotoTests(unittest.TestCase):
 def app(self,login=True):
  a=AppTest.from_file('student_app.py',default_timeout=20)
  a.secrets['users']={'learner':{'role':'student','password_hash':make_hash('test-photo-password')}}
  a.secrets['student_edition']={'approved_cases':list(CASES)}
  a.run()
  if login:
   a.text_input[0].set_value('learner');a.text_input[1].set_value('test-photo-password');a.button[0].click().run()
  return a
 def test_auth_gate(self):
  a=self.app(False);self.assertEqual(len(a.get('iframe')),0);self.assertFalse(a.radio)
 def test_photo_and_return(self):
  a=self.app();self.assertEqual(len(a.selectbox[0].options),5)
  a.radio(key='workspace_mode').set_value('EKG fotoğrafı inceleme').run()
  self.assertFalse(a.exception);self.assertEqual(len(a.get('iframe')),1);self.assertEqual(len(a.selectbox),0)
  a.radio(key='workspace_mode').set_value('Sentetik alıştırmalar').run()
  self.assertFalse(a.exception);self.assertEqual(len(a.selectbox[0].options),5)
 def test_answer_survives_mode_switch_and_logout(self):
  a=self.app();a.radio(key='choice_regular60').set_value('Düzenli');a.number_input[0].set_value(60);a.button[1].click().run()
  a.radio(key='workspace_mode').set_value('EKG fotoğrafı inceleme').run()
  self.assertEqual(a.session_state['answers']['regular60']['rate'],60)
  a.button[0].click().run();self.assertEqual(len(a.get('iframe')),0)
if __name__=='__main__':unittest.main()

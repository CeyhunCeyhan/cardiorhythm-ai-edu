"""Process-wide bounded login limiter; per-session identity stays in Streamlit."""
import hashlib,time,threading
from security import verify_password

class LoginGuard:
 def __init__(self):
  self.entries={};self.lock=threading.Lock()
 def authenticate(self,username,password,users,now=None):
  now=time.monotonic() if now is None else now
  key=hashlib.sha256(username.encode()).hexdigest()
  # Lock covers the check/update pair. Never store supplied passwords.
  with self.lock:
   self.entries={k:v for k,v in self.entries.items() if now-v[2]<900}
   count,until,_=self.entries.get(key,(0,0,now))
   if now<until:return None,'Çok fazla deneme. Beş dakika sonra tekrar deneyin.'
   if key not in self.entries and len(self.entries)>=1024:
    return None,'Giriş geçici olarak yoğun. Lütfen daha sonra deneyin.'
   user=users.get(username,{})
   valid=verify_password(password,user.get('password_hash',''))
   if valid and user.get('role') in ('student','resident','admin'):
    self.entries.pop(key,None)
    return {'username':username,'role':user['role']},''
   count+=1
   self.entries[key]=(0 if count>=5 else count,now+300 if count>=5 else 0,now)
   return None,'Kullanıcı adı veya şifre hatalı.'

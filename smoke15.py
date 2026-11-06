from concurrent.futures import ProcessPoolExecutor
import json,time

def one(i):
 from test_student import app,login
 a=login(app());a.selectbox[0].select('regular60').run();a.radio[0].set_value('Düzenli');a.button[1].click().run()
 assert not a.exception
 assert len(a.session_state['answers'])==1
 a.button[0].click().run()
 assert len(a.selectbox)==0
 return i
if __name__=='__main__':
 started=time.monotonic()
 with ProcessPoolExecutor(max_workers=15) as pool: done=list(pool.map(one,range(15)))
 print(json.dumps({'isolated_process_sessions_passed':len(done),'seconds':round(time.monotonic()-started,2),'limitation':'AppTest processes, not real browsers or shared-host load test'}))

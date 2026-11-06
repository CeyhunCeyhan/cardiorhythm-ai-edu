"""Mobile educational entrypoint, independent of research validation app."""
import json,time
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from student_cases import CASES,OPTIONS,waveform
from student_access import LoginGuard

st.set_page_config(page_title='CardioRhythm AI – Student Edition',page_icon='🫀',layout='centered')
st.title('CardioRhythm AI')
st.caption('Student Edition · Ders öncesi pilot')
st.info('Sentetik EKG alıştırmaları · Hasta verisi içermez. Klinik tanı veya tedavi için kullanılmaz.')

@st.cache_resource
def login_guard():return LoginGuard()

def reset_session():
 for key in list(st.session_state):del st.session_state[key]

try:users=st.secrets['users']
except (KeyError,FileNotFoundError):
 st.error('Ders hesapları henüz yapılandırılmamış. Eğiticinize başvurun.');st.stop()
if not users:
 st.error('Ders hesapları henüz yapılandırılmamış.');st.stop()
if st.session_state.get('identity') and time.monotonic()-st.session_state.get('last_activity',0)>1800:
 reset_session();st.info('Oturumunuz sona erdi. Yeniden giriş yapın.')
if not st.session_state.get('identity'):
 with st.form('login',clear_on_submit=True):
  name=st.text_input('Kullanıcı adı',max_chars=80)
  password=st.text_input('Şifre',type='password',max_chars=256)
  submitted=st.form_submit_button('Giriş yap',type='primary',use_container_width=True)
 if submitted:
  identity,error=login_guard().authenticate(name.strip().lower(),password,users)
  if identity:
   st.session_state.identity=identity;st.session_state.last_activity=time.monotonic();st.rerun()
  else:st.error(error)
 st.stop()
identity=st.session_state.identity
# Re-check authorization so removing an account revokes existing sessions on rerun.
if users.get(identity['username'],{}).get('role')!=identity['role']:
 reset_session();st.rerun()
st.session_state.last_activity=time.monotonic()
is_admin=identity['role']=='admin'
st.caption('Eğitici' if is_admin else 'Öğrenci oturumu')
if st.button('Çıkış yap'):
 reset_session();st.rerun()
settings=st.secrets.get('student_edition',{})
approved=set(settings.get('approved_cases',[])) & set(CASES)
available=list(CASES) if is_admin else [c for c in CASES if c in approved]
if is_admin:
 st.warning('Vaka açıklamaları eğitici incelemesi bekliyor. Öğrenciler yalnızca onaylanan vakaları görür.')
 with st.expander('Ders hazırlığı'):
  st.write('Vakaları inceleyin. Onayladığınız kimlikleri Streamlit Secrets içindeki student_edition.approved_cases listesine ekleyin.')
  st.code('approved_cases = '+json.dumps(list(CASES)))
  st.caption('Bu liste hesap bilgisi içermez. İlk ders öncesi gerçek telefon ve 15 oturum provası gerekir.')
if not available:
 st.info('Eğiticiniz henüz vaka açmadı.');st.stop()
case_id=st.selectbox('Alıştırma seç',available,format_func=lambda k:CASES[k]['title'])
case=CASES[case_id]
if case_id not in approved:st.caption('Eğitici önizlemesi · Öğrencilere kapalı')
t,y,beats,fs=waveform(case_id)
start=st.slider('Şeridin başlangıcı (s)',0,10,0,key='start_'+case_id)
mask=(t>=start)&(t<start+6)
fig=go.Figure(go.Scatter(x=t[mask],y=y[mask],mode='lines',line=dict(color='#17324D',width=1.5),name='Sentetik sinyal'))
fig.update_layout(height=320,margin=dict(l=15,r=10,t=15,b=30),xaxis_title='Saniye',yaxis_title='mV',dragmode='pan',showlegend=False)
fig.update_xaxes(dtick=.2,gridcolor='#efd5d5',range=[start,start+6])
fig.update_yaxes(gridcolor='#efd5d5',range=[-.7,1.5])
st.plotly_chart(fig,use_container_width=True,config={'displaylogo':False,'scrollZoom':False})
st.caption('6 saniyelik görünüm · Grafik araçlarıyla yakınlaştırabilirsiniz. Ekran boyutu kâğıt kalibrasyonu değildir.')
with st.form('answer_'+case_id):
 answer=st.radio('16 saniyelik alıştırmanın tamamında hangi özellik öne çıkıyor?',OPTIONS,index=None,key='choice_'+case_id)
 estimate=st.number_input('16 saniyelik kaydın ortalama hızı için tahmininiz (/dk)',min_value=0,max_value=300,value=0,key='rate_'+case_id)
 submitted=st.form_submit_button('Yanıtımı kontrol et',use_container_width=True)
if submitted:
 if answer is None:st.warning('Önce bir seçenek işaretleyin.')
 else:
  answers=dict(st.session_state.get('answers',{}));answers[case_id]={'answer':answer,'rate':estimate};st.session_state.answers=answers
saved=st.session_state.get('answers',{}).get(case_id)
if saved:
 if saved['answer']==case['answer']:st.success('Bu alıştırmanın hedeflediği özelliği seçtiniz.')
 else:st.info('Birlikte karşılaştıralım: '+case['answer'])
 st.write(case['note'])
 st.metric('Üretim zamanlarından hesaplanan ortalama hız',f'{60/np.mean(np.diff(beats)):.1f} /dk')
 st.caption('Bu değer bilinen sentetik atım zamanlarından hesaplanır; otomatik R-tepe analizi sonucu değildir.')
 rr=go.Figure(go.Scatter(x=beats[1:],y=np.diff(beats),mode='lines+markers',line=dict(color='#48A3B6')))
 rr.update_layout(height=240,margin=dict(l=15,r=10,t=15,b=30),xaxis_title='Saniye',yaxis_title='RR (s)')
 st.plotly_chart(rr,use_container_width=True,config={'displaylogo':False})
answers=st.session_state.get('answers',{})
st.progress(len(set(answers)&set(available))/len(available),text=f'{len(set(answers)&set(available))}/{len(available)} alıştırma yanıtlandı')
if answers:
 st.download_button('Yanıtlarımı indir',json.dumps(answers,ensure_ascii=False,indent=2),'yanitlarim.json','application/json')
st.caption('Yanıtlar yalnızca bu oturumda tutulur. Yenileme veya çıkışta kaybolabilir. Fotoğraf yükleme henüz açık değildir.')

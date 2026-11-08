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
st.info('EKG eğitimi · Klinik tanı veya tedavi için kullanılmaz.')

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
mode=st.radio('Çalışma alanı',['Sentetik alıştırmalar','EKG fotoğrafı inceleme'],horizontal=True,key='workspace_mode')
if mode=='EKG fotoğrafı inceleme':
 if st.secrets.get('photo_ai',{}).get('enabled') is True:
  from student_photo_ai import render
  render(st)
  st.stop()
 from pathlib import Path
 import streamlit.components.v1 as components
 components.html(Path(__file__).with_name('student_photo.html').read_text(encoding='utf-8'),height=1250,scrolling=True)
 st.stop()
st.caption('Bu bölümdeki beş alıştırma sentetiktir; hasta verisi içermez.')
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
fig.update_xaxes(dtick=1,tickangle=0,minor=dict(dtick=.2,showgrid=True,gridcolor='#f7eeee'),gridcolor='#efd5d5',range=[start,start+6])
fig.update_yaxes(gridcolor='#efd5d5',range=[-.7,1.5])
st.plotly_chart(fig,use_container_width=True,config={'displaylogo':False,'scrollZoom':False})
st.caption('6 saniyelik görünüm · Grafik araçlarıyla yakınlaştırabilirsiniz. Ekran boyutu kâğıt kalibrasyonu değildir.')
with st.form('answer_'+case_id):
 answer=st.radio('16 saniyelik alıştırmanın tamamında hangi özellik öne çıkıyor?',OPTIONS,index=None,key='choice_'+case_id)
 uncertain=st.checkbox('Güvenilir ölçüm yapamıyorum',key='uncertain_'+case_id) if case_id=='noise' else False
 estimate=st.number_input('16 saniyelik kaydın ortalama hızı için tahmininiz (/dk)',min_value=0,max_value=300,value=0,key='rate_'+case_id)
 submitted=st.form_submit_button('Yanıtımı kontrol et',use_container_width=True)
if submitted:
 if answer is None:st.warning('Önce bir seçenek işaretleyin.')
 else:
  answers=dict(st.session_state.get('answers',{}));answers[case_id]={'answer':answer,'rate':None if uncertain else estimate,'rate_uncertain':uncertain};st.session_state.answers=answers
saved=st.session_state.get('answers',{}).get(case_id)
if saved:
 if saved['answer']==case['answer']:st.success('Bu alıştırmanın hedeflediği özelliği seçtiniz.')
 else:st.info('Birlikte karşılaştıralım: '+case['answer'])
 reference_rate=float(60/np.mean(np.diff(beats)))
 st.write('**Hız tahmini geri bildirimi**')
 if saved.get('rate_uncertain'):
  st.info('Güvenilir ölçüm yapamadığınızı belirttiniz. Gürültülü bölümü temiz bölümlerle karşılaştırın; gerekirse daha kaliteli bir kayıt isteyin. Sayısal tahmininiz değerlendirilmedi.')
 elif not saved.get('rate'):
  st.warning('Hız tahmini yanıtlanmadı. Özellik seçimi ile hız tahmini ayrı değerlendirilir.')
 else:
  difference=float(saved['rate'])-reference_rate
  st.write(f"Tahmininiz: {saved['rate']} /dk · Referans: {reference_rate:.1f} /dk · Fark: {difference:+.1f} /dk.")
  st.caption('Referans hız = 60 / ortalama RR. Şeridi kaydırarak kaydın tamamını inceleyin.')
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
st.caption('Yanıtlar yalnızca bu oturumda tutulur. Yenileme veya çıkışta kaybolabilir.')

"""Offline synthetic teaching cases. Not patient ECGs or clinical diagnoses."""
import numpy as np

CASES = {
 'regular60': {'title':'01 · Hız hesabı', 'beats':list(np.arange(1,15,1.0)), 'answer':'Düzenli', 'note':'Üretilen atımlar arasında 1 saniye var: 60/1 = 60 atım/dk.'},
 'regular90': {'title':'02 · Hız karşılaştırması', 'beats':list(np.arange(1,15,2/3)), 'answer':'Düzenli', 'note':'Üretilen RR yaklaşık 0,667 saniye: yaklaşık 90 atım/dk. Bu bir tanı değildir.'},
 'variable': {'title':'03 · RR karşılaştırması', 'beats':[1,1.8,2.9,3.6,4.6,5.45,6.65,7.35,8.4,9.2,10.35,11.1,12.1,12.85,14], 'answer':'Değişken', 'note':'Üretilen atım aralıkları değişiyor. Yalnızca RR değişkenliğiyle ritim tanısı konulmaz.'},
 'early': {'title':'04 · Erken gelen atım', 'beats':[1,2,3,4,4.55,6,7,8,9,10,11,12,13,14], 'answer':'Erken atım ve ardından uzun aralık', 'note':'4,55 saniyedeki sentetik atım erken, onu izleyen aralık daha uzundur. Köken tanısı bu şemadan çıkarılmaz.'},
 'noise': {'title':'05 · Sinyal kalitesi', 'beats':list(np.arange(1,15,1.0)), 'answer':'Sinyal kalitesi değerlendirmeyi zorlaştırıyor', 'note':'5–8 saniye arasına yapay gürültü eklendi. İşaretler üretimdeki konumlardır; gürültüde otomatik tespit başarısını göstermez.'},
}
OPTIONS = ['Düzenli','Değişken','Erken atım ve ardından uzun aralık','Sinyal kalitesi değerlendirmeyi zorlaştırıyor']

def waveform(case_id):
 case=CASES[case_id];fs=250;t=np.arange(0,16,1/fs);y=np.zeros_like(t)
 for b in case['beats']:
  for offset,amp,width in [(-.18,.12,.035),(-.025,-.12,.009),(0,1,.012),(.035,-.25,.012),(.28,.28,.065)]:
   y += amp*np.exp(-.5*((t-b-offset)/width)**2)
 if case_id=='noise':
  mask=(t>=5)&(t<=8);y[mask]+=np.random.default_rng(42).normal(0,.24,mask.sum())
 return t,y,np.asarray(case['beats']),fs

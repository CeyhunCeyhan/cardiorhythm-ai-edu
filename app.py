"""CardioRhythm AI: gated, educational ECG waveform viewer."""
import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import wfdb
from scipy.signal import butter, find_peaks, sosfiltfilt
from security import verify_password
from validation import reference_beats, evaluate_r_peaks
st.set_page_config(page_title='CardioRhythm AI | Eğitim', page_icon='🫀', layout='wide')
st.title('CardioRhythm AI')
st.caption('EKG ve aritmi eğitimi · Deneysel prototip v0.2')
st.warning('Yalnızca eğitim ve araştırma amaçlıdır. Klinik tanı, hasta takibi veya tedavi kararında kullanılmaz. Hasta verisi yüklemeyin.')

# This app is intended for an educational demo, not a production identity service.
# Store credential hashes in Streamlit's encrypted Secrets management, never in Git.
try:
    users = st.secrets["users"]
except (KeyError, FileNotFoundError):
    users = None

if users is None:
    import hmac
    from security import make_hash

    try:
        setup_key = st.secrets["bootstrap"]["token"]
    except (KeyError, FileNotFoundError):
        setup_key = ""

    if not setup_key or len(setup_key) < 32:
        st.error("Yönetici kurulumu için Secrets ayarları eksik.")
        st.stop()

    st.subheader("İlk yönetici hesabı kurulumu")
    with st.form("admin_setup"):
        entered_key = st.text_input("Kurulum anahtarı", type="password")
        new_password = st.text_input("Yeni şifre", type="password")
        repeat_password = st.text_input("Şifre tekrarı", type="password")
        create = st.form_submit_button("Şifre özeti oluştur")

    if create:
        if not hmac.compare_digest(entered_key, setup_key):
            st.error("Kurulum anahtarı hatalı.")
        elif len(new_password) < 12 or new_password != repeat_password:
            st.error("Şifreler aynı olmalı ve en az 12 karakter içermeli.")
        else:
            st.session_state.admin_hash = make_hash(new_password)

    if "admin_hash" in st.session_state:
        st.success("Şifre özeti hazır.")
        st.code(
            '[users.ceyhun]\nrole = "admin"\npassword_hash = "'
            + st.session_state.admin_hash + '"',
            language="toml"
        )
        st.info("Bu metni yalnızca Streamlit Secrets içine kaydedin.")
    st.stop()

if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None
if 'failed_attempts' not in st.session_state:
    st.session_state.failed_attempts = 0
if 'locked_until' not in st.session_state:
    st.session_state.locked_until = 0.0

if st.session_state.authenticated_user is None:
    st.subheader('Güvenli giriş')
    with st.form('login'):
        username = st.text_input('Kullanıcı adı', max_chars=80).strip().lower()
        password = st.text_input('Şifre', type='password')
        submitted = st.form_submit_button('Giriş yap', type='primary')
    if submitted:
        if time.monotonic() < st.session_state.locked_until:
            st.error('Çok fazla başarısız giriş. Lütfen birkaç dakika sonra tekrar deneyin.')
        else:
            record = users.get(username)
            # Perform a real hash check only for configured users.
            valid = bool(record and verify_password(password, record.get('password_hash', '')))
            if valid and record.get('role') in ('admin', 'resident', 'student'):
                st.session_state.authenticated_user = {'username': username, 'role': record['role']}
                st.session_state.failed_attempts = 0
                st.rerun()
            else:
                st.session_state.failed_attempts += 1
                if st.session_state.failed_attempts >= 5:
                    st.session_state.locked_until = time.monotonic() + 300
                    st.session_state.failed_attempts = 0
                st.error('Kullanıcı adı veya şifre hatalı.')
    st.stop()

identity = st.session_state.authenticated_user
role_label = {'admin': 'Eğitici / Yönetici', 'resident': 'Asistan', 'student': 'Öğrenci'}[identity['role']]
with st.sidebar:
    st.success(f"{identity['username']} · {role_label}")
    if st.button('Çıkış yap'):
        st.session_state.authenticated_user = None
        st.rerun()

st.subheader('EKG analiz laboratuvarı')
st.info('Örnek veri: PhysioNet MIT-BIH Arrhythmia Database, kayıt 100. Ağ bağlantısı gerektirir.')

@st.cache_data(ttl=3600, show_spinner='Örnek EKG kaydı yükleniyor…')
def load_sample():
    rec = wfdb.rdrecord('100', pn_dir='mitdb', sampto=36000)
    return float(rec.fs), rec.sig_name, rec.p_signal

try:
    fs, channels, matrix = load_sample()
    lead = st.selectbox('Kanal', channels)
    signal = matrix[:, channels.index(lead)]
    duration = len(signal) / fs
    window = st.slider('Görüntüleme süresi (s)', 3, 20, 10)
    start = st.slider('Başlangıç (s)', 0, max(0, int(duration) - window), 0)
    a, b = int(start * fs), int((start + window) * fs)
    segment = signal[a:b]
    sos = butter(3, [5, 18], btype='bandpass', fs=fs, output='sos')
    filtered = sosfiltfilt(sos, segment)
    peaks, _ = find_peaks(np.abs(filtered), distance=max(1, int(0.25 * fs)), prominence=max(np.std(filtered) * 1.1, 1e-8))
    rr = np.diff(peaks) / fs
    hr = 60 / np.mean(rr) if len(rr) else float('nan')
    cv = np.std(rr, ddof=1) / np.mean(rr) if len(rr) > 1 else float('nan')
    c1, c2, c3 = st.columns(3)
    c1.metric('Tahmini kalp hızı', f'{hr:.1f} /dk' if np.isfinite(hr) else '—')
    c2.metric('Aday tepe sayısı', len(peaks))
    c3.metric('RR değişkenlik katsayısı', f'{cv:.2f}' if np.isfinite(cv) else '—')
    t = np.arange(a, b) / fs
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=segment, name='EKG', mode='lines'))
    fig.add_trace(go.Scatter(x=t[peaks], y=segment[peaks], name='Aday R tepeleri', mode='markers'))
    fig.update_layout(height=450, xaxis_title='Zaman (s)', yaxis_title='Genlik (mV)')
    st.plotly_chart(fig, use_container_width=True)
    st.caption('RR düzensizliği tek başına AF tanısı değildir.')
    st.subheader('MIT-BIH referans validasyonu')
    try:
        annotation = wfdb.rdann('100', 'atr', pn_dir='mitdb')
        reference = reference_beats(annotation, a, b)
        result = evaluate_r_peaks(peaks + a, reference, fs, tolerance_ms=150)
        v1, v2, v3 = st.columns(3)
        v1.metric('Sensitivite', f"{result['sensitivity']:.1%}")
        v2.metric('PPV', f"{result['ppv']:.1%}")
        v3.metric('Ortalama mutlak zamanlama hatası', f"{result['mean_absolute_error_ms']:.1f} ms")
        st.write(f"TP: {result['TP']} | FP: {result['FP']} | FN: {result['FN']}")
        st.caption('MIT-BIH kayıt 100, seçilen pencere; ±150 ms tolerans. Bu sonuç tüm veri tabanının validasyonu değildir.')
    except Exception as exc:
        st.warning(f'Referans validasyonu tamamlanamadı: {type(exc).__name__}
    st.download_button('RR aralıklarını CSV indir', pd.DataFrame({'RR_s': rr}).to_csv(index=False), 'rr_intervals.csv', 'text/csv')
    if identity['role'] == 'admin':
        st.info('Yönetici modu: kullanıcılar şimdilik Streamlit Secrets üzerinden yönetilir. Yönetim paneli sonraki sürümde.')
except Exception:
    st.error('Örnek EKG verisi yüklenemedi veya işlenemedi. İnternet bağlantısını ve uygulama günlüklerini kontrol edin.')

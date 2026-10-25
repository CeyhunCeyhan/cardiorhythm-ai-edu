import numpy as np
import plotly.graph_objects as go
import streamlit as st
import wfdb

st.set_page_config(page_title="CardioRhythm AI - FP incelemesi")
st.title("İki yalancı pozitifin EKG incelemesi")
st.caption("MIT-BIH kayıt 100 · MLII · 1518–1522 saniye")

@st.cache_data(show_spinner=False)
def load_data():
    fs = 360
    start, end = 1517, 1523
    record = wfdb.rdrecord(
        "100", pn_dir="mitdb",
        sampfrom=int(start * fs), sampto=int(end * fs),
        channels=[0]
    )
    annotation = wfdb.rdann(
        "100", "atr", pn_dir="mitdb",
        sampfrom=int(start * fs), sampto=int(end * fs),
        shift_samps=False
    )
    return record.p_signal[:, 0], annotation.sample, annotation.symbol, fs, start

with st.spinner("EKG ve referans anotasyonları yükleniyor..."):
    signal, samples, symbols, fs, start = load_data()

times = start + np.arange(len(signal)) / fs
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=times, y=signal, mode="lines",
    name="MLII EKG", line=dict(color="#17324D", width=1.5)
))

beat_symbols = {"N", "L", "R", "B", "A", "a", "J", "S",
                "V", "r", "F", "e", "j", "n", "E", "/", "f", "Q", "?"}
for sample, symbol in zip(samples, symbols):
    t = sample / fs
    if symbol in beat_symbols and 1518 <= t <= 1522:
        fig.add_vline(x=t, line_color="green", line_dash="dash")

for t in [1519.139, 1520.022]:
    fig.add_vline(x=t, line_color="red", line_dash="dot")

fig.add_vline(x=1520, line_color="orange", line_width=3)
fig.update_layout(
    xaxis_title="Kayıt zamanı (s)",
    yaxis_title="Amplitüd (mV)",
    height=450,
    xaxis=dict(range=[1518, 1522]),
    legend=dict(orientation="h")
)
st.plotly_chart(fig, use_container_width=True)
st.caption("Yeşil: referans atımlar · Kırmızı: FP tespitleri · Turuncu: 1520 s pencere sınırı")
st.write("FP zamanları (s): 1519.139 ve 1520.022")
st.warning("Araştırma amaçlı görselleştirmedir; klinik değerlendirme değildir.")

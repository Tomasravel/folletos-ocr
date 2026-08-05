import json
import os
import requests
import pandas as pd
import streamlit as st

API = os.environ.get("API_URL", "http://localhost:8000")
TOKEN = os.environ.get("API_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

st.set_page_config(page_title="Folletos OCR", layout="wide")
st.title("OCR de reparto de folletos")

caps = requests.get(f"{API}/capabilities", headers=HEADERS).json()
levels = caps.get("levels", ["rapida"])
col1, col2 = st.columns([3, 1])
level = col2.selectbox("Nivel", levels)
debug = col2.toggle("Debug", value=False)
files = col1.file_uploader("Imágenes", type=["jpg", "jpeg", "png", "webp"],
                           accept_multiple_files=True)

if st.button("Procesar", disabled=not files):
    rows = []
    prog = st.container()
    for f in files:
        placeholder = prog.empty()
        placeholder.info(f"Procesando {f.name}…")
        with requests.post(
            f"{API}/process", params={"level": level, "stream": "true", "debug": debug},
            files={"images": (f.name, f.getvalue(), f.type)}, headers=HEADERS, stream=True
        ) as r:
            last = None
            for line in r.iter_lines():
                if line and line.startswith(b"data: "):
                    payload = line[6:].decode()
                    if payload.strip() in ("", "{}"):
                        continue
                    ev = json.loads(payload)
                    fields = ev.get("fields", {})
                    placeholder.write(
                        f"**{f.name}** · {ev.get('stage')} · {ev.get('engine')}/"
                        f"{ev.get('parser')} → {fields}")
                    last = fields
            if last:
                last["_img"] = f.name
                rows.append(last)
    if rows:
        st.subheader("Resultados (editables)")
        edited = st.data_editor(pd.DataFrame(rows), num_rows="dynamic")
        c1, c2 = st.columns(2)
        c1.download_button("Descargar CSV", edited.to_csv(index=False), "folletos.csv")

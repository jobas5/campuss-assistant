"""Trigger #1 — the student form.   streamlit run submit_app.py"""
import tempfile

import streamlit as st

from extract import extract_request, extract_text_request
from workflow import process

st.title("Layanan Mahasiswa · Ajukan Permohonan")
st.caption("Contoh praktikum. Permohonan diproses AI lalu diperiksa staf BAAK sebelum dikirim.")

photo = st.file_uploader("Foto KTM / formulir (opsional)", type=["jpg", "jpeg", "png"])
text = st.text_area("Atau tulis permohonan Anda (sertakan nama dan NIM)")

if st.button("Kirim permohonan", disabled=not (photo or text.strip())):
    with st.spinner("Membaca dan memproses permohonan…"):
        if photo:
            with tempfile.NamedTemporaryFile(suffix="." + photo.name.rsplit(".", 1)[-1]) as f:
                f.write(photo.getvalue())
                f.flush()
                data = extract_request(f.name)
        else:
            data = extract_text_request(text)
        out = process(data)
    if out["status"] == "NEEDS_FIX":
        st.error(out["message"])
    else:
        st.success(f"Permohonan #{out['id']} diterima dan menunggu persetujuan staf.")

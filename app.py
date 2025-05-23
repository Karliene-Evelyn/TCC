import streamlit as st
import requests
import os
from datetime import datetime
import tempfile

# Configuração da página
st.set_page_config(page_title="DataWeath - GFS Downloader", layout="wide")
st.title("🌎 DataWeath - GFS Downloader e Viewer")
st.write("Facilite sua vida acadêmica baixando e visualizando dados do GFS!")

# ===== ENTRADAS DO USUÁRIO =====
st.sidebar.header("📅 Parâmetros do GFS")
data = st.sidebar.date_input("Data da previsão", datetime(2024, 1, 1), help="Data da análise do modelo GFS")
hora = st.sidebar.selectbox("Hora da análise (UTC)", ["00", "06", "12", "18"], help="Hora de início da análise do GFS")
previsao = st.sidebar.selectbox("Horas à frente (previsão)", ["f000", "f006", "f012", "f024", "f048", "f072", "f096", "f120", "f168", "f240"], help="Tempo de previsão a ser baixado")
resolucao = st.sidebar.radio("Resolução", ["0p25"], help="Resolução espacial do modelo (Apenas 0.25°)")

# ===== LINK DE DOWNLOAD =====
ano = data.strftime("%Y")
mes = data.strftime("%m")
dia = data.strftime("%d")
base_url = "https://data-osdf.rda.ucar.edu/ncar/rda/d084001"
arquivo = f"gfs.{resolucao}.{ano}{mes}{dia}{hora}.{previsao}.grib2"
url_completa = f"{base_url}/{ano}/{ano}{mes}{dia}/{arquivo}"

st.subheader("🔗 Link gerado")
st.code(url_completa, language='bash')

# ===== LINK WGET =====
st.subheader("📥 Use o comando wget para baixar:")
st.code(f"wget {url_completa}", language='bash')

# ===== FUNÇÃO DE DOWNLOAD =====
def download_file(url):
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            total = int(r.headers.get('content-length', 0))
            progress_bar = st.progress(0)
            downloaded = 0
            filename = os.path.basename(url)
            temp_path = os.path.join(tempfile.gettempdir(), filename)
            with open(temp_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress_bar.progress(min(downloaded / total, 1.0))
            return temp_path
    except Exception as e:
        st.error(f"Erro ao baixar o arquivo: {e}")
        return None

# ===== BOTÃO DE DOWNLOAD =====
if st.button("⬇️ Baixar o Arquivo GFS"):
    st.info("Baixando arquivo...")
    path_file = download_file(url_completa)
    if path_file:
        st.success(f"Arquivo baixado com sucesso: {path_file}")
    else:
        st.warning("Não foi possível baixar o arquivo.")

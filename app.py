import streamlit as st
import requests
import os
from datetime import datetime
import tempfile
import xarray as xr
import matplotlib.pyplot as plt
import plotly.express as px

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
        st.session_state["path_file"] = path_file  # Salva na sessão
    else:
        st.warning("Não foi possível baixar o arquivo.")

# ===== LISTAR VARIÁVEIS =====
@st.cache_data(show_spinner="🔍 Lendo variáveis disponíveis...")
def listar_variaveis(path_file):
    try:
        ds = xr.open_dataset(path_file, engine="cfgrib", filter_by_keys={"typeOfLevel": "isobaricInhPa"})
        variaveis = [v for v in ds.data_vars if ds[v].ndim > 0]
        return variaveis
    except:
        return []

# ===== LISTAR NÍVEIS DE PRESSÃO =====
@st.cache_data(show_spinner="🔍 Lendo níveis disponíveis...")
def listar_niveis(path_file):
    ds = xr.open_dataset(path_file, engine="cfgrib", filter_by_keys={"typeOfLevel": "isobaricInhPa"})
    niveis = list(ds["isobaricInhPa"].values)
    return niveis

# ===== CARREGAR DADOS SELECIONADOS =====
@st.cache_data(show_spinner="🧠 Carregando dados para visualização...")
def carregar_dataset(path_file, variavel, nivel):
    ds = xr.open_dataset(path_file, engine="cfgrib", filter_by_keys={"typeOfLevel": "isobaricInhPa"})
    dados = ds[variavel].sel(isobaricInhPa=nivel, method="nearest")
    return dados

if "path_file" in st.session_state:
    st.subheader("📊 Visualização de Variáveis no Nível Isobárico (hPa)")
    variaveis = listar_variaveis(st.session_state["path_file"])

    if variaveis:
        variavel = st.selectbox("Escolha uma variável:", variaveis)

        descricao_variaveis = {
            "gh": "Altura geopotencial (metros) — altura na qual a pressão é medida.",
            "t": "Temperatura do ar (Kelvin) — medida da energia térmica.",
            "r": "Razão de mistura — quantidade de vapor d’água na atmosfera (kg/kg).",
            "q": "Umidade específica — massa de vapor d’água por massa de ar úmido (kg/kg).",
            "u": "Componente zonal do vento (m/s) — vento de oeste para leste.",
            "v": "Componente meridional do vento (m/s) — vento de sul para norte.",
            "w": "Velocidade vertical do vento (Pa/s) — movimento do ar para cima ou para baixo.",
            "wz": "Vorticidade relativa — medida da rotação do ar.",
            "absv": "Velocidade absoluta do vento (m/s) — intensidade total do vento.",
            "o3mr": "Mistura de ozônio — concentração de ozônio na atmosfera (kg/kg)."
        }


        if variavel in descricao_variaveis:
            st.markdown(f"**Descrição:** {descricao_variaveis[variavel]}")
        else:
            st.markdown("Descrição da variável não disponível.")

        niveis = listar_niveis(st.session_state["path_file"])
        nivel_escolhido = st.selectbox("Escolha o nível de pressão (hPa):", niveis)

        if variavel and nivel_escolhido:
            st.markdown(f"### Variável: `{variavel}` no nível {nivel_escolhido} hPa")
            dados = carregar_dataset(st.session_state["path_file"], variavel, nivel_escolhido)
            st.write("Dimensões dos dados:", dados.dims)

            if dados.ndim < 2:
                st.warning("Variável com dimensões insuficientes para plotar um mapa. Exibindo valor:")
                st.write(dados.values)
            else:
                # pegando os valores das coords
                lat = dados.coords['latitude'].values   # array com 721 elementos
                lon = dados.coords['longitude'].values  # array com 1440 elementos

                # matriz 2D com shape (latitude, longitude)
                z = dados.values  

                # Atenção: verifique se latitude está em ordem crescente (de Sul para Norte)
                # Se estiver decrescente (Norte para Sul), inverta para plotar certo:
                if lat[0] > lat[-1]:
                    lat = lat[::-1]
                    z = z[::-1, :]

                fig = px.imshow(
                    z,
                    x=lon,
                    y=lat,
                    origin='lower',  # garante que o eixo y é latitude crescente para cima
                    labels={'x':'Longitude', 'y':'Latitude', 'color': dados.name},
                    aspect='auto',
                    color_continuous_scale='Viridis'
                )

                fig.update_layout(
                    title=f'Mapa interativo da variável {dados.name}',
                    coloraxis_colorbar=dict(title=dados.attrs.get('units', ''))
                )

                st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("Nenhuma variável disponível no nível isobárico.")

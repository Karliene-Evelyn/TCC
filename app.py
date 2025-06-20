import streamlit as st
import requests
import os
from datetime import datetime
import tempfile
import xarray as xr
import plotly.express as px
from descricoes import descricao_isobaric, descricao_surface


# Configuração da página
st.set_page_config(page_title="DataWeath - GFS Downloader", layout="wide")
st.title("🌎 DataWeath - GFS Downloader e Viewer")
st.write("Escolha os parâmetros para gerar o link e baixar o arquivo GRIB2.")

# ===== ENTRADAS DO USUÁRIO =====
st.sidebar.header("📅 Parâmetros do GFS")
data = st.sidebar.date_input("Data da previsão", datetime(2024, 1, 1), help="Data da análise do modelo GFS")
hora = st.sidebar.selectbox("Hora da análise (UTC)", ["00", "06", "12", "18"], help="Hora de início da análise do GFS")
previsao = st.sidebar.selectbox("Horas à frente (previsão)", ["f000", "f006", "f012", "f024", "f048", "f072", "f096", "f120", "f168", "f240"], help="Tempo de previsão a ser baixado")
resolucao = st.sidebar.radio("Resolução", ["0p25"], help="Resolução espacial do modelo (Apenas 0.25°)")

# ===== LINK DE DOWNLOAD =====
ano, mes, dia = data.strftime("%Y"), data.strftime("%m"), data.strftime("%d")
data_str = f"{ano}{mes}{dia}"
base_url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod"
pasta = f"gfs.{data_str}/{hora}/atmos"
arquivo = f"gfs.t{hora}z.pgrb2.{resolucao}.{previsao}"
url_completa = f"{base_url}/{pasta}/{arquivo}"

st.subheader("🔗 Link gerado")
st.code(url_completa, language='bash')

# ===== VERIFICAR SE O LINK ESTÁ FUNCIONANDO =====
def verificar_link(url):
    try:
        response = requests.get(url, stream=True, timeout=10)
        return response.status_code == 200
    except Exception as e:
        st.error(f"❌ Erro ao verificar o link: {e}")
        return False

# ===== FUNÇÃO DE DOWNLOAD COM PORCENTAGEM =====
def download_file(url):
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            total = int(r.headers.get('content-length', 0))
            progress_bar = st.progress(0)
            percent_text = st.empty()

            downloaded = 0
            filename = os.path.basename(url)
            temp_path = os.path.join(tempfile.gettempdir(), filename)
            with open(temp_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        percent = int((downloaded / total) * 100) if total > 0 else 0
                        progress_bar.progress(min(downloaded / total, 1.0))
                        percent_text.text(f"📥 Download: {percent}%")

            percent_text.text("✅ Download concluído!")
            return temp_path
    except Exception as e:
        st.error(f"Erro ao baixar o arquivo: {e}")
        return None

# TESTE MANUAL DE ACESSO AO LINK GERADO
try:
    debug_response = requests.get(url_completa, stream=True, timeout=10)
    st.info(f"Código de status da URL: {debug_response.status_code}")

    content_length = debug_response.headers.get('content-length', None)
    if content_length:
        tamanho_mb = int(content_length) / (1024 * 1024)
        st.info(f"Tamanho do arquivo: {tamanho_mb:.2f} MB")
    else:
        st.info("Tamanho do arquivo: Não informado")
except Exception as e:
    st.warning(f"⚠️ Erro ao tentar acessar o link diretamente: {e}")


# ===== BOTÃO DE DOWNLOAD =====
if st.button("⬇️ Baixar o Arquivo GFS"):
    status_placeholder = st.empty()
    status_placeholder.info("Verificando o link...")

    if verificar_link(url_completa):
        status_placeholder.empty()
        path_file = download_file(url_completa)

        if path_file:
            status_placeholder.success(f"✅ Arquivo baixado com sucesso: {path_file}")
            st.session_state["path_file"] = path_file
        else:
            status_placeholder.error("❌ Não foi possível baixar o arquivo.")
    else:
        status_placeholder.error("🚫 Link inválido ou indisponível.")

# ===== FUNÇÕES DE LEITURA DE VARIÁVEIS E NÍVEIS =====
@st.cache_data(show_spinner="🔍 Lendo variáveis disponíveis...")
def listar_variaveis_e_niveis(path_file):
    variaveis = {}
    niveis = {}

    # Isobaric
    try:
        ds_iso = xr.open_dataset(path_file, engine="cfgrib", filter_by_keys={"typeOfLevel": "isobaricInhPa"})
        variaveis["isobaricInhPa"] = [v for v in ds_iso.data_vars if ds_iso[v].ndim > 0]
        niveis["isobaricInhPa"] = list(ds_iso["isobaricInhPa"].values)
    except:
        variaveis["isobaricInhPa"] = []
        niveis["isobaricInhPa"] = []

    # Surface
    try:
        surface_vars = []
        step_types = ["instant", "avg", "accum"]
        for step in step_types:
            try:
                ds_surface = xr.open_dataset(path_file, engine="cfgrib", filter_by_keys={"typeOfLevel": "surface", "stepType": step})
                surface_vars.extend([v for v in ds_surface.data_vars if ds_surface[v].ndim > 0])
            except:
                continue
        variaveis["surface"] = list(set(surface_vars))
        niveis["surface"] = ["surface"]
    except:
        variaveis["surface"] = []
        niveis["surface"] = []

    # MeanSea
    try:
        ds_meansea = xr.open_dataset(path_file, engine="cfgrib", filter_by_keys={"typeOfLevel": "meanSea"})
        variaveis["meanSea"] = [v for v in ds_meansea.data_vars if ds_meansea[v].ndim > 0]
        niveis["meanSea"] = ["meanSea"]
    except:
        variaveis["meanSea"] = []
        niveis["meanSea"] = []

    return variaveis, niveis


@st.cache_data(show_spinner="🧠 Carregando dados para visualização...")
def carregar_dataset(path_file, variavel, tipo_nivel, nivel=None):
    if tipo_nivel == "isobaricInhPa":
        filtro = {"typeOfLevel": tipo_nivel}
        ds = xr.open_dataset(path_file, engine="cfgrib", filter_by_keys=filtro)
        return ds[variavel].sel(isobaricInhPa=nivel, method="nearest")

    elif tipo_nivel == "meanSea":
        try:
            ds = xr.open_dataset(path_file, engine="cfgrib", filter_by_keys={"typeOfLevel": "meanSea"})
            if variavel in ds.data_vars:
                return ds[variavel]
        except:
            pass
        raise ValueError(f"❌ Variável {variavel} não encontrada no nível meanSea.")

    else:  # Surface
        step_types = ["instant", "avg", "accum"]
        for step in step_types:
            try:
                ds = xr.open_dataset(path_file, engine="cfgrib", filter_by_keys={"typeOfLevel": "surface", "stepType": step})
                if variavel in ds.data_vars:
                    return ds[variavel]
            except:
                continue
        raise ValueError(f"❌ Variável {variavel} não encontrada em nenhum stepType do nível surface.")


# ===== VISUALIZAÇÃO ====
from descricoes import descricao_isobaric, descricao_surface, descricao_meanSea

if "path_file" in st.session_state:
    st.subheader("📊 Visualização de Variáveis")

    variaveis_dict, niveis_dict = listar_variaveis_e_niveis(st.session_state["path_file"])

    tipo_nivel_opcoes = {
        "isobaricInhPa": "Camadas de Pressão (hPa)",
        "surface": "Superfície",
        "meanSea": "Nível Médio do Mar (MSLP)"
    }

    tipo_nivel_legivel = st.selectbox(
        "Escolha o tipo de nível:",
        ["Selecione..."] + list(tipo_nivel_opcoes.values())
    )

    # Mapeamento reverso
    tipo_nivel_escolhido = None
    for key, label in tipo_nivel_opcoes.items():
        if tipo_nivel_legivel == label:
            tipo_nivel_escolhido = key

    if tipo_nivel_escolhido:
        variaveis = variaveis_dict.get(tipo_nivel_escolhido, [])

        if variaveis:
            var_escolhida = st.selectbox("Escolha a variável:", ["Selecione..."] + variaveis)

            if var_escolhida != "Selecione...":
    
                if tipo_nivel_escolhido == "isobaricInhPa":
                    descricao_ativa = descricao_isobaric
                elif tipo_nivel_escolhido == "surface":
                    descricao_ativa = descricao_surface
                elif tipo_nivel_escolhido == "meanSea":
                    descricao_ativa = descricao_meanSea
                else:
                    descricao_ativa = {}

                
                if var_escolhida in descricao_ativa:
                    st.markdown(f"**Descrição:** {descricao_ativa[var_escolhida]}")
                else:
                    st.markdown("🧩 *Descrição não disponível para essa variável.*")

                dados = None

                if tipo_nivel_escolhido == "isobaricInhPa":
                    nivel_escolhido = st.selectbox(
                        "Escolha o nível de pressão (hPa):",
                        ["Selecione..."] + [str(n) for n in niveis_dict[tipo_nivel_escolhido]]
                    )
                    if nivel_escolhido != "Selecione...":
                        dados = carregar_dataset(
                            st.session_state["path_file"],
                            var_escolhida,
                            tipo_nivel_escolhido,
                            float(nivel_escolhido)
                        )
                        st.markdown(f"### Variável `{var_escolhida}` no nível {nivel_escolhido} hPa")

                else:
                    dados = carregar_dataset(
                        st.session_state["path_file"],
                        var_escolhida,
                        tipo_nivel_escolhido
                    )
                    nivel_str = " (nível de superfície)" if tipo_nivel_escolhido == "surface" else " (nível médio do mar)"
                    st.markdown(f"### Variável `{var_escolhida}`{nivel_str}")

                # Plota
                if dados is not None:
                    if dados.ndim < 2:
                        st.warning("⚠️ Variável com dimensões insuficientes para visualização em mapa.")
                    else:
                        lat = dados.coords['latitude'].values
                        lon = dados.coords['longitude'].values
                        z = dados.values

                        if lat[0] > lat[-1]:
                            lat = lat[::-1]
                            z = z[::-1, :]

                        fig = px.imshow(
                            z,
                            x=lon,
                            y=lat,
                            origin='lower',
                            labels={'x': 'Longitude', 'y': 'Latitude', 'color': dados.name},
                            aspect='auto',
                            color_continuous_scale='Viridis'
                        )

                        fig.update_layout(
                            title=f'Mapa da variável {dados.name}',
                            coloraxis_colorbar=dict(title=dados.attrs.get('units', ''))
                        )

                        st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning("Nenhuma variável disponível para esse tipo de nível.")

# ===== DICIONÁRIO INTERATIVO DE VARIÁVEIS =====
with st.sidebar.expander("📚 Dicionário de Variáveis", expanded=True):
    nivel_opcoes = {
        "isobaricInhPa": "Camadas de Pressão (hPa)",
        "surface": "Superfície",
        "meanSea": "Nível Médio do Mar (MSLP)"
    }

    nivel_legivel = st.selectbox(
        "Escolha o tipo de nível:",
        ["Selecione..."] + list(nivel_opcoes.values()),
        key="dicionario_nivel"
    )

    # Mapeamento reverso
    nivel_escolhido = None
    for key, label in nivel_opcoes.items():
        if nivel_legivel == label:
            nivel_escolhido = key

    if nivel_escolhido:
        from descricoes import descricao_isobaric, descricao_surface, descricao_meanSea

        if nivel_escolhido == "isobaricInhPa":
            dicionario = descricao_isobaric
        elif nivel_escolhido == "surface":
            dicionario = descricao_surface
        elif nivel_escolhido == "meanSea":
            dicionario = descricao_meanSea
        else:
            dicionario = {}

        if dicionario:
            dicionario_ordenado = dict(sorted(dicionario.items(), key=lambda item: item[1].lower()))
            
            for var, desc in dicionario_ordenado.items():
                st.markdown(f"**`{var}`** → {desc}")
        else:
            st.markdown("⚠️ Nenhuma variável disponível para esse nível.")


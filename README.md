# Explicação do Código Fonte

## Objetivo Geral do Código

O sistema **"DataWeath - GFS Downloader e Viewer"** foi desenvolvido com a finalidade de facilitar o **download** e a **visualização de dados meteorológicos** do modelo GFS (Global Forecast System), especialmente em arquivos com extensão `.grib2`.  
Utiliza as seguintes bibliotecas principais:

- **Streamlit**: Para interface web;
- **xarray**: Para leitura dos dados meteorológicos;
- **Plotly**: Para visualizações interativas.

---

## 1. Importação de Bibliotecas

```python
import streamlit as st
import requests
import os
from datetime import datetime
import tempfile
import xarray as xr
import matplotlib.pyplot as plt
import plotly.express as px
```
Essas bibliotecas oferecem recursos para:

- Criação da interface interativa: Streamlit

- Requisições HTTP: requests

- Manipulação de arquivos: os, tempfile

- Leitura de dados meteorológicos: xarray

- Gráficos interativos: Plotly

### 2. Configuração da Página
```python
st.set_page_config(page_title="DataWeath - GFS Downloader", layout="wide")
st.title("🌎 DataWeath - GFS Downloader e Viewer")
st.write("Facilite sua vida acadêmica baixando e visualizando dados do GFS!")
Define o título da página e configura o layout responsivo e amigável.
```
### 3. Parâmetros do GFS (Entrada do Usuário)
```python
st.sidebar.header("📅 Parâmetros do GFS")
```
Na barra lateral, o usuário escolhe:

- Data da previsão
- Hora da análise (00, 06, 12, 18 UTC)
- Hora da previsão futura (f000 a f240)
- Resolução espacial: (apenas 0.25°)

### 4. Geração de Link para Download
```python
arquivo = f"gfs.{resolucao}.{ano}{mes}{dia}{hora}.{previsao}.grib2"
url_completa = f"{base_url}/{ano}/{ano}{mes}{dia}/{arquivo}"
```
O código monta o link dinâmico com base nas opções escolhidas pelo usuário.

### 5. Comando WGET
```python
st.code(f"wget {url_completa}", language='bash')
```
Mostra ao usuário o comando WGET para baixar o arquivo via terminal.

### 6. Função de Download com Barra de Progresso
```python
def download_file(url):
    ...
```
Função que:

- Realiza o download por streaming;
- Salva o arquivo em um diretório temporário;
- Mostra a barra de progresso em tempo real;
- Retorna o caminho do arquivo salvo.

### 7. Botão de Ação para Download
```python
if st.button("⬇️ Baixar o Arquivo GFS"):
    ...
```
Aciona o processo de download ao ser clicado.

### 8. Leitura de Variáveis e Níveis Isobáricos
```python
@st.cache_data(...)
def listar_variaveis(path_file): ...

def listar_niveis(path_file): ...
```
Essas funções:

- Abrem o arquivo GRIB com xarray;

- Filtram apenas os dados com nível de pressão atmosférica (isobaricInhPa).

###9. Carregamento de Dados Selecionados
```python
def carregar_dataset(path_file, variavel, nivel):
    ...
```
Abre e extrai dados da variável e do nível de pressão escolhidos.

### 10. Visualização Interativa dos Dados
```python
fig = px.imshow(...)
st.plotly_chart(fig, use_container_width=True)
```
- Usa plotly.express.imshow para exibir um mapa 2D interativo com escala de cores;

- Corrige a ordem da latitude se necessário;

- Permite exploração visual dos dados meteorológicos.

### 11. Dicionário de Variáveis
O sistema exibe uma descrição automática da variável selecionada, como:

- gh: Altura geopotencial
- t: Temperatura
- u / v: Componentes do vento
- q / r: Umidade
- o3mr: Mistura de ozônio

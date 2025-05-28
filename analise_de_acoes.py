import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from PIL import Image

# Configuração da página
st.set_page_config(page_title="Análise de Ações", layout="wide")

# === Logo e Título Lado a Lado ===
col1, col2 = st.columns([1, 5])
with col1:
    logo = Image.open("casemiro.png")  # certifique-se que está na mesma pasta do app
    st.image(logo, width=100)

with col2:
    st.markdown("## 📊 Análise de Ações")

# Lista de tickers de exemplo
tickers = ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'BBAS3.SA', 'WEGE3.SA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN']

# ==============================
# FUNÇÃO - BUSCA DE DADOS ATUAIS
# ==============================
@st.cache_data
def buscar_dados_tabela(tickers):
    hoje = datetime.today()
    um_ano_atras = hoje - timedelta(days=365)
    dados = []

    for ticker in tickers:
        try:
            acao = yf.Ticker(ticker)
            historico = acao.history(start=um_ano_atras, end=hoje)

            if historico.empty:
                continue

            preco_atual = historico['Close'][-1]
            preco_ontem = historico['Close'][-2]
            preco_ano_passado = historico['Close'][0]

            variacao_dia = ((preco_atual - preco_ontem) / preco_ontem) * 100
            variacao_12m = ((preco_atual - preco_ano_passado) / preco_ano_passado) * 100

            dados.append({
                'Ticker': ticker,
                'Preço Atual (R$)': round(preco_atual, 2),
                'Variação do Dia (%)': round(variacao_dia, 2),
                'Variação 12 Meses (%)': round(variacao_12m, 2),
            })
        except Exception as e:
            st.warning(f"Erro ao carregar dados de {ticker}: {e}")

    return pd.DataFrame(dados)

# ==============================
# FUNÇÃO - HISTÓRICO PARA GRÁFICO
# ==============================
@st.cache_data
def carregar_historico(tickers, start, end):
    df = pd.DataFrame()
    tickers_sem_dados = []

    for ticker in tickers:
        try:
            dados = yf.download(ticker, start=start, end=end)
            if dados.empty:
                tickers_sem_dados.append(ticker)
                continue

            dados = dados.reset_index()
            dados['Ticker'] = ticker
            df = pd.concat([df, dados[['Date', 'Close', 'Ticker']]])
        except Exception:
            tickers_sem_dados.append(ticker)

    return df, tickers_sem_dados

# ==============================
# TABELA GERAL
# ==============================
st.subheader("📋 Tabela Geral")
df_acoes = buscar_dados_tabela(tickers)
st.dataframe(df_acoes, use_container_width=True)

# ==============================
# FILTROS PARA GRÁFICO
# ==============================
st.subheader("📈 Gráfico de Histórico de Ações")

acoes_escolhidas = st.multiselect("Selecione uma ou mais ações:", options=tickers, default=['PETR4.SA'])
periodo = st.selectbox("Selecione o período:", options=[
    "1 mês", "3 meses", "6 meses", "1 ano", "3 anos", "5 anos", "10 anos"
])

# Conversão do período para data
dias = {
    "1 mês": 30,
    "3 meses": 90,
    "6 meses": 180,
    "1 ano": 365,
    "3 anos": 365 * 3,
    "5 anos": 365 * 5,
    "10 anos": 365 * 10,
}
hoje = datetime.today()
inicio = hoje - timedelta(days=dias[periodo])

# ==============================
# GRÁFICO
# ==============================
df_grafico, tickers_sem_dados = carregar_historico(acoes_escolhidas, inicio, hoje)

if tickers_sem_dados:
    st.warning(f"❌ Não foi possível obter dados para: {', '.join(tickers_sem_dados)}")

if df_grafico.empty:
    st.error("Nenhum dado disponível para os tickers selecionados no período escolhido.")
else:
    # Garantir colunas simples
    df_grafico.columns = [str(col) if not isinstance(col, tuple) else col[0] for col in df_grafico.columns]
    
    fig = px.line(df_grafico, x="Date", y="Close", color="Ticker", title="Histórico de Preços")
    fig.update_layout(xaxis_title="Data", yaxis_title="Preço (R$)")
    st.plotly_chart(fig, use_container_width=True)

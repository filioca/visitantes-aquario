import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import re
import unicodedata
from rapidfuzz import process, utils
from functools import lru_cache

# ==========================================
# CONFIGURAÇÃO E ESTILO
# ==========================================
st.set_page_config(page_title="Dashboard Aquário Pro+", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stDownloadButton {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🐠 Dashboard Gerencial - Aquário Municipal")
st.markdown("### Processamento Consolidado & Inteligência Geográfica")

# ==========================================
# LISTA DE REFERÊNCIA (MT + CAPITAIS)
# ==========================================
CIDADES_REFERENCIA = [
    "Cuiabá", "Várzea Grande", "Rondonópolis", "Sinop", "Sorriso", "Tangará da Serra", 
    "Cáceres", "Primavera do Leste", "Lucas do Rio Verde", "Barra do Garças", 
    "Alta Floresta", "Pontes e Lacerda", "Juína", "Guarantã do Norte", "Poconé", 
    "Nova Mutum", "Campo Novo do Parecis", "Barra do Bugres", "Colniza", "Vila Rica", 
    "Peixoto de Azevedo", "Água Boa", "Juara", "Colíder", "Diamantino", "Canarana", 
    "Campo Verde", "Aripuanã", "Nova Xavantina", "Sapezal", "Poxoréu", "Jaciara", 
    "Brasnorte", "Paranatinga", "Pedra Preta", "Guiratinga", "Nova Bandeirantes", 
    "São José do Rio Claro", "Araputanga", "Matupá", "Nobres", "Alto Araguaia", 
    "Vila Bela da Santíssima Trindade", "Campinápolis", "Juruena", "Porto Alegre do Norte", 
    "Cláudia", "Comodoro", "Vera", "Denise", "Rosário Oeste", "Nossa Senhora do Livramento",
    "São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Fortaleza", "Belo Horizonte", 
    "Manaus", "Curitiba", "Recife", "Porto Alegre", "Belém", "Goiânia", "Guarulhos", 
    "Campinas", "São Luís", "Maceió", "Duque de Caxias", "Campo Grande", "Natal", 
    "Teresina", "São Bernardo do Campo", "João Pessoa", "Osasco", "Santo André", 
    "Jaboatão dos Guararapes", "Uberlândia", "Contagem", "Sorocaba", "Ribeirão Preto", 
    "Aracaju", "Feira de Santana", "Cuiabá", "Joinville", "Aparecida de Goiânia", 
    "Londrina", "Ananindeua", "Porto Velho", "Serra", "Niterói", "Belford Roxo", 
    "Caxias do Sul", "Campos dos Goytacazes", "Macapá", "Florianópolis", "Boa Vista",
    "Rio Branco", "Vitória", "Palmas"
]

# ==========================================
# PIPELINE DE SANITIZAÇÃO
# ==========================================

@lru_cache(maxsize=1000)
def fuzzy_match_cidade(nome_sujo):
    """Etapa 3: Fuzzy Matching contra lista de referência."""
    if not nome_sujo: return ""
    result = process.extractOne(nome_sujo, CIDADES_REFERENCIA, processor=utils.default_process)
    if result and result[1] >= 85:
        return result[0]
    return nome_sujo.title()

def remover_acentos(texto):
    if pd.isna(texto): return ""
    texto = str(texto).lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFKD', texto) 
                  if unicodedata.category(c) != 'Mn')

def sanitizar_pipeline(cidade_origem):
    """Pipeline Triple-Stage Fail-Fast (Expanded LATAM)."""
    if pd.isna(cidade_origem): return "Não Informado", False
    
    texto_raw = str(cidade_origem).lower().strip()
    
    # ---------------------------------------------------------
    # STAGE 1: TRADUTOR DE ESTRANGEIROS (Expansão LATAM)
    # ---------------------------------------------------------
    mapeamento_estrangeiro = {
        r'\b(usa|eua|united states|texas|florida|miami|new york|orlando)\b': "Estados Unidos",
        r'\b(france|franca|paris)\b': "França",
        r'\b(belgium|belgica|brussels|bruxelas)\b': "Bélgica",
        r'\b(czech|tcheca|prague)\b': "República Tcheca",
        r'\b(argentina|buenos aires|cordoba|rosario)\b': "Argentina",
        r'\b(bolivia|la paz|santa cruz|sucre)\b': "Bolívia",
        r'\b(paraguay|paraguai|asuncion|assuncao)\b': "Paraguai",
        r'\b(chile|santiago|valparaiso)\b': "Chile",
        r'\b(uruguay|uruguai|montevideo|punta del este)\b': "Uruguai",
        r'\b(colombia|bogota|medellin|cartagena)\b': "Colômbia",
        r'\b(peru|lima|cusco|machu picchu)\b': "Peru",
        r'\b(venezuela|caracas|maracaibo)\b': "Venezuela",
        r'\b(ecuador|equador|quito|guayaquil)\b': "Equador",
        r'\b(mexico|cancun|mexico city)\b': "México",
        r'\b(portugal|lisboa|porto)\b': "Portugal",
        r'\b(spain|espanha|madrid|barcelona)\b': "Espanha",
        r'\b(italy|italia|rome|roma|milano)\b': "Itália",
        r'\b(germany|alemanha|berlin|munich)\b': "Alemanha",
        r'\b(japan|japao|tokyo|toquio)\b': "Japão",
        r'\b(china|beijing|shanghai)\b': "China",
        r'\b(uk|reino unido|london|londres|england|inglaterra)\b': "Reino Unido"
    }
    
    for regex, pais in mapeamento_estrangeiro.items():
        if re.search(regex, texto_raw):
            return pais, True
            
    # ---------------------------------------------------------
    # STAGE 2: SIGLAS E LIMPEZA LOCAL
    # ---------------------------------------------------------
    c_limpa = remover_acentos(texto_raw)
    c_limpa = re.sub(r'(\bmt\b|\bbr\b|\bbrasil\b|[-/])', ' ', c_limpa).strip()
    c_limpa = re.sub(r'\s+', ' ', c_limpa)
    
    siglas = {
        r'\bcba\b': "Cuiabá",
        r'\bvg\b': "Várzea Grande",
        r'\bsp\b': "São Paulo",
        r'\bbh\b': "Belo Horizonte",
        r'\brj\b': "Rio de Janeiro",
        r'\bcgr\b': "Campo Grande",
        r'\bcur\b': "Curitiba",
        r'\bgyn\b': "Goiânia"
    }
    
    for sigla_re, nome_oficial in siglas.items():
        if re.search(sigla_re, c_limpa):
            return nome_oficial, False

    # ---------------------------------------------------------
    # STAGE 3: FUZZY MATCHING
    # ---------------------------------------------------------
    nome_final = fuzzy_match_cidade(c_limpa)
    return nome_final, False

# ==========================================
# UPLOAD E CARREGAMENTO
# ==========================================
uploaded_files = st.file_uploader(
    "Upload de arquivos de visitantes (XLSX ou CSV)", 
    type=['xlsx', 'csv'], 
    accept_multiple_files=True
)

if uploaded_files:
    dataframes = []
    
    for f in uploaded_files:
        try:
            if f.name.endswith('.csv'):
                try: df_cur = pd.read_csv(f)
                except: df_cur = pd.read_csv(f, encoding='latin1', sep=';')
            else:
                df_cur = pd.read_excel(f)
            
            if df_cur.shape[1] >= 6:
                df_cur = df_cur.iloc[:, 0:7]
                df_cur.columns = ['Data_Hora', 'Nome', 'Cidade_Origem', 'Whatsapp', 'Idade', 'Qtd_Criancas', 'Obs']
                dataframes.append(df_cur)
        except Exception as e:
            st.error(f"Erro no arquivo {f.name}: {e}")

    if not dataframes:
        st.stop()

    df_raw = pd.concat(dataframes, ignore_index=True)

    try:
        # ==========================================
        # PIPELINE DE TRATAMENTO
        # ==========================================
        
        # 1. Datas
        df_raw['Data_Hora'] = pd.to_datetime(df_raw['Data_Hora'], errors='coerce')
        df = df_raw.dropna(subset=['Data_Hora']).copy()
        df['Data'] = df['Data_Hora'].dt.date
        mapa_dias = {'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta', 'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}
        df['Dia_Semana'] = df['Data_Hora'].dt.strftime('%A').map(mapa_dias)
        df['Dia_Semana'] = pd.Categorical(df['Dia_Semana'], categories=list(mapa_dias.values()), ordered=True)

        # 2. Sanitização Numérica
        def process_criancas(val):
            if pd.isna(val): return 0
            s = str(val).lower().strip()
            if any(term in s for term in ["nenhum", "nenhuma", "não", "nao", "zero"]): return 0
            match = re.search(r'(\d+)', s)
            return int(match.group(1)) if match else 0

        df['Qtd_Criancas'] = df['Qtd_Criancas'].apply(process_criancas)
        
        lim_exc = 40
        med_cr = df[df['Qtd_Criancas'] <= lim_exc]['Qtd_Criancas'].mean()
        df.loc[df['Qtd_Criancas'] > lim_exc, 'Qtd_Criancas'] = int(round(med_cr)) if not np.isnan(med_cr) else 0

        def process_idade(val):
            if pd.isna(val): return np.nan
            match = re.search(r'(\d+)', str(val))
            if match:
                idade = int(match.group(1))
                return idade if 1 <= idade <= 120 else np.nan
            return np.nan

        df['Idade'] = df['Idade'].apply(process_idade)

        # 3. Sanitização 3-Stage
        with st.spinner("Aplicando Inteligência Geográfica..."):
            resultados = df['Cidade_Origem'].apply(sanitizar_pipeline)
            df['Cidade_Limpa'] = [r[0] for r in resultados]
            df['Estrangeiro'] = [r[1] for r in resultados]

        df['Total_Visitantes_Linha'] = 1 + df['Qtd_Criancas']
        df['Tipo_Grupo'] = df['Qtd_Criancas'].apply(lambda x: 'Família/Grupo' if x > 0 else 'Individual/Adultos')

        # ==========================================
        # INTERFACE E FILTROS
        # ==========================================
        st.sidebar.header("🔍 Filtros Avançados")
        periodo = st.sidebar.date_input("Intervalo de Datas", [df['Data'].min(), df['Data'].max()])
        gringos_only = st.sidebar.toggle("Focar Apenas em Estrangeiros")

        df_f = df.copy()
        if len(periodo) == 2:
            df_f = df_f[(df_f['Data'] >= periodo[0]) & (df_f['Data'] <= periodo[1])]
        if gringos_only:
            df_f = df_f[df_f['Estrangeiro']]

        if df_f.empty:
            st.warning("Sem dados para os filtros selecionados.")
        else:
            # KPIs
            t_ge = int(df_f['Total_Visitantes_Linha'].sum())
            t_ad = len(df_f)
            t_cr = int(df_f['Qtd_Criancas'].sum())
            t_est = int(df_f[df_f['Estrangeiro']]['Total_Visitantes_Linha'].sum())

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Público Total", f"{t_ge:,}".replace(',','.'))
            c2.metric("Adultos", f"{t_ad:,}".replace(',','.'))
            c3.metric("Crianças", f"{t_cr:,}".replace(',','.'))
            c4.metric("Estrangeiros", f"{t_est:,}".replace(',','.'))
            
            st.markdown("---")
            
            # BOTÃO DE EXPORTAÇÃO (FILTRADO)
            csv = df_f.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Planilha Higienizada (CSV)",
                data=csv,
                file_name='visitantes_higienizados.csv',
                mime='text/csv',
            )

            # Gráficos (Matplotlib/Seaborn)
            sns.set_theme(style="whitegrid")
            fig = plt.figure(figsize=(22, 14))
            plt.subplots_adjust(hspace=0.4, wspace=0.3)
            plt.suptitle('Dashboard Aquário - Análise Inteligente', fontsize=18, fontweight='bold', y=0.98)

            # 1. Composição
            plt.subplot(2, 3, 1)
            plt.pie([t_ad, t_cr], labels=['Adultos', 'Crianças'], autopct='%1.1f%%', colors=['#3498db', '#f1c40f'], startangle=90, explode=(0.05, 0))
            plt.title('Distribuição Adultos vs Crianças', fontweight='bold')

            # 2. Perfil
            plt.subplot(2, 3, 2)
            df_f['Tipo_Grupo'].value_counts().plot.pie(autopct='%1.1f%%', colors=['#e74c3c', '#2ecc71'], startangle=90)
            plt.title('Perfil dos Visitantes', fontweight='bold')
            plt.ylabel('')

            # 3. Evolução
            plt.subplot(2, 3, 3)
            df_f.groupby('Data')['Total_Visitantes_Linha'].sum().plot(marker='o', color='#8e44ad')
            plt.title('Fluxo de Visitantes no Período', fontweight='bold')
            plt.xticks(rotation=45)

            # 4. Médias
            plt.subplot(2, 3, 4)
            media_op = df_f.groupby('Dia_Semana')['Total_Visitantes_Linha'].sum() / df_f.groupby('Dia_Semana')['Data'].nunique()
            sns.barplot(x=media_op.index, y=media_op.values, palette="rocket")
            plt.title('Média de Visitantes por Dia', fontweight='bold')

            # 5. Top Cidades
            plt.subplot(2, 3, 5)
            top_10 = df_f['Cidade_Limpa'].value_counts().head(10)
            sns.barplot(x=top_10.values, y=top_10.index, palette="viridis")
            plt.title('Top 10 Cidades de Origem', fontweight='bold')

            # 6. Estrangeiros
            plt.subplot(2, 3, 6)
            if t_est > 0:
                top_es = df_f[df_f['Estrangeiro']]['Cidade_Limpa'].value_counts().head(5)
                sns.barplot(x=top_es.values, y=top_es.index, palette="copper")
                plt.title('Top Países Estrangeiros', fontweight='bold')
            else:
                plt.text(0.5, 0.5, "Sem Estrangeiros no Período", ha='center', va='center', color='gray')
                plt.axis('off')

            st.pyplot(fig)

    except Exception as e:
        st.error(f"🚨 Erro no processamento: {e}")
else:
    st.info("💡 Carregue os arquivos para consolidar a análise e liberar a exportação.")

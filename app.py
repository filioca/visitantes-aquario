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
# CONFIGURAÇÃO E ESTILO (UI UX PRO MAX)
# ==========================================
st.set_page_config(
    page_title="SIT - Sistema de Inteligência Turística",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta de Cores Institucional (Cuiabá Premium - Civic Blue & Gold)
# Primary: #003366 (Civic Blue)
# Accent: #C5A059 (Metallic Gold)
# Background: #F3F4F6 (Cool Gray)
# Text: #1F2937 (Slate 800)

st.markdown("""
    <style>
    /* Global Font & Background */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1F2937;
    }
    
    .stApp {
        background-color: #F3F4F6;
    }

    /* Header Container */
    .header-container {
        background: linear-gradient(135deg, #003366 0%, #004080 100%);
        padding: 2rem 2rem;
        border-radius: 12px;
        color: white;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 2rem;
    }
    
    .header-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.025em;
        color: #ffffff !important;
    }
    
    .header-subtitle {
        font-size: 1rem;
        font-weight: 400;
        opacity: 0.9;
        margin-top: 0.5rem;
        color: #E5E7EB !important;
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        transition: transform 0.2s;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        border-color: #C5A059;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        color: #6B7280;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
        color: #003366;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: transparent;
        padding-bottom: 1rem;
        border-bottom: 2px solid #E5E7EB;
    }

    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px;
        color: #6B7280;
        font-weight: 600;
        font-size: 1rem;
        padding: 0 1rem;
        border: none;
    }

    .stTabs [aria-selected="true"] {
        color: #003366;
        border-bottom: 3px solid #C5A059; /* Gold accent */
        background-color: rgba(197, 160, 89, 0.05);
    }

    /* Button Styling */
    .stDownloadButton button {
        background-color: #003366 !important;
        color: white !important;
        border: none !important;
        padding: 0.6rem 1.5rem !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: background-color 0.2s;
    }
    
    .stDownloadButton button:hover {
        background-color: #002244 !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #E5E7EB;
    }
    
    .sidebar-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #C5A059;
        display: inline-block;
    }

    </style>
    """, unsafe_allow_html=True)

# Header Institucional
st.markdown("""
    <div class="header-container">
        <h1 class="header-title">🏛️ SIT - Sistema de Inteligência Turística</h1>
        <p class="header-subtitle">Prefeitura Municipal de Cuiabá • Secretaria de Turismo • Gestão de Dados</p>
    </div>
""", unsafe_allow_html=True)

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
    "Aracaju", "Feira de Santana", "Joinville", "Aparecida de Goiânia", 
    "Londrina", "Ananindeua", "Porto Velho", "Serra", "Niterói", "Belford Roxo", 
    "Caxias do Sul", "Campos dos Goytacazes", "Macapá", "Florianópolis", "Boa Vista",
    "Rio Branco", "Vitória", "Palmas"
]

# ==========================================
# PIPELINE DE SANITIZAÇÃO
# ==========================================

@lru_cache(maxsize=1000)
def fuzzy_match_cidade(nome_sujo):
    """Etapa 3: Fuzzy Matching contra lista de referência (Score 80)."""
    if not nome_sujo: return ""
    result = process.extractOne(nome_sujo, CIDADES_REFERENCIA, processor=utils.default_process)
    if result and result[1] >= 80:
        return result[0]
    return nome_sujo.title()

def remover_acentos(texto):
    if pd.isna(texto): return ""
    texto = str(texto).lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFKD', texto) 
                  if unicodedata.category(c) != 'Mn')

def sanitizar_pipeline(cidade_origem):
    """Pipeline Triple-Stage Otimizado (Regex Vassoura + Fallback com Acento)."""
    if pd.isna(cidade_origem): return "Não Informado", False
    
    texto_raw = str(cidade_origem).strip()
    texto_lower = texto_raw.lower()
    
    # STAGE 1: TRADUTOR DE ESTRANGEIROS (Expansão LATAM)
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
        if re.search(regex, texto_lower):
            return pais, True
            
    # STAGE 2: REGEX VASSOURA & LIMPEZA DE PONTUAÇÃO
    c_limpa = texto_raw
    regex_ufs = r'\b(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)\b'
    c_limpa = re.sub(regex_ufs, ' ', c_limpa, flags=re.IGNORECASE)
    regex_lixo = r'\b(brasil|mato grosso|cidade|estado|municipio)\b'
    c_limpa = re.sub(regex_lixo, ' ', c_limpa, flags=re.IGNORECASE)
    c_limpa = re.sub(r'[^a-zA-ZÀ-ÿ\s]', ' ', c_limpa)
    c_limpa = re.sub(r'\s+', ' ', c_limpa).strip()
    
    if not c_limpa or len(c_limpa) < 2:
        return "Não Informado", False

    c_temp_norm = remover_acentos(c_limpa)
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
        if re.search(sigla_re, c_temp_norm):
            return nome_oficial, False

    # STAGE 3: FUZZY MATCHING
    nome_final = fuzzy_match_cidade(c_limpa)
    return nome_final, False

# ==========================================
# UPLOAD E CARREGAMENTO
# ==========================================
uploaded_files = st.sidebar.file_uploader(
    "📂 Importar Dados (XLSX/CSV)", 
    type=['xlsx', 'csv'], 
    accept_multiple_files=True,
    help="Carregue as planilhas de cadastro de visitantes para iniciar o processamento."
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
        df_raw['Data_Hora'] = pd.to_datetime(df_raw['Data_Hora'], errors='coerce')
        df = df_raw.dropna(subset=['Data_Hora']).copy()
        
        df['Data'] = df['Data_Hora'].dt.date
        df['Hora'] = df['Data_Hora'].dt.hour.fillna(0).astype(int)
        
        mapa_dias = {'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta', 'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}
        df['Dia_Semana'] = df['Data_Hora'].dt.strftime('%A').map(mapa_dias)
        df['Dia_Semana'] = pd.Categorical(df['Dia_Semana'], categories=list(mapa_dias.values()), ordered=True)

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

        def definir_faixa_etaria(idade):
            if pd.isna(idade): return "Não Informado"
            if idade <= 12: return "Criança (0-12)"
            elif idade <= 17: return "Adolescente (13-17)"
            elif idade <= 35: return "Jovem Adulto (18-35)"
            elif idade <= 59: return "Adulto (36-59)"
            else: return "Idoso (60+)"

        df['Faixa_Etaria'] = df['Idade'].apply(definir_faixa_etaria)
        faixas_ordem = ["Criança (0-12)", "Adolescente (13-17)", "Jovem Adulto (18-35)", "Adulto (36-59)", "Idoso (60+)", "Não Informado"]
        df['Faixa_Etaria'] = pd.Categorical(df['Faixa_Etaria'], categories=faixas_ordem, ordered=True)

        with st.spinner("Processando Inteligência de Dados..."):
            resultados = df['Cidade_Origem'].apply(sanitizar_pipeline)
            df['Cidade_Limpa'] = [r[0] for r in resultados]
            df['Estrangeiro'] = [r[1] for r in resultados]

        df['Total_Visitantes_Linha'] = 1 + df['Qtd_Criancas']
        df['Tipo_Grupo'] = df['Qtd_Criancas'].apply(lambda x: 'Família/Grupo' if x > 0 else 'Individual/Adultos')

        # ==========================================
        # INTERFACE E FILTROS
        # ==========================================
        st.sidebar.markdown('<div class="sidebar-header">🛠️ Painel de Controle</div>', unsafe_allow_html=True)
        
        periodo = st.sidebar.date_input("📅 Período de Análise", [df['Data'].min(), df['Data'].max()])
        cidades_sel = st.sidebar.multiselect("📍 Filtrar Origem (Cidades)", sorted(df['Cidade_Limpa'].unique()))
        grupos_sel = st.sidebar.multiselect("👥 Tipologia de Grupo", df['Tipo_Grupo'].unique())
        gringos_only = st.sidebar.toggle("🌐 Apenas Visitantes Internacionais")

        df_f = df.copy()
        if len(periodo) == 2:
            df_f = df_f[(df_f['Data'] >= periodo[0]) & (df_f['Data'] <= periodo[1])]
        
        if cidades_sel:
            df_f = df_f[df_f['Cidade_Limpa'].isin(cidades_sel)]
        if grupos_sel:
            df_f = df_f[df_f['Tipo_Grupo'].isin(grupos_sel)]
            
        if gringos_only:
            df_f = df_f[df_f['Estrangeiro']]

        if df_f.empty:
            st.warning("⚠️ Nenhum registro encontrado para os filtros aplicados.")
        else:
            # TABS PROFISSIONAIS
            tab1, tab2 = st.tabs(["📊 Visão Estratégica", "🔍 Análise Tática & Demográfica"])

            with tab1:
                # KPIs
                t_ge = int(df_f['Total_Visitantes_Linha'].sum())
                t_ad = len(df_f)
                t_cr = int(df_f['Qtd_Criancas'].sum())
                t_est = int(df_f[df_f['Estrangeiro']]['Total_Visitantes_Linha'].sum())

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Fluxo Total", f"{t_ge:,}".replace(',','.'))
                c2.metric("Público Adulto", f"{t_ad:,}".replace(',','.'))
                c3.metric("Público Infantil", f"{t_cr:,}".replace(',','.'))
                c4.metric("Turistas Internacionais", f"{t_est:,}".replace(',','.'))
                
                st.markdown("---")
                
                # BOTÃO DE EXPORTAÇÃO
                csv = df_f.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Exportar Dados Processados (.CSV)",
                    data=csv,
                    file_name='SIT_Visitantes_Processados.csv',
                    mime='text/csv',
                )

                # Gráficos (Visual Clean e Corporativo)
                # Configurando paleta corporativa para Matplotlib
                plt.rcParams['font.family'] = 'sans-serif'
                plt.rcParams['text.color'] = '#1F2937'
                plt.rcParams['axes.labelcolor'] = '#4B5563'
                plt.rcParams['xtick.color'] = '#4B5563'
                plt.rcParams['ytick.color'] = '#4B5563'
                
                sns.set_theme(style="whitegrid", rc={"axes.facecolor": ".98", "grid.color": ".90"})
                fig = plt.figure(figsize=(22, 14))
                plt.subplots_adjust(hspace=0.4, wspace=0.3)
                
                # Título discreto removido pois já está no header do app
                # plt.suptitle('Indicadores Estratégicos', fontsize=16, fontweight='bold', y=0.98, color='#003366')

                # 1. Composição
                plt.subplot(2, 3, 1)
                # Cores: Civic Blue e Muted Gold
                plt.pie([t_ad, t_cr], labels=['Adultos', 'Crianças'], autopct='%1.1f%%', colors=['#003366', '#C5A059'], startangle=90, explode=(0.05, 0), textprops={'fontsize': 11})
                plt.title('Segmentação Etária Macro', fontweight='bold', color='#111827')

                # 2. Perfil
                plt.subplot(2, 3, 2)
                # Cores: Deep Teal e Slate Blue
                df_f['Tipo_Grupo'].value_counts().plot.pie(autopct='%1.1f%%', colors=['#0D9488', '#475569'], startangle=90, textprops={'fontsize': 11})
                plt.title('Tipologia dos Visitantes', fontweight='bold', color='#111827')
                plt.ylabel('')

                # 3. Evolução
                plt.subplot(2, 3, 3)
                # Cor: Civic Blue
                df_f.groupby('Data')['Total_Visitantes_Linha'].sum().plot(marker='o', color='#003366', linewidth=2)
                plt.title('Tendência de Fluxo Diário', fontweight='bold', color='#111827')
                plt.xlabel('')
                plt.xticks(rotation=45)
                plt.grid(axis='y', linestyle='--', alpha=0.7)

                # 4. Médias
                plt.subplot(2, 3, 4)
                media_op = df_f.groupby('Dia_Semana')['Total_Visitantes_Linha'].sum() / df_f.groupby('Dia_Semana')['Data'].nunique()
                # Palette customizada Blue -> Gold
                sns.barplot(x=media_op.index, y=media_op.values, palette="ch:s=.25,rot=-.25")
                plt.title('Média de Fluxo Semanal', fontweight='bold', color='#111827')
                plt.xlabel('')
                plt.ylabel('Média de Visitantes')

                # 5. Top Cidades
                plt.subplot(2, 3, 5)
                top_10 = df_f['Cidade_Limpa'].value_counts().head(10)
                sns.barplot(x=top_10.values, y=top_10.index, palette="mako")
                plt.title('Top 10 Origens (Nacional)', fontweight='bold', color='#111827')
                plt.xlabel('Volume de Visitantes')

                # 6. Estrangeiros
                plt.subplot(2, 3, 6)
                if t_est > 0:
                    top_es = df_f[df_f['Estrangeiro']]['Cidade_Limpa'].value_counts().head(5)
                    sns.barplot(x=top_es.values, y=top_es.index, palette="copper")
                    plt.title('Top Origens (Internacional)', fontweight='bold', color='#111827')
                else:
                    plt.text(0.5, 0.5, "Sem dados internacionais no período", ha='center', va='center', color='#9CA3AF', fontsize=12)
                    plt.axis('off')

                st.pyplot(fig)

            with tab2:
                st.markdown("### ⏲️ Análise Operacional e Demográfica")
                
                # Gráfico 7: Heatmap de Fluxo
                st.markdown("#### Matriz de Calor: Intensidade Operacional (Dia x Hora)")
                
                heatmap_data = df_f.pivot_table(
                    index='Dia_Semana', 
                    columns='Hora', 
                    values='Total_Visitantes_Linha', 
                    aggfunc='sum',
                    fill_value=0
                )
                
                heatmap_data = heatmap_data.reindex(list(mapa_dias.values()), fill_value=0)
                
                fig7, ax7 = plt.subplots(figsize=(20, 6))
                # Palette: Blues (mais institucional)
                sns.heatmap(heatmap_data, cmap="Blues", annot=True, fmt='g', linewidths=.5, ax=ax7, cbar_kws={'label': 'Volume de Visitantes'})
                plt.title('Mapa de Calor Operacional', fontweight='bold', color='#111827')
                plt.xlabel('Hora do Dia', fontweight='500')
                plt.ylabel('Dia da Semana', fontweight='500')
                st.pyplot(fig7)
                
                st.markdown("---")
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.markdown("#### Pirâmide Etária")
                    
                    df_idade = df_f[df_f['Faixa_Etaria'] != 'Não Informado'] 
                    if df_idade.empty:
                        st.info("Insuficiência de dados etários para plotagem.")
                    else:
                        fig8, ax8 = plt.subplots(figsize=(10, 6))
                        # Palette discreta
                        sns.countplot(y='Faixa_Etaria', data=df_idade, palette="GnBu_d", ax=ax8)
                        for container in ax8.containers:
                            ax8.bar_label(container, padding=5)
                        plt.title('Distribuição Etária Declarada', fontweight='bold')
                        plt.xlabel('Quantidade')
                        plt.ylabel('')
                        # Remover bordas desnecessárias
                        sns.despine(left=True, bottom=True)
                        st.pyplot(fig8)

                with col_b:
                    st.markdown("#### Comportamento de Grupos")
                    
                    fig9, ax9 = plt.subplots(figsize=(10, 6))
                    sns.histplot(data=df_f, x='Total_Visitantes_Linha', discrete=True, color="#003366", kde=True, ax=ax9, alpha=0.7)
                    plt.title('Histograma de Dimensionamento de Grupos', fontweight='bold')
                    plt.xlabel('Nº de Pessoas por Grupo')
                    plt.ylabel('Ocorrências')
                    sns.despine()
                    st.pyplot(fig9)

    except Exception as e:
        st.error(f"🚨 Erro crítico no processamento de dados: {e}")
else:
    # Empty State Profissional
    st.info("⚠️ Aguardando importação de dados. Utilize o painel lateral para carregar os arquivos .CSV ou .XLSX do sistema de cadastro.")

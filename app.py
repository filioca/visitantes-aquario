import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import re

# ==========================================
# CONFIGURAÇÃO E ESTILO
# ==========================================
st.set_page_config(page_title="Dashboard Aquário Pro", layout="wide")

# Custom CSS for Premium Look
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🐠 Dashboard Gerencial - Aquário Municipal")
st.markdown("### Processamento Multi-Arquivos & Inteligência de Localização")
st.info("Arraste um ou mais arquivos Excel (.xlsx) ou CSV para consolidar a análise.")

# ==========================================
# UPLOAD MULTI-ARQUIVOS
# ==========================================
uploaded_files = st.file_uploader(
    "Escolha os arquivos de visitantes", 
    type=['xlsx', 'csv'], 
    accept_multiple_files=True
)

def process_whatsapp(phone):
    """Limpa e extrai DDI do WhatsApp."""
    if pd.isna(phone):
        return None
    # Remove tudo que não é dígito
    clean = re.sub(r'\D', '', str(phone))
    if not clean:
        return None
    return clean

if uploaded_files:
    dataframes = []
    
    for uploaded_file in uploaded_files:
        try:
            if uploaded_file.name.endswith('.csv'):
                try:
                    curr_df = pd.read_csv(uploaded_file)
                except:
                    curr_df = pd.read_csv(uploaded_file, encoding='latin1', sep=';')
            else:
                curr_df = pd.read_excel(uploaded_file)
            
            # Validação Mínima de Colunas (Preservando as 7 originais)
            if curr_df.shape[1] < 6:
                st.warning(f"⚠️ O arquivo `{uploaded_file.name}` parece estar incompleto e foi ignorado.")
                continue
                
            curr_df = curr_df.iloc[:, 0:7]
            curr_df.columns = ['Data_Hora', 'Nome', 'Cidade_Origem', 'Whatsapp', 'Idade', 'Qtd_Criancas', 'Obs']
            dataframes.append(curr_df)
            
        except Exception as e:
            st.error(f"❌ Erro ao ler `{uploaded_file.name}`: {e}")

    if not dataframes:
        st.stop()

    # Consolidar Dados
    df = pd.concat(dataframes, ignore_index=True)
    
    try:
        # ==========================================
        # 1. PIPELINE DE LIMPEZA & TRATAMENTO
        # ==========================================
        
        # --- DATAS (Guard Clause Integrada) ---
        df['Data_Hora'] = pd.to_datetime(df['Data_Hora'], errors='coerce')
        df = df.dropna(subset=['Data_Hora'])
        if df.empty:
            st.error("🚨 Nenhum dado válido encontrado após processar as datas.")
            st.stop()
            
        df['Data'] = df['Data_Hora'].dt.date
        df['Mes'] = df['Data_Hora'].dt.strftime('%Y-%m')
        
        # Tradução Dias da Semana
        mapa_dias = {
            'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta', 
            'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
        }
        df['Dia_Semana'] = df['Data_Hora'].dt.strftime('%A').map(mapa_dias)
        ordem_dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        df['Dia_Semana'] = pd.Categorical(df['Dia_Semana'], categories=ordem_dias, ordered=True)

        # --- CIDADES ---
        df['Cidade_Limpa'] = df['Cidade_Origem'].astype(str).str.strip().str.title()
        df.loc[df['Cidade_Limpa'].str.contains('Cuiab|Cba', case=False, na=False), 'Cidade_Limpa'] = 'Cuiabá'
        df.loc[df['Cidade_Limpa'].str.contains('Varzea|Várzea', case=False, na=False), 'Cidade_Limpa'] = 'Várzea Grande'
        
        # --- IDADES & CRIANÇAS ---
        df['Idade'] = pd.to_numeric(df['Idade'], errors='coerce')
        df = df[(df['Idade'] > 0) & (df['Idade'] <= 100)]
        df['Qtd_Criancas'] = pd.to_numeric(df['Qtd_Criancas'], errors='coerce').fillna(0)
        
        # Lógica de Excursão (Regra de Negócio Mantida)
        limite_excursao = 40
        media_real = df.loc[df['Qtd_Criancas'] <= limite_excursao, 'Qtd_Criancas'].mean()
        media_real = int(round(media_real)) if not np.isnan(media_real) else 0
        df.loc[df['Qtd_Criancas'] > limite_excursao, 'Qtd_Criancas'] = media_real
        
        df['Total_Visitantes_Linha'] = 1 + df['Qtd_Criancas']
        df['Tipo_Grupo'] = df['Qtd_Criancas'].apply(lambda x: 'Família/Grupo' if x > 0 else 'Individual/Adultos')

        # --- DETECÇÃO AVANÇADA DE ESTRANGEIROS ---
        # 1. Via WhatsApp (DDI)
        df['Whatsapp_Clean'] = df['Whatsapp'].apply(process_whatsapp)
        
        def is_foreign_ddi(val):
            if not val: return False
            # Se começar com 55 (Brasil), não é estrangeiro via DDI
            # Consideramos estrangeiro se tiver DDI e não for 55
            # Números brasileiros sem DDI costumam ter 10-11 dígitos. 
            # Se tiver mais que isso e não começar com 55, é forte indício.
            if len(val) >= 10:
                if not val.startswith('55'):
                    return True
            return False

        df['Estrangeiro_DDI'] = df['Whatsapp_Clean'].apply(is_foreign_ddi)

        # 2. Via Localização (Regex Fallback)
        termos_estrangeiros = ['Argentina', 'Bolivia', 'Paraguay', 'Uruguay', 'Chile', 'Peru', 'Colombia', 'Usa', 'Portugal', 'Spain', 'France', 'Italy', 'Germany', 'China', 'Japan', 'Bolívia', 'Paraguai', 'Uruguai']
        termos_proibidos_brasil = ['Mt', 'Ms', 'Sp', 'Rj', 'Mg', 'Pr', 'Sc', 'Rs', 'Go', 'Df', 'Brasil', 'Mato Grosso', 'São Paulo', 'Rio De Janeiro']
        regex_estrangeiro = r'\b(' + '|'.join(termos_estrangeiros) + r')\b'
        regex_proibido = r'\b(' + '|'.join(termos_proibidos_brasil) + r')\b'
        
        df['Estrangeiro_Local'] = df['Cidade_Limpa'].str.contains(regex_estrangeiro, case=False, regex=True, na=False) & \
                                 (~df['Cidade_Limpa'].str.contains(regex_proibido, case=False, regex=True, na=False))
        
        # 3. Consolidação (Cross-check)
        df['Estrangeiro'] = df['Estrangeiro_DDI'] | df['Estrangeiro_Local']

        # ==========================================
        # 2. SIDEBAR - FILTROS DINÂMICOS
        # ==========================================
        st.sidebar.header("🔍 Filtros Consolidados")
        
        min_date = df['Data'].min()
        max_date = df['Data'].max()
        periodo = st.sidebar.date_input("Período de Análise", [min_date, max_date], min_value=min_date, max_value=max_date)
        
        cidades_unicas = sorted(df['Cidade_Limpa'].unique())
        cidades_sel = st.sidebar.multiselect("Cidades de Origem", cidades_unicas, default=[])
        
        tipos_sel = st.sidebar.multiselect("Perfil do Visitante", df['Tipo_Grupo'].unique(), default=list(df['Tipo_Grupo'].unique()))
        
        ver_apenas_estrangeiros = st.sidebar.toggle("Focar apenas em Estrangeiros", value=False)

        # ==========================================
        # 3. APLICAÇÃO DOS FILTROS
        # ==========================================
        df_f = df.copy()
        
        if len(periodo) == 2:
            df_f = df_f[(df_f['Data'] >= periodo[0]) & (df_f['Data'] <= periodo[1])]
            
        if cidades_sel:
            df_f = df_f[df_f['Cidade_Limpa'].isin(cidades_sel)]
            
        df_f = df_f[df_f['Tipo_Grupo'].isin(tipos_sel)]
        
        if ver_apenas_estrangeiros:
            df_f = df_f[df_f['Estrangeiro'] == True]

        # ==========================================
        # 4. EXIBIÇÃO DE RESULTADOS
        # ==========================================
        if df_f.empty:
            st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados.")
        else:
            total_adultos = len(df_f)
            total_criancas = int(df_f['Qtd_Criancas'].sum())
            total_geral = total_adultos + total_criancas
            df_est = df_f[df_f['Estrangeiro'] == True]
            qtd_estrangeiros = int(df_est['Total_Visitantes_Linha'].sum())

            st.success(f"✅ Consolidação Concluída: {len(df_f)} registros de {len(dataframes)} arquivo(s).")
            
            # KPIs
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Público Total", f"{total_geral:,}".replace(',','.'))
            col2.metric("Adultos", f"{total_adultos:,}".replace(',','.'))
            col3.metric("Crianças", f"{total_criancas:,}".replace(',','.'))
            col4.metric("Estrangeiros", f"{qtd_estrangeiros:,}".replace(',','.'))
            st.markdown("---")

            # Estilo de Gráficos
            sns.set_theme(style="whitegrid")
            fig = plt.figure(figsize=(22, 14))
            plt.subplots_adjust(hspace=0.4, wspace=0.3)
            plt.suptitle('Análise Consolidada de Visitantes - Aquário Municipal', fontsize=18, fontweight='bold', y=0.98)
            
            # 1. Composição
            plt.subplot(2, 3, 1)
            plt.pie([total_adultos, total_criancas], labels=['Adultos', 'Crianças'], 
                    autopct='%1.1f%%', colors=['#3498db', '#f1c40f'], startangle=90, explode=(0.05, 0))
            plt.title('Distribuição Adultos vs Crianças', fontsize=14, fontweight='bold')

            # 2. Perfil Visitantes
            plt.subplot(2, 3, 2)
            contagem_grupo = df_f['Tipo_Grupo'].value_counts()
            if not contagem_grupo.empty:
                plt.pie(contagem_grupo, labels=contagem_grupo.index, autopct='%1.1f%%', 
                        colors=['#e74c3c', '#2ecc71'], startangle=90, wedgeprops={'alpha':0.8})
                plt.title('Perfil dos Grupos', fontsize=14, fontweight='bold')

            # 3. Evolução Diária
            plt.subplot(2, 3, 3)
            evolucao = df_f.groupby('Data')['Total_Visitantes_Linha'].sum()
            evolucao.plot(kind='line', marker='o', color='#8e44ad', linewidth=2)
            plt.title('Evolução do Fluxo Diário', fontsize=14, fontweight='bold')
            plt.xlabel('Data')
            plt.ylabel('Visitantes')
            plt.xticks(rotation=45)

            # 4. Média por Dia da Semana
            plt.subplot(2, 3, 4)
            soma_dia = df_f.groupby('Dia_Semana')['Total_Visitantes_Linha'].sum()
            qtd_dias = df_f.groupby('Dia_Semana')['Data'].nunique()
            media = (soma_dia / qtd_dias).fillna(0)
            sns.barplot(x=media.index, y=media.values, palette="rocket")
            plt.title('Média por Dia da Semana', fontsize=14, fontweight='bold')
            plt.xlabel('Dia')
            plt.ylabel('Média')

            # 5. Top Cidades
            plt.subplot(2, 3, 5)
            top_cid = df_f['Cidade_Limpa'].value_counts().head(10)
            if not top_cid.empty:
                sns.barplot(x=top_cid.values, y=top_cid.index, palette="viridis")
                plt.title('Top 10 Cidades de Origem', fontsize=14, fontweight='bold')
                plt.xlabel('Visitantes')
                plt.ylabel('Cidade')

            # 6. Estrangeiros (Top 5)
            plt.subplot(2, 3, 6)
            if qtd_estrangeiros > 0:
                top_est = df_est['Cidade_Limpa'].value_counts().head(5)
                sns.barplot(x=top_est.values, y=top_est.index, palette="copper")
                plt.title('Origem dos Estrangeiros (Top 5)', fontsize=14, fontweight='bold')
                plt.xlabel('Visitantes')
                plt.ylabel('País/Cidade')
            else:
                plt.text(0.5, 0.5, "Sem registros internacionais\nno período selecionado", 
                         ha='center', va='center', fontsize=12, color='gray')
                plt.axis('off')

            st.pyplot(fig)

    except Exception as e:
        st.error(f"🚨 Erro crítico no pipeline de dados: {e}")
else:
    st.info("💡 Sugestão: Você pode carregar vários meses de uma vez para ver a evolução histórica.")

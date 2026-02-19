import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Configuração da Página
st.set_page_config(page_title="Dashboard Aquário", layout="wide")
st.title("🐠 Dashboard Gerencial - Aquário Municipal")
st.markdown("Faça o upload da planilha de visitantes para gerar a análise automática.")

# UPLOAD
uploaded_file = st.file_uploader("Escolha o arquivo Excel (.xlsx) ou CSV", type=['xlsx', 'csv'])

if uploaded_file is not None:
    try:
        # ==========================================
        # 1. LEITURA E PADRONIZAÇÃO
        # ==========================================
        if uploaded_file.name.endswith('.csv'):
            try:
                df_raw = pd.read_csv(uploaded_file)
            except:
                df_raw = pd.read_csv(uploaded_file, encoding='latin1', sep=';')
        else:
            df_raw = pd.read_excel(uploaded_file)
            
        # Padronização de Colunas (Fixando as primeiras 7 colunas)
        df_raw = df_raw.iloc[:, 0:7]
        df_raw.columns = ['Data_Hora', 'Nome', 'Cidade_Origem', 'Whatsapp', 'Idade', 'Qtd_Criancas', 'Obs']
        
        # ==========================================
        # 2. LIMPEZA E TRATAMENTO
        # ==========================================
        df = df_raw.copy()
        
        # --- DATAS ---
        df['Data_Hora'] = pd.to_datetime(df['Data_Hora'], errors='coerce')
        df = df.dropna(subset=['Data_Hora'])
        df['Data'] = df['Data_Hora'].dt.date
        df['Mes'] = df['Data_Hora'].dt.strftime('%Y-%m')
        
        # Tradução Dias da Semana
        df['Dia_Semana_Ingles'] = df['Data_Hora'].dt.strftime('%A')
        mapa_dias = {
            'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta', 
            'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
        }
        df['Dia_Semana'] = df['Dia_Semana_Ingles'].map(mapa_dias)
        ordem_dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        df['Dia_Semana'] = pd.Categorical(df['Dia_Semana'], categories=ordem_dias, ordered=True)

        # --- CIDADES ---
        df['Cidade_Limpa'] = df['Cidade_Origem'].astype(str).str.strip().str.title()
        df.loc[df['Cidade_Limpa'].str.contains('Cuiab|Cba', case=False), 'Cidade_Limpa'] = 'Cuiabá'
        df.loc[df['Cidade_Limpa'].str.contains('Varzea|Várzea', case=False), 'Cidade_Limpa'] = 'Várzea Grande'
        
        # --- IDADES & CRIANÇAS ---
        df['Idade'] = pd.to_numeric(df['Idade'], errors='coerce')
        df = df[(df['Idade'] > 0) & (df['Idade'] <= 100)]
        df['Qtd_Criancas'] = pd.to_numeric(df['Qtd_Criancas'], errors='coerce').fillna(0)
        
        # Lógica de Excursão (Preservada conforme original)
        limite_excursao = 40
        media_real = df.loc[df['Qtd_Criancas'] <= limite_excursao, 'Qtd_Criancas'].mean()
        media_real = int(round(media_real)) if not np.isnan(media_real) else 0
        df.loc[df['Qtd_Criancas'] > limite_excursao, 'Qtd_Criancas'] = media_real
        
        df['Total_Visitantes_Linha'] = 1 + df['Qtd_Criancas']
        df['Tipo_Grupo'] = df['Qtd_Criancas'].apply(lambda x: 'Família/Grupo' if x > 0 else 'Individual/Adultos')

        # --- ESTRANGEIROS ---
        termos_estrangeiros = [
            'Argentina', 'Bolivia', 'Paraguay', 'Uruguay', 'Chile', 'Peru', 
            'Colombia', 'Usa', 'Portugal', 'Spain', 'France', 'Italy', 
            'Germany', 'China', 'Japan', 'Bolívia', 'Paraguai', 'Uruguai'
        ]
        termos_proibidos_brasil = [
            'Mt', 'Ms', 'Sp', 'Rj', 'Mg', 'Pr', 'Sc', 'Rs', 'Go', 'Df', 
            'Brasil', 'Mato Grosso', 'São Paulo', 'Rio De Janeiro'
        ]
        regex_estrangeiro = r'\b(' + '|'.join(termos_estrangeiros) + r')\b'
        regex_proibido = r'\b(' + '|'.join(termos_proibidos_brasil) + r')\b'
        df['Estrangeiro'] = df['Cidade_Limpa'].str.contains(regex_estrangeiro, case=False, regex=True) & \
                           (~df['Cidade_Limpa'].str.contains(regex_proibido, case=False, regex=True))

        # ==========================================
        # 3. SIDEBAR - FILTROS DINÂMICOS
        # ==========================================
        st.sidebar.header("🔍 Filtros de Análise")
        
        # Filtro de Data
        min_date = df['Data'].min()
        max_date = df['Data'].max()
        periodo = st.sidebar.date_input("Período de Análise", [min_date, max_date], min_value=min_date, max_value=max_date)
        
        # Filtro de Cidade
        cidades_unicas = sorted(df['Cidade_Limpa'].unique())
        cidades_sel = st.sidebar.multiselect("Cidades de Origem", cidades_unicas, default=[])
        
        # Filtro Tipo de Grupo
        tipos_sel = st.sidebar.multiselect("Perfil do Visitante", df['Tipo_Grupo'].unique(), default=list(df['Tipo_Grupo'].unique()))
        
        # Toggle Estrangeiros
        ver_apenas_estrangeiros = st.sidebar.toggle("Ver apenas Estrangeiros", value=False)

        # ==========================================
        # 4. APLICAÇÃO DOS FILTROS
        # ==========================================
        df_filtered = df.copy()
        
        if len(periodo) == 2:
            start_date, end_date = periodo
            df_filtered = df_filtered[(df_filtered['Data'] >= start_date) & (df_filtered['Data'] <= end_date)]
            
        if cidades_sel:
            df_filtered = df_filtered[df_filtered['Cidade_Limpa'].isin(cidades_sel)]
            
        df_filtered = df_filtered[df_filtered['Tipo_Grupo'].isin(tipos_sel)]
        
        if ver_apenas_estrangeiros:
            df_filtered = df_filtered[df_filtered['Estrangeiro'] == True]

        # ==========================================
        # 5. CÁLCULOS E EXIBIÇÃO
        # ==========================================
        if df_filtered.empty:
            st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados.")
        else:
            total_adultos = len(df_filtered)
            total_criancas = int(df_filtered['Qtd_Criancas'].sum())
            total_geral = total_adultos + total_criancas
            df_est_f = df_filtered[df_filtered['Estrangeiro'] == True]
            qtd_estrangeiros = df_est_f['Total_Visitantes_Linha'].sum()

            st.success(f"✅ Exibindo análise de {len(df_filtered)} registros.")
            
            # KPIs
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Público Total", f"{total_geral:,}".replace(',','.'))
            col2.metric("Adultos", f"{total_adultos:,}".replace(',','.'))
            col3.metric("Crianças", f"{total_criancas:,}".replace(',','.'))
            col4.metric("Estrangeiros", int(qtd_estrangeiros))
            st.markdown("---")

            # Gráficos
            sns.set_theme(style="whitegrid")
            fig = plt.figure(figsize=(22, 14))
            plt.subplots_adjust(hspace=0.4, wspace=0.3)
            plt.suptitle('Análise de Visitantes do Aquário Municipal', fontsize=18, fontweight='bold', y=0.98)
            
            # 1. Composição
            plt.subplot(2, 3, 1)
            plt.pie([total_adultos, total_criancas], labels=['Adultos', 'Crianças'], 
                    autopct='%1.1f%%', colors=['#3498db', '#f1c40f'], startangle=90, explode=(0.05, 0))
            plt.title('Distribuição Adultos vs Crianças', fontsize=14, fontweight='bold')

            # 2. Perfil Visitantes
            plt.subplot(2, 3, 2)
            contagem_grupo = df_filtered['Tipo_Grupo'].value_counts()
            if not contagem_grupo.empty:
                plt.pie(contagem_grupo, labels=contagem_grupo.index, autopct='%1.1f%%', 
                        colors=['#e74c3c', '#2ecc71'], startangle=90, wedgeprops={'alpha':0.8})
                plt.title('Perfil dos Visitantes', fontsize=14, fontweight='bold')

            # 3. Evolução Diária
            plt.subplot(2, 3, 3)
            evolucao = df_filtered.groupby('Data')['Total_Visitantes_Linha'].sum()
            evolucao.plot(kind='line', marker='o', color='#8e44ad', linewidth=2)
            plt.title('Evolução do Fluxo de Pessoas', fontsize=14, fontweight='bold')
            plt.xlabel('Data')
            plt.ylabel('Total de Visitantes')
            plt.xticks(rotation=45)

            # 4. Média por Dia da Semana
            plt.subplot(2, 3, 4)
            soma_dia = df_filtered.groupby('Dia_Semana')['Total_Visitantes_Linha'].sum()
            qtd_dias = df_filtered.groupby('Dia_Semana')['Data'].nunique()
            media = (soma_dia / qtd_dias).fillna(0)
            sns.barplot(x=media.index, y=media.values, palette="rocket")
            plt.title('Média de Visitantes por Dia da Semana', fontsize=14, fontweight='bold')
            plt.xlabel('Dia da Semana')
            plt.ylabel('Média de Visitantes')

            # 5. Top Cidades
            plt.subplot(2, 3, 5)
            top_cid = df_filtered['Cidade_Limpa'].value_counts().head(10)
            if not top_cid.empty:
                sns.barplot(x=top_cid.values, y=top_cid.index, palette="viridis")
                plt.title('Cidades de Origem (Top 10)', fontsize=14, fontweight='bold')
                plt.xlabel('Número de Visitantes')
                plt.ylabel('Cidade')

            # 6. Estrangeiros
            plt.subplot(2, 3, 6)
            if qtd_estrangeiros > 0:
                top_est = df_est_f['Cidade_Limpa'].value_counts().head(5)
                sns.barplot(x=top_est.values, y=top_est.index, palette="copper")
                plt.title('Origem dos Estrangeiros (Top 5)', fontsize=14, fontweight='bold')
                plt.xlabel('Número de Visitantes')
                plt.ylabel('País/Cidade')
            else:
                plt.text(0.5, 0.5, "Sem registros internacionais\nno período selecionado", 
                         ha='center', va='center', fontsize=12, color='gray')
                plt.axis('off')

            st.pyplot(fig)

    except Exception as e:
        st.error(f"Erro no processamento: {e}")

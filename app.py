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
        # Leitura
        if uploaded_file.name.endswith('.csv'):
            try:
                df = pd.read_csv(uploaded_file)
            except:
                df = pd.read_csv(uploaded_file, encoding='latin1', sep=';')
        else:
            df = pd.read_excel(uploaded_file)
            
        # Padronização
        df = df.iloc[:, 0:7]
        df.columns = ['Data_Hora', 'Nome', 'Cidade_Origem', 'Whatsapp', 'Idade', 'Qtd_Criancas', 'Obs']
        
        # Limpeza
        df['Cidade_Limpa'] = df['Cidade_Origem'].astype(str).str.strip().str.title()
        df.loc[df['Cidade_Limpa'].str.contains('Cuiab|Cba', case=False), 'Cidade_Limpa'] = 'Cuiabá'
        df.loc[df['Cidade_Limpa'].str.contains('Varzea|Várzea', case=False), 'Cidade_Limpa'] = 'Várzea Grande'
        df['Cidade_Limpa'] = df['Cidade_Limpa'].str.title()

        df['Data_Hora'] = pd.to_datetime(df['Data_Hora'], errors='coerce')
        df = df.dropna(subset=['Data_Hora'])
        df['Mes'] = df['Data_Hora'].dt.strftime('%Y-%m')
        
        # Tradução Dias
        df['Dia_Semana_Ingles'] = df['Data_Hora'].dt.strftime('%A')
        mapa_dias = {'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta', 'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}
        df['Dia_Semana'] = df['Dia_Semana_Ingles'].map(mapa_dias)
        ordem_dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        df['Dia_Semana'] = pd.Categorical(df['Dia_Semana'], categories=ordem_dias, ordered=True)

        # Lógica Crianças/Idade
        df['Idade'] = pd.to_numeric(df['Idade'], errors='coerce')
        df = df[(df['Idade'] > 0) & (df['Idade'] <= 100)]
        
        df['Qtd_Criancas'] = pd.to_numeric(df['Qtd_Criancas'], errors='coerce')
        limite_excursao = 40
        media_real = df.loc[df['Qtd_Criancas'] <= limite_excursao, 'Qtd_Criancas'].mean()
        if np.isnan(media_real): media_real = 0
        else: media_real = int(round(media_real))
        df['Qtd_Criancas'] = df['Qtd_Criancas'].fillna(0)
        df.loc[df['Qtd_Criancas'] > limite_excursao, 'Qtd_Criancas'] = media_real
        
        df['Total_Visitantes_Linha'] = 1 + df['Qtd_Criancas']
        df['Tipo_Grupo'] = df['Qtd_Criancas'].apply(lambda x: 'Família/Grupo' if x > 0 else 'Individual/Adultos')

        # Estrangeiros Blindado
        termos_estrangeiros = ['Argentina', 'Buenos Aires', 'Cordoba', 'Rosario', 'Bolivia', 'Bolívia', 'Santa Cruz de la Sierra', 'Cochabamba', 'La Paz', 'Paraguay', 'Paraguai', 'Asuncion', 'Assunção', 'Ciudad del Este', 'Uruguay', 'Uruguai', 'Montevideo', 'Montevidéu', 'Chile', 'Santiago', 'Valparaiso', 'Peru', 'Lima', 'Cusco', 'Colombia', 'Colômbia', 'Bogota', 'Venezuela', 'Equador', 'Usa', 'Eua', 'Estados Unidos', 'Miami', 'New York', 'Orlando', 'Portugal', 'Lisboa', 'Porto', 'Spain', 'Espanha', 'Madrid', 'Barcelona', 'France', 'França', 'Paris', 'Italy', 'Itália', 'Roma', 'Milano', 'Germany', 'Alemanha', 'Berlin', 'Uk', 'Reino Unido', 'London', 'Londres', 'China', 'Japan', 'Japão']
        termos_proibidos_brasil = ['Velho', 'Alegre', 'Oeste', 'Norte', 'Sul', 'Feliz', 'Seguro', 'Nacional', 'União', 'Rondonia', 'Rondônia', 'Ro', 'Rio Grande', 'Rs', 'Mato Grosso', 'Mt', 'Parana', 'Paraná', 'Pr', 'São Paulo', 'Sao Paulo', 'Sp', 'Minas', 'Mg', 'Bahia', 'Ba', 'Goias', 'Goiás', 'Go', 'Brasil', 'Brazil', 'Br']
        
        regex_estrangeiro = r'\b(' + '|'.join(termos_estrangeiros) + r')\b'
        regex_proibido = r'\b(' + '|'.join(termos_proibidos_brasil) + r')\b'
        parece_estrangeiro = df['Cidade_Limpa'].str.contains(regex_estrangeiro, case=False, regex=True)
        tem_termo_proibido = df['Cidade_Limpa'].str.contains(regex_proibido, case=False, regex=True)
        df['Estrangeiro'] = parece_estrangeiro & (~tem_termo_proibido)

        # KPIs
        total_adultos = len(df)
        total_criancas = int(df['Qtd_Criancas'].sum())
        total_geral = total_adultos + total_criancas
        df_estrangeiros = df[df['Estrangeiro'] == True]
        qtd_estrangeiros = df_estrangeiros['Total_Visitantes_Linha'].sum()

        st.success("✅ Análise Concluída!")
        
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Público Total", total_geral)
        col2.metric("Adultos", total_adultos)
        col3.metric("Crianças", total_criancas)
        col4.metric("Estrangeiros", int(qtd_estrangeiros))
        st.markdown("---")

        # Gráficos
        fig = plt.figure(figsize=(20, 12))
        
        plt.subplot(2, 3, 1)
        plt.pie([total_adultos, total_criancas], labels=['Adultos', 'Crianças'], autopct='%1.1f%%', colors=['#2980b9', '#f1c40f'], startangle=90)
        plt.title('Composição (Absoluto)')

        plt.subplot(2, 3, 2)
        contagem_grupo = df['Tipo_Grupo'].value_counts()
        plt.pie(contagem_grupo, labels=contagem_grupo.index, autopct='%1.1f%%', colors=['#e74c3c', '#27ae60'], startangle=90)
        plt.title('Perfil dos Grupos')

        plt.subplot(2, 3, 3)
        df.groupby('Mes')['Total_Visitantes_Linha'].sum().plot(marker='o', color='green')
        plt.title('Evolução Mensal')
        plt.grid(True, linestyle='--', alpha=0.5)

        plt.subplot(2, 3, 4)
        soma_dia = df.groupby('Dia_Semana')['Total_Visitantes_Linha'].sum()
        qtd_dias = df.groupby('Dia_Semana')['Data_Hora'].apply(lambda x: x.dt.date.nunique())
        media = soma_dia / qtd_dias
        sns.barplot(x=media.index, y=media.values, palette="Blues_d")
        plt.title('Média Diária (Operacional)')

        plt.subplot(2, 3, 5)
        top_cid = df['Cidade_Limpa'].value_counts().head(10)
        sns.barplot(x=top_cid.values, y=top_cid.index, palette="viridis")
        plt.title('Top 10 Cidades')

        plt.subplot(2, 3, 6)
        if qtd_estrangeiros > 0:
            top_est = df_estrangeiros['Cidade_Limpa'].value_counts().head(5)
            sns.barplot(x=top_est.values, y=top_est.index, palette="Oranges_r")
            plt.title('Top Estrangeiros')
        else:
            plt.text(0.5, 0.5, "Sem Estrangeiros", ha='center')

        st.pyplot(fig)

    except Exception as e:
        st.error(f"Erro no processamento: {e}")

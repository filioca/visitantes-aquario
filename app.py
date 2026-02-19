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
            
        # Padronização de Colunas
        df_raw = df_raw.iloc[:, 0:7]
        df_raw.columns = ['Data_Hora', 'Nome', 'Cidade_Origem', 'Whatsapp', 'Idade', 'Qtd_Criancas', 'Obs']
        
        # ==========================================
        # 2. LIMPEZA E TRATAMENTO (Calculado uma vez)
        # ==========================================
        df = df_raw.copy()
        
        # --- DATAS ---
        df['Data_Hora'] = pd.to_datetime(df['Data_Hora'], errors='coerce')
        df = df.dropna(subset=['Data_Hora'])
        df['Data'] = df['Data_Hora'].dt.date
        df['Mes'] = df['Data_Hora'].dt.strftime('%Y-%m')
        
        # Tradução Dias da Semana
        df['Dia_Semana_Ingles'] = df['Data_Hora'].dt.strftime('%A')
        mapa_dias = {'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta', 'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}
        df['Dia_Semana'] = df['Dia_Semana_Ingles'].map(mapa_dias)
        ordem_dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        df['Dia_Semana'] = pd.Categorical(df['Dia_Semana'], categories=ordem_dias, ordered=True)

        # --- IDADES & CRIANÇAS (Correção de Excursões) ---
        df['Idade'] = pd.to_numeric(df['Idade'], errors='coerce')
        df = df[(df['Idade'] > 0) & (df['Idade'] <= 100)]
        
        df['Qtd_Criancas'] = pd.to_numeric(df['Qtd_Criancas'], errors='coerce')
        limite_excursao = 40
        media_real = df.loc[df['Qtd_Criancas'] <= limite_excursao, 'Qtd_Criancas'].mean()
        if np.isnan(media_real): media_real = 0
        else: media_real = int(round(media_real))
        
        df['Qtd_Criancas'] = df['Qtd_Criancas'].fillna(0)
        df.loc[df['Qtd_Criancas'] > limite_excursao, 'Qtd_Criancas'] = media_real
        
        # Totais por Linha
        df['Total_Visitantes_Linha'] = 1 + df['Qtd_Criancas']
        df['Tipo_Grupo'] = df['Qtd_Criancas'].apply(lambda x: 'Família/Grupo' if x > 0 else 'Individual/Adultos')

        # ==========================================
        # 3. ESTRANGEIROS BLINDADO (V4 - FINAL)
        # ==========================================
        termos_estrangeiros = [
            'Argentina', 'Buenos Aires', 'Cordoba', 'Rosario',
            'Bolivia', 'Bolívia', 'Santa Cruz de la Sierra', 'Cochabamba', 'La Paz',
            'Paraguay', 'Paraguai', 'Asuncion', 'Assunção', 'Ciudad del Este',
            'Uruguay', 'Uruguai', 'Montevideo', 'Montevidéu',
            'Chile', 'Santiago', 'Valparaiso', 'Peru', 'Lima', 'Cusco',
            'Colombia', 'Colômbia', 'Bogota', 'Venezuela', 'Equador',
            'Usa', 'Eua', 'Estados Unidos', 'Miami', 'New York', 'Orlando',
            'Portugal', 'Lisboa', 'Porto', 'Spain', 'Espanha', 'Madrid', 'Barcelona',
            'France', 'França', 'Paris', 'Italy', 'Itália', 'Roma', 'Milano',
            'Germany', 'Alemanha', 'Berlin', 'Uk', 'Reino Unido', 'London', 'Londres',
            'China', 'Japan', 'Japão'
        ]
        
        # LISTA DE BLOQUEIO EXPANDIDA (Para evitar Alto Paraguai, Porto Estrela, etc)
        termos_proibidos_brasil = [
            'Alto', 'Baixo', 'Médio', 'Novo', 'Nova', 'Velho', 'Velha',
            'Alegre', 'Triste', 'Feliz', 'Seguro', 'Nacional', 'União',
            'Estrela', 'Gauchos', 'Gaúchos', 'Esperidião', 'Santa', 'Santo',
            'Norte', 'Sul', 'Leste', 'Oeste', 'Centro',
            'Rondonia', 'Rondônia', 'Ro', 'Acre', 'Ac', 'Amazonas', 'Am', 'Roraima', 'Rr',
            'Para', 'Pará', 'Pa', 'Amapa', 'Amapá', 'Ap', 'Tocantins', 'To',
            'Maranhao', 'Maranhão', 'Ma', 'Piaui', 'Piauí', 'Pi', 'Ceara', 'Ceará', 'Ce',
            'Rio Grande', 'Rn', 'Rs', 'Paraiba', 'Paraíba', 'Pb', 'Pernambuco', 'Pe',
            'Alagoas', 'Al', 'Sergipe', 'Se', 'Bahia', 'Ba', 'Minas', 'Gerais', 'Mg',
            'Espirito Santo', 'Es', 'Rio de Janeiro', 'Rj', 'Sao Paulo', 'São Paulo', 'Sp',
            'Parana', 'Paraná', 'Pr', 'Santa Catarina', 'Sc',
            'Mato Grosso', 'Mt', 'Ms', 'Goias', 'Goiás', 'Go', 'Df', 'Brasilia', 'Brasília',
            'Brasil', 'Brazil', 'Br'
        ]
        
        regex_estrangeiro = r'\b(' + '|'.join(termos_estrangeiros) + r')\b'
        regex_proibido = r'\b(' + '|'.join(termos_proibidos_brasil) + r')\b'
        
        parece_estrangeiro = df['Cidade_Limpa'].str.contains(regex_estrangeiro, case=False, regex=True)
        tem_termo_proibido = df['Cidade_Limpa'].str.contains(regex_proibido, case=False, regex=True)
        
        # Só é estrangeiro se parecer gringo E NÃO tiver termo proibido
        df['Estrangeiro'] = parece_estrangeiro & (~tem_termo_proibido)

        # ==========================================
        # 4. CÁLCULOS E EXIBIÇÃO
        # ==========================================
        total_adultos = len(df)
        total_criancas = int(df['Qtd_Criancas'].sum())
        total_geral = total_adultos + total_criancas
        df_estrangeiros = df[df['Estrangeiro'] == True]
        qtd_estrangeiros = df_estrangeiros['Total_Visitantes_Linha'].sum()

        st.success("✅ Análise Concluída!")
        
        # KPIs
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Público Total", total_geral)
        col2.metric("Adultos", total_adultos)
        col3.metric("Crianças", total_criancas)
        col4.metric("Estrangeiros", int(qtd_estrangeiros))
        st.markdown("---")

        # Gráficos
        fig = plt.figure(figsize=(20, 12))
        plt.style.use('seaborn-v0_8-darkgrid') # Estilo para os gráficos
        plt.suptitle('Análise de Visitantes do Aquário Municipal', fontsize=18, fontweight='bold', y=1.02)

        # 1. Composição
        plt.subplot(2, 3, 1)
        plt.pie([total_adultos, total_criancas], labels=['Adultos', 'Crianças'], 
                autopct='%1.1f%%', colors=['#3498db', '#f1c40f'], startangle=90, explode=(0.05, 0))
        plt.title('Distribuição Adultos vs Crianças', fontsize=14, fontweight='bold')

        # 2. Perfil Grupos
        plt.subplot(2, 3, 2)
        contagem_grupo = df_filtered['Tipo_Grupo'].value_counts()
        if not contagem_grupo.empty:
            plt.pie(contagem_grupo, labels=contagem_grupo.index, autopct='%1.1f%%', 
                    colors=['#e74c3c', '#2ecc71'], startangle=90, wedgeprops={'alpha':0.8})
            plt.title('Perfil dos Visitantes', fontsize=14, fontweight='bold')
        else:
            plt.text(0.5, 0.5, "Dados insuficientes para perfil de grupos", ha='center', va='center', fontsize=12, color='gray')
            plt.axis('off')

        # 3. Evolução Diária
        plt.subplot(2, 3, 3)
        evolucao = df_filtered.groupby('Data')['Total_Visitantes_Linha'].sum()
        evolucao.plot(kind='line', marker='o', color='#8e44ad', linewidth=2)
        plt.title('Evolução do Fluxo de Pessoas', fontsize=14, fontweight='bold')
        plt.xlabel('Data')
        plt.ylabel('Total de Visitantes')
        plt.xticks(rotation=45)
        plt.grid(True, linestyle='--', alpha=0.6)

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
        else:
            plt.text(0.5, 0.5, "Dados insuficientes para cidades de origem", ha='center', va='center', fontsize=12, color='gray')
            plt.axis('off')

        # 6. Detalhe Estrangeiros
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

        plt.tight_layout(rect=[0, 0.03, 1, 0.98]) # Ajusta layout para evitar sobreposição de títulos
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Erro no processamento: {e}")

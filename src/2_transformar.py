import os
import pandas as pd
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Configuração de conexão
caminho_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(caminho_env)

DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "root")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "transparencia")

senha_codificada = quote_plus(str(DB_PASS))
DATABASE_URI = f"mysql+mysqlconnector://{DB_USER}:{senha_codificada}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URI)

def processar_silver_viagem():
    # Limpa o cache de conexões para evitar transações presas
    engine.dispose()

    print("⏳ Lendo dados da raw_viagem...")
    df_raw = pd.read_sql("SELECT * FROM raw_viagem", engine)
    
    mapeamento = {
        'Identificador do processo de viagem': 'id_viagem',
        'Número da Proposta (PCDP)': 'num_proposta',
        'Situação': 'situacao',
        'Viagem Urgente': 'viagem_urgente',
        'Código do órgão superior': 'cod_orgao_superior',
        'Nome do órgão superior': 'nome_orgao_superior',
        'Nome': 'nome_viajante',
        'Cargo': 'cargo',
        'Período - Data de início': 'data_inicio',
        'Período - Data de fim': 'data_fim',
        'Destinos': 'destinos',
        'Motivo': 'motivo',
        'Valor diárias': 'valor_diarias',
        'Valor passagens': 'valor_passagens',
        'Valor devolução': 'valor_devolucao',
        'Valor outros gastos': 'valor_outros_gastos'
    }
    
    # Renomear colunas
    df_silver = df_raw.rename(columns=mapeamento)
    
    # 1. Remove nulos obrigatórios e duplicatas de ID
    df_silver = df_silver.dropna(subset=['id_viagem', 'nome_orgao_superior'])
    df_silver = df_silver.drop_duplicates(subset=['id_viagem'], keep='first')
    
    # 2. Conversão de datas
    df_silver['data_inicio'] = pd.to_datetime(df_silver['data_inicio'], format='%d/%m/%Y', errors='coerce')
    df_silver['data_fim'] = pd.to_datetime(df_silver['data_fim'], format='%d/%m/%Y', errors='coerce')
    
    # 3. Conversão monetária e garantia de valor >= 0
    cols_monetarias = ['valor_diarias', 'valor_passagens', 'valor_devolucao', 'valor_outros_gastos']
    for col in cols_monetarias:
        df_silver[col] = pd.to_numeric(
            df_silver[col].astype(str).str.replace(',', '.', regex=False), 
            errors='coerce'
        ).fillna(0.0).clip(lower=0)

    # 4. Cálculos
    df_silver['duracao_dias'] = (df_silver['data_fim'] - df_silver['data_inicio']).dt.days.fillna(0).astype(int)
    df_silver['valor_total'] = df_silver[cols_monetarias].sum(axis=1)

    # 5. FILTRO DE COLUNAS: Garante que apenas as colunas da Silver sejam enviadas para o SQL
    colunas_finais = list(mapeamento.values()) + ['duracao_dias', 'valor_total']
    df_silver = df_silver[colunas_finais]

    print("🚀 Limpando registros antigos e gravando em lotes na tabela silver_viagem...")
    
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM silver_viagem"))
        # O parâmetro chunksize=5000 divide as 340k linhas em lotes seguros, evitando queda de conexão
        df_silver.to_sql('silver_viagem', conn, if_exists='append', index=False, chunksize=5000)
        
    print("🎯 SUCESSO! Tabela 'silver_viagem' carregada perfeitamente.")

if __name__ == "__main__":
    processar_silver_viagem()
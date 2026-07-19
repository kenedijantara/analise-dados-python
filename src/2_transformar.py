import os
import pandas as pd
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

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
    engine.dispose()
    if not inspect(engine).has_table('raw_viagem'):
        print("⚠️ Tabela 'raw_viagem' não encontrada no banco. Pulando...\n")
        return

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
    
    df_silver = df_raw.rename(columns=mapeamento)
    df_silver = df_silver.dropna(subset=['id_viagem', 'nome_orgao_superior'])
    df_silver = df_silver.drop_duplicates(subset=['id_viagem'], keep='first')
    
    df_silver['data_inicio'] = pd.to_datetime(df_silver['data_inicio'], format='%d/%m/%Y', errors='coerce')
    df_silver['data_fim'] = pd.to_datetime(df_silver['data_fim'], format='%d/%m/%Y', errors='coerce')
    
    cols_monetarias = ['valor_diarias', 'valor_passagens', 'valor_devolucao', 'valor_outros_gastos']
    for col in cols_monetarias:
        df_silver[col] = pd.to_numeric(
            df_silver[col].astype(str).str.replace(',', '.', regex=False), 
            errors='coerce'
        ).fillna(0.0).clip(lower=0)

    df_silver['duracao_dias'] = (df_silver['data_fim'] - df_silver['data_inicio']).dt.days.fillna(0).astype(int)
    df_silver['valor_total'] = df_silver[cols_monetarias].sum(axis=1)

    colunas_finais = list(mapeamento.values()) + ['duracao_dias', 'valor_total']
    df_silver = df_silver[colunas_finais]

    print("🚀 Limpando registros antigos e gravando em lotes na tabela silver_viagem...")
    with engine.begin() as conn:
        if inspect(engine).has_table('silver_viagem'):
            conn.execute(text("DELETE FROM silver_viagem"))
        df_silver.to_sql('silver_viagem', conn, if_exists='append', index=False, chunksize=5000)
        
    print("🎯 SUCESSO! Tabela 'silver_viagem' carregada perfeitamente.\n")

def processar_silver_pagamento():
    engine.dispose()
    if not inspect(engine).has_table('raw_pagamento'):
        print("⚠️ Tabela 'raw_pagamento' não encontrada no banco. Pulando...\n")
        return

    print("⏳ Lendo dados da raw_pagamento...")
    df_raw = pd.read_sql("SELECT * FROM raw_pagamento", engine)
    
    mapeamento = {
        'Identificador do processo de viagem': 'id_viagem',
        'Tipo de pagamento': 'tipo_pagamento',
        'Valor': 'valor'
    }
    
    df_silver = df_raw.rename(columns=mapeamento)
    df_silver = df_silver.dropna(subset=['id_viagem', 'valor'])
    df_silver['id_viagem'] = pd.to_numeric(df_silver['id_viagem'], errors='coerce')
    df_silver = df_silver.dropna(subset=['id_viagem'])
    df_silver['id_viagem'] = df_silver['id_viagem'].astype(int)
    
    df_silver['valor'] = pd.to_numeric(
        df_silver['valor'].astype(str).str.replace(',', '.', regex=False), 
        errors='coerce'
    ).fillna(0.0).clip(lower=0)
    
    colunas_finais = [c for c in list(mapeamento.values()) if c in df_silver.columns]
    df_silver = df_silver[colunas_finais]
    
    print("🚀 Limpando registros antigos e gravando em lotes na tabela silver_pagamento...")
    with engine.begin() as conn:
        if inspect(engine).has_table('silver_pagamento'):
            conn.execute(text("DELETE FROM silver_pagamento"))
        df_silver.to_sql('silver_pagamento', conn, if_exists='append', index=False, chunksize=5000)
        
    print("🎯 SUCESSO! Tabela 'silver_pagamento' carregada perfeitamente.\n")

def processar_silver_trecho():
    engine.dispose()
    if not inspect(engine).has_table('raw_trecho'):
        print("⚠️ Tabela 'raw_trecho' não encontrada no banco. Pulando...\n")
        return

    print("⏳ Lendo dados da raw_trecho...")
    df_raw = pd.read_sql("SELECT * FROM raw_trecho", engine)
    
    mapeamento = {
        'Identificador do processo de viagem': 'id_viagem',
        'Origem - Cidade': 'origem',
        'Destino - Cidade': 'destino',
        'Destino - UF': 'uf_destino',
        'Meio de transporte': 'meio_transporte'
    }
    
    df_silver = df_raw.rename(columns=mapeamento)
    df_silver = df_silver.dropna(subset=['id_viagem'])
    df_silver['id_viagem'] = pd.to_numeric(df_silver['id_viagem'], errors='coerce')
    df_silver = df_silver.dropna(subset=['id_viagem'])
    df_silver['id_viagem'] = df_silver['id_viagem'].astype(int)
    
    colunas_finais = [c for c in list(mapeamento.values()) if c in df_silver.columns]
    df_silver = df_silver[colunas_finais]
    
    print("🚀 Limpando registros antigos e gravando em lotes na tabela silver_trecho...")
    with engine.begin() as conn:
        if inspect(engine).has_table('silver_trecho'):
            conn.execute(text("DELETE FROM silver_trecho"))
        df_silver.to_sql('silver_trecho', conn, if_exists='append', index=False, chunksize=5000)
        
    print("🎯 SUCESSO! Tabela 'silver_trecho' carregada perfeitamente.\n")

def processar_silver_passagem():
    engine.dispose()
    if not inspect(engine).has_table('raw_passagem'):
        print("⚠️ Tabela 'raw_passagem' não encontrada no banco. Pulando...\n")
        return

    print("⏳ Lendo dados da raw_passagem...")
    df_raw = pd.read_sql("SELECT * FROM raw_passagem", engine)
    
    mapeamento = {
        'Identificador do processo de viagem': 'id_viagem',
        'Valor': 'valor_passagem',
        'Valor da passagem': 'valor_passagem'
    }
    
    df_silver = df_raw.rename(columns=mapeamento)
    df_silver = df_silver.dropna(subset=['id_viagem'])
    df_silver['id_viagem'] = pd.to_numeric(df_silver['id_viagem'], errors='coerce')
    df_silver = df_silver.dropna(subset=['id_viagem'])
    df_silver['id_viagem'] = df_silver['id_viagem'].astype(int)
    
    if 'valor_passagem' in df_silver.columns:
        df_silver['valor_passagem'] = pd.to_numeric(
            df_silver['valor_passagem'].astype(str).str.replace(',', '.', regex=False), 
            errors='coerce'
        ).fillna(0.0).clip(lower=0)
    else:
        df_silver['valor_passagem'] = 0.0
        
    colunas_finais = [c for c in ['id_viagem', 'valor_passagem'] if c in df_silver.columns]
    df_silver = df_silver[colunas_finais]
    
    print("🚀 Limpando registros antigos e gravando em lotes na tabela silver_passagem...")
    with engine.begin() as conn:
        if inspect(engine).has_table('silver_passagem'):
            conn.execute(text("DELETE FROM silver_passagem"))
        df_silver.to_sql('silver_passagem', conn, if_exists='append', index=False, chunksize=5000)
        
    print("🎯 SUCESSO! Tabela 'silver_passagem' carregada perfeitamente.\n")

if __name__ == "__main__":
    print("🚀 Iniciando processamento da Camada Silver a partir das tabelas Raw...\n")
    try:
        processar_silver_viagem()
        processar_silver_pagamento()
        processar_silver_trecho()
        processar_silver_passagem()
        print("🏁 Processamento concluído!")
    finally:
        engine.dispose()
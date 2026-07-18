import os
import time
import pandas as pd
from urllib.parse import quote_plus  # <--- Biblioteca nativa para codificar senhas
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Carrega as variáveis do arquivo .env
load_dotenv()

# =====================================================================
# CONFIGURAÇÕES DE CONEXÃO COM O BANCO DE DADOS
# =====================================================================
# IMPORTANTE: Verifique se os nomes abaixo (DB_USER, DB_PASS, etc.) 
# são idênticos aos que estão escritos dentro do seu arquivo .env!
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "root")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "transparencia")

# Codifica a senha para evitar que caracteres especiais (@, #, !, %, etc.) quebrem a conexão
senha_codificada = quote_plus(DB_PASS)

# Conexão via SQLAlchemy usando o driver mysql-connector-python e a senha protegida
DATABASE_URI = f"mysql+mysqlconnector://{DB_USER}:{senha_codificada}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URI)

# =====================================================================
# PARÂMETROS DO PIPELINE
# =====================================================================
# Tamanho do lote ajustado para não sobrecarregar a memória do notebook
TAMANHO_LOTE = 50000  

# Mapeamento: Arquivo CSV de origem -> Tabela de destino na camada RAW
ARQUIVOS_PARA_PROCESSAR = [
    ("dados/2025_Viagem.csv", "raw_viagem"),
    ("dados/2025_Passagem.csv", "raw_passagem"),
    ("dados/2025_Trecho.csv", "raw_trecho"),
    ("dados/2025_Pagamento.csv", "raw_pagamento")
]

# =====================================================================
# FUNÇÃO DE EXTRAÇÃO E CARGA EM LOTES (CHUNKS)
# =====================================================================
def carregar_csv_para_mysql(caminho_arquivo, nome_tabela, engine_db, chunk_size):
    if not os.path.exists(caminho_arquivo):
        print(f"❌ ERRO: O arquivo '{caminho_arquivo}' não foi encontrado! Verifique se está na pasta 'dados/'.")
        return

    print(f"⏳ Lendo arquivo em lotes de {chunk_size} registros...")
    inicio_tempo = time.time()
    total_linhas = 0
    lote_num = 1

    try:
        # Portal da Transparência: separador ponto e vírgula (;), codificação latin1/iso-8859-1
        # dtype=str garante que códigos e números não percam formatação na camada Raw
        leitor_csv = pd.read_csv(
            caminho_arquivo,
            sep=';',
            encoding='latin1',
            chunksize=chunk_size,
            dtype=str,
            low_memory=False
        )

        for lote in leitor_csv:
            # if_exists='append' é OBRIGATÓRIO para não deletar a tabela e perder as PKs/FKs criadas no banco
            lote.to_sql(
                name=nome_tabela,
                con=engine_db,
                if_exists='append',
                index=False
            )
            
            linhas_lote = len(lote)
            total_linhas += linhas_lote
            print(f"   ✔ Lote {lote_num} gravado em '{nome_tabela}': +{linhas_lote} linhas (Total acumulado: {total_linhas})")
            lote_num += 1

        tempo_gasto = round(time.time() - inicio_tempo, 2)
        print(f"🎯 Sucesso! Tabela '{nome_tabela}' recebeu {total_linhas} registros em {tempo_gasto} segundos.")

    except SQLAlchemyError as err_db:
        print(f"❌ Erro de Banco de Dados ao tentar gravar em '{nome_tabela}':\n{err_db}")
    except Exception as err_geral:
        print(f"❌ Erro inesperado ao processar o arquivo '{caminho_arquivo}':\n{err_geral}")

# =====================================================================
# BLOCO DE EXECUÇÃO PRINCIPAL
# =====================================================================
if __name__ == "__main__":
    print("🚀 Iniciando Pipeline de Extração - Camada Raw (Medallion)")
    print("------------------------------------------------------------")
    print("--- INICIANDO PIPELINE DE EXTRAÇÃO (CAMADA RAW) ---")
    
    for caminho, tabela in ARQUIVOS_PARA_PROCESSAR:
        print(f"\nProcessando: {caminho} -> Destino: {tabela}")
        carregar_csv_para_mysql(caminho, tabela, engine, TAMANHO_LOTE)
        
    print("\n--- EXTRAÇÃO CONCLÚIDA COM SUCESSO! ---")
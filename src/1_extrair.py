import os
import time
import pandas as pd
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "root")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "transparencia")

senha_codificada = quote_plus(DB_PASS)

DATABASE_URI = (
    f"mysql+mysqlconnector://"
    f"{DB_USER}:{senha_codificada}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URI)

TAMANHO_LOTE = 50000

ARQUIVOS_PARA_PROCESSAR = [
    ("dados/2025_Viagem.csv", "raw_viagem"),
    ("dados/2025_Passagem.csv", "raw_passagem"),
    ("dados/2025_Trecho.csv", "raw_trecho"),
    ("dados/2025_Pagamento.csv", "raw_pagamento"),
]


def carregar_csv_para_mysql(caminho_arquivo, nome_tabela, engine_db, chunk_size):

    if not os.path.exists(caminho_arquivo):
        print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
        return

    print(f"⏳ Processando {caminho_arquivo}...")

    inicio = time.time()

    total = 0
    lote_num = 1

    try:

        leitor = pd.read_csv(
            caminho_arquivo,
            sep=";",
            encoding="latin1",
            dtype=str,
            chunksize=chunk_size,
            low_memory=False
        )

        for lote in leitor:

            lote.columns = (
                lote.columns
                .str.replace('"', '', regex=False)
                .str.replace("\ufeff", "", regex=False)
                .str.replace("\xa0", " ", regex=False)
                .str.strip()
            )

            lote.to_sql(
                name=nome_tabela,
                con=engine_db,
                if_exists="append",
                index=False
            )

            linhas = len(lote)
            total += linhas

            print(
                f"✔ Lote {lote_num} gravado "
                f"({linhas} linhas - total {total})"
            )

            lote_num += 1

            tempo = round(time.time() - inicio, 2)

        print(
            f"🎯 Sucesso! Tabela '{nome_tabela}' recebeu "
            f"{total} registros em {tempo} segundos."
        )

    except SQLAlchemyError as err_db:
        print(f"\n❌ Erro ao gravar na tabela '{nome_tabela}':")
        print(err_db)

    except Exception as err:
        print(f"\n❌ Erro ao processar '{caminho_arquivo}':")
        print(err)


if __name__ == "__main__":

    print("🚀 Iniciando Pipeline de Extração (Camada Raw)")
    print("-" * 60)

    for caminho, tabela in ARQUIVOS_PARA_PROCESSAR:

        print(f"\nArquivo: {caminho}")
        print(f"Tabela: {tabela}")

        carregar_csv_para_mysql(
            caminho_arquivo=caminho,
            nome_tabela=tabela,
            engine_db=engine,
            chunk_size=TAMANHO_LOTE
        )

    print("\n🏁 Extração finalizada!")

    engine.dispose()
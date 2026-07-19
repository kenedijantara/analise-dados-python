import os
import pandas as pd
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

engine = create_engine(
    f"mysql+mysqlconnector://{DB_USER}:{quote_plus(DB_PASS)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


def salvar_tabela(nome_tabela, consulta):
    df = pd.read_sql(consulta, engine)
    df.to_sql(nome_tabela, engine, if_exists="replace", index=False)

    print("\n" + "=" * 80)
    print(nome_tabela.upper())
    print("=" * 80)
    print(df)
    print()


consulta1 = """
SELECT
    nome_orgao_superior,
    ROUND(SUM(valor_total),2) AS custo_total
FROM silver_viagem
GROUP BY nome_orgao_superior
ORDER BY custo_total DESC
LIMIT 5;
"""

consulta2 = """
SELECT
    t.destino,
    ROUND(AVG(v.valor_total),2) AS custo_medio
FROM silver_viagem v
INNER JOIN silver_trecho t
ON v.id_viagem = t.id_viagem
GROUP BY t.destino
ORDER BY custo_medio DESC
LIMIT 3;
"""

consulta3 = """
SELECT
    id_viagem,
    nome_viajante,
    nome_orgao_superior,
    duracao_dias,
    valor_total
FROM silver_viagem
ORDER BY duracao_dias DESC
LIMIT 1;
"""
consulta4 = """
SELECT
    tipo_pagamento,
    ROUND(AVG(valor),2) AS valor_medio
FROM silver_pagamento
GROUP BY tipo_pagamento
ORDER BY valor_medio DESC
LIMIT 1;
"""

consulta5 = """
SELECT
    meio_transporte,
    COUNT(*) AS quantidade
FROM silver_trecho
GROUP BY meio_transporte
ORDER BY quantidade DESC
LIMIT 1;
"""

consulta6 = """
SELECT
    uf_destino,
    COUNT(*) AS quantidade
FROM silver_trecho
GROUP BY uf_destino
ORDER BY quantidade DESC
LIMIT 1;
"""

consulta7 = """
SELECT
    nome_orgao_superior,
    ROUND(SUM(valor_total),2) AS total_pago
FROM silver_viagem
GROUP BY nome_orgao_superior
ORDER BY total_pago DESC
LIMIT 1;
"""


if __name__ == "__main__":

    print("\nINICIANDO CAMADA GOLD\n")

    salvar_tabela("gold_top5_orgaos", consulta1)

    salvar_tabela("gold_top3_destinos", consulta2)

    salvar_tabela("gold_maior_viagem", consulta3)

    salvar_tabela("gold_tipo_pagamento", consulta4)

    salvar_tabela("gold_meio_transporte", consulta5)

    salvar_tabela("gold_uf_destino", consulta6)

    salvar_tabela("gold_orgao_maior_gasto", consulta7)

    engine.dispose()

    print("=" * 80)
    print("CAMADA GOLD CONCLUÍDA COM SUCESSO!")
    print("=" * 80)
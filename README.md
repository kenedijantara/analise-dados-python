# Análise de Dados de Viagens a Serviço

Projeto desenvolvido para a disciplina de Análise de Dados utilizando Python, MySQL e a Arquitetura Medallion (Raw, Silver e Gold).

## Objetivo

Construir um pipeline de ETL para processar dados públicos de viagens a serviço do Governo Federal e responder perguntas de negócio por meio de consultas e análises.

## Tecnologias utilizadas

- Python
- Pandas
- SQLAlchemy
- MySQL
- Jupyter Notebook
- Git e GitHub

## Estrutura do projeto

```
analise-dados-python/
│
├── dados/
├── notebooks/
│   └── analise.ipynb
├── sql/
│   └── 0_criar_banco.sql
├── src/
│   ├── 1_extrair.py
│   ├── 2_transformar.py
│   └── 3_gold.py
├── .env
├── requirements.txt
└── README.md
```

## Arquitetura Medallion

### Camada Raw

Realiza a extração dos arquivos CSV e o carregamento das tabelas no MySQL sem alterações nos dados.

### Camada Silver

Realiza limpeza, padronização, tratamento de datas, conversão de valores monetários, remoção de duplicidades e criação de colunas derivadas.

### Camada Gold

Gera tabelas analíticas para responder às perguntas de negócio propostas.

## Perguntas respondidas

- Top 5 órgãos com maior custo total.
- Top 3 destinos com maior custo médio por viagem.
- Viagem de maior duração e seu custo total.
- Tipo de pagamento com maior valor médio.
- Meio de transporte mais utilizado.
- UF de destino com maior número de trechos.
- Órgão com maior gasto total.

## Como executar

1. Criar o banco de dados utilizando:

```
sql/0_criar_banco.sql
```

2. Configurar o arquivo `.env`.

3. Executar a camada Raw:

```
python src/1_extrair.py
```

4. Executar a camada Silver:

```
python src/2_transformar.py
```

5. Executar a camada Gold:

```
python src/3_gold.py
```

6. Abrir o notebook:

```
notebooks/analise.ipynb
```

## Autor

Kenedi Nazário Jantara
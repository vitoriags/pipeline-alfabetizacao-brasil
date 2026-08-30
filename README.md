# Pipeline de Alfabetização no Brasil

Projeto desenvolvido para o Tech Challenge — Fase 2 da pós-graduação em AI Scientist.

## Pipeline Bronze

A primeira etapa da pipeline realiza a ingestão dos arquivos brutos da pasta `data/raw` e salva os dados em formato Parquet na pasta `data/bronze`.

Nesta camada, os dados são mantidos próximos da fonte original. As únicas alterações adicionadas são metadados de ingestão, como:

- `data_ingestao`: data e hora em que o arquivo foi processado;
- `arquivo_origem`: nome do arquivo original utilizado na ingestão.

Para executar a etapa Bronze:

```bash
python src/ingest_bronze.py

## Pipeline Silver

A etapa Silver realiza a padronização das tabelas geradas na camada Bronze e cria um relatório simples de qualidade dos dados.

Nesta camada foram aplicadas transformações como:

- padronização de tipos de dados;
- renomeação de colunas para deixar o significado mais claro;
- preservação dos códigos de `rede` e `serie` quando o dicionário oficial não estava disponível;
- validação de duplicidades nas chaves principais;
- validação de percentuais no intervalo de 0 a 100.

O relatório de qualidade é salvo em:

```bash
data/silver/quality_report_silver.csv
```

Para executar a etapa Silver:

```bash
python src/transform_silver.py
```
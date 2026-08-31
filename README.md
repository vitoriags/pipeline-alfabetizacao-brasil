# Pipeline de Alfabetização no Brasil

Projeto desenvolvido para o Tech Challenge — Fase 2 da pós-graduação em AI Scientist.

O objetivo do projeto é construir uma pipeline de dados para análise da alfabetização no Brasil, utilizando dados oficiais em camadas Bronze, Silver e Gold.

## Escopo do projeto

As tabelas escolhidas para o MVP são:

- `uf`: resultados observados da alfabetização por unidade da federação e rede de ensino;
- `meta_alfabetizacao_uf`: metas de alfabetização por UF até 2030;
- `meta_alfabetizacao_brasil`: metas e resultado consolidado em nível nacional.

Essa escolha permite analisar a situação da alfabetização no Brasil a partir de três pontos:

- resultado observado;
- distância em relação às metas;
- comparação com o cenário nacional.

## Estrutura do projeto

```bash
data/
├── raw/
├── bronze/
├── silver/
└── gold/

notebooks/
└── 01_exploracao_base_alfabetizacao.ipynb

src/
├── ingest_bronze.py
└── transform_silver.py
```

## Pipeline Bronze

A primeira etapa da pipeline realiza a ingestão dos arquivos brutos da pasta `data/raw` e salva os dados em formato Parquet na pasta `data/bronze`.

Nesta camada, os dados são mantidos próximos da fonte original. As únicas alterações adicionadas são metadados de ingestão:

- `data_ingestao`: data e hora em que o arquivo foi processado;
- `arquivo_origem`: nome do arquivo original utilizado na ingestão.

Para executar a etapa Bronze:

```bash
python src/ingest_bronze.py
```

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

## Observações

Os arquivos de dados brutos e os arquivos gerados nas camadas Bronze, Silver e Gold não são versionados no GitHub, seguindo boas práticas para projetos de dados.

A coluna `rede` possui dicionário oficial indicado pela Base dos Dados, mas a tabela de tradução não pôde ser acessada via download manual. Por isso, nesta versão do projeto, os códigos da tabela `uf` foram preservados sem tradução.
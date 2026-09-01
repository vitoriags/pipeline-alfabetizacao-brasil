# Documentação Técnica

## Visão geral

Este documento complementa o README do projeto e descreve, de forma mais técnica, a implementação da pipeline de dados para análise da alfabetização no Brasil.

A solução foi construída com foco em um MVP funcional, utilizando dados oficiais da Base dos Dados relacionados à Avaliação da Alfabetização. A pipeline segue a arquitetura Medalhão, com camadas Bronze, Silver e Gold, além de uma simulação de streaming e monitoramento da execução.

## Fontes de dados

As tabelas utilizadas foram:

- `uf`
- `meta_alfabetizacao_uf`
- `meta_alfabetizacao_brasil`

Os arquivos foram baixados manualmente em formato CSV compactado e armazenados localmente na pasta `data/raw`.

Arquivos esperados:

```bash
data/raw/br_inep_avaliacao_alfabetizacao_uf.csv.gz
data/raw/br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_uf.csv.gz
data/raw/br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_brasil.csv.gz
```

Esses arquivos não são versionados no GitHub.

## Estrutura lógica da pipeline

```bash
data/raw
   ↓
data/bronze
   ↓
data/silver
   ↓
data/gold
   ↓
data/streaming e data/monitoring
   ↓
AWS S3
   ↓
Amazon Athena
```

## Camada Bronze

Arquivo responsável:

```bash
src/ingest_bronze.py
```

A camada Bronze realiza a ingestão dos arquivos brutos da pasta `data/raw` e salva as tabelas em formato Parquet na pasta `data/bronze`.

Nesta etapa, os dados são mantidos próximos da fonte original. As únicas colunas adicionadas são metadados de ingestão:

- `data_ingestao`
- `arquivo_origem`

Saídas geradas:

```bash
data/bronze/uf.parquet
data/bronze/meta_alfabetizacao_uf.parquet
data/bronze/meta_alfabetizacao_brasil.parquet
```

## Camada Silver

Arquivo responsável:

```bash
src/transform_silver.py
```

A camada Silver lê os arquivos Parquet da Bronze, padroniza algumas colunas e gera uma versão mais organizada dos dados.

Principais tratamentos aplicados:

- padronização de tipos de dados;
- padronização de `sigla_uf`;
- renomeação de `serie` para `serie_codigo`;
- renomeação de `rede` para `rede_codigo` na tabela `uf`;
- renomeação de `rede` para `rede_descricao` nas tabelas de metas;
- preservação dos códigos de `rede` quando o dicionário oficial não estava disponível.

Saídas geradas:

```bash
data/silver/uf.parquet
data/silver/meta_alfabetizacao_uf.parquet
data/silver/meta_alfabetizacao_brasil.parquet
data/silver/quality_report_silver.csv
```

## Regras de qualidade

As validações de qualidade foram aplicadas na camada Silver.

Regras implementadas:

| Regra | Descrição |
|---|---|
| `duplicidade_chave` | Verifica se existem registros duplicados nas chaves principais de cada tabela |
| `percentual_entre_0_e_100` | Verifica se taxas, metas e percentuais estão dentro do intervalo esperado de 0 a 100 |

Chaves consideradas:

| Tabela | Chave |
|---|---|
| `uf` | `ano`, `sigla_uf`, `serie_codigo`, `rede_codigo` |
| `meta_alfabetizacao_uf` | `ano`, `sigla_uf`, `rede_descricao` |
| `meta_alfabetizacao_brasil` | `ano`, `rede_descricao` |

O resultado das validações é salvo em:

```bash
data/silver/quality_report_silver.csv
```

Na execução testada, as regras retornaram status `ok`.

## Camada Gold

Arquivo responsável:

```bash
src/transform_gold.py
```

A camada Gold gera tabelas analíticas finais, voltadas para análise e consumo em ferramentas SQL ou BI.

Saídas geradas:

```bash
data/gold/indicadores_alfabetizacao_uf.parquet
data/gold/comparativo_metas_uf_brasil.parquet
```

### Tabela `indicadores_alfabetizacao_uf`

Essa tabela utiliza a base `uf` da camada Silver e calcula a distância da média de português em relação ao ponto de corte de 743 pontos.

Principais campos:

- `ano`
- `sigla_uf`
- `serie_codigo`
- `rede_codigo`
- `taxa_alfabetizacao`
- `media_portugues`
- `distancia_ponto_corte`
- `status_ponto_corte`

O campo `status_ponto_corte` classifica os registros como:

- `abaixo_do_ponto_corte`
- `acima_ou_igual_ao_ponto_corte`

### Tabela `comparativo_metas_uf_brasil`

Essa tabela utiliza as bases `meta_alfabetizacao_uf` e `meta_alfabetizacao_brasil` da camada Silver.

Ela calcula:

- meta de referência do ano;
- distância da taxa observada para a meta da UF;
- status da UF em relação à meta;
- diferença entre taxa da UF e taxa nacional.

Principais campos:

- `ano`
- `sigla_uf`
- `rede_descricao`
- `taxa_alfabetizacao`
- `meta_referencia_ano`
- `distancia_para_meta_uf`
- `status_meta_uf`
- `taxa_alfabetizacao_brasil`
- `meta_referencia_brasil`
- `diferenca_taxa_uf_brasil`
- `percentual_participacao`
- `percentual_participacao_brasil`

## Streaming e monitoramento

Arquivo responsável:

```bash
src/simulate_streaming_monitoring.py
```

Como os dados oficiais de alfabetização são publicados de forma periódica, a ingestão principal foi implementada em batch.

Para representar a parte streaming, foi criada uma simulação de eventos operacionais da pipeline em formato JSONL.

Eventos gerados:

- `bronze_ingestion_completed`
- `silver_transformation_completed`
- `quality_validation_completed`
- `gold_table_updated`
- `pipeline_run_completed`

Saída streaming:

```bash
data/streaming/pipeline_events.jsonl
```

Além disso, os eventos são convertidos em um log tabular de monitoramento.

Saída de monitoramento:

```bash
data/monitoring/pipeline_monitoring_log.csv
```

O log contém informações como:

- `event_id`
- `event_timestamp`
- `event_type`
- `stage`
- `status`
- `table`
- `records_processed`
- `total_rules`
- `rules_with_error`

## Implementação em cloud

A implementação em cloud foi feita na AWS.

Serviços utilizados:

| Serviço | Uso |
|---|---|
| Amazon S3 | Armazenamento das camadas da pipeline |
| Amazon Athena | Consulta SQL das tabelas Gold em Parquet |

As camadas foram enviadas para o bucket S3:

```bash
s3://pipeline-alfabetizacao-brasil-vitoria-20260830/
```

Organização no S3:

```bash
raw/
bronze/
silver/
gold/
streaming/
monitoring/
athena-results/
```

As tabelas Gold foram organizadas em pastas específicas para facilitar a criação de tabelas externas no Athena:

```bash
s3://pipeline-alfabetizacao-brasil-vitoria-20260830/gold/indicadores_alfabetizacao_uf/
s3://pipeline-alfabetizacao-brasil-vitoria-20260830/gold/comparativo_metas_uf_brasil/
```

## Athena

Arquivo SQL responsável:

```bash
sql/create_athena_tables.sql
```

No Athena, foi criado o banco:

```sql
alfabetizacao_brasil
```

E duas tabelas externas:

```sql
alfabetizacao_brasil.indicadores_alfabetizacao_uf
alfabetizacao_brasil.comparativo_metas_uf_brasil
```

As tabelas externas apontam para os arquivos Parquet da camada Gold armazenados no S3.

## FinOps

O controle de custos foi feito principalmente por decisões arquiteturais.

Decisões adotadas:

- uso de S3 como armazenamento principal;
- uso de Parquet para reduzir volume de dados lidos em consultas;
- uso do Athena apenas para consulta das tabelas Gold;
- ausência de recursos persistentes, como EC2, EMR ou clusters sempre ligados;
- baixo volume de dados no MVP;
- bucket privado;
- versionamento do bucket desativado;
- organização das tabelas Gold em pastas separadas.

A escolha por S3 + Athena reduz a necessidade de manter infraestrutura ativa continuamente, o que é adequado para o ambiente AWS Academy e para o escopo do projeto.

## Limitações técnicas

Algumas limitações foram assumidas nesta versão:

- a tabela de tradução oficial da coluna `rede` não pôde ser acessada via download manual;
- por isso, os códigos de `rede` da tabela `uf` foram preservados sem tradução;
- a parte streaming foi implementada como simulação de eventos operacionais, e não com ferramenta real como Kafka ou Kinesis;
- as tabelas municipais e de alunos não foram usadas no MVP para evitar aumento de volume, custo e complexidade;
- não foi implementado modelo de machine learning nesta fase, apenas a preparação da camada Gold para possíveis aplicações futuras.

## Como executar localmente

Criar e ativar o ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instalar dependências:

```bash
pip install -r requirements.txt
```

Executar a pipeline completa:

```bash
python src/ingest_bronze.py
python src/transform_silver.py
python src/transform_gold.py
python src/simulate_streaming_monitoring.py
```

## Versionamento

O projeto foi versionado com Git e GitHub, utilizando branches separadas por etapa e Pull Requests para integração na branch principal.

Etapas versionadas:

- configuração inicial;
- exploração dos dados;
- pipeline Bronze;
- pipeline Silver e qualidade;
- pipeline Gold;
- streaming e monitoramento;
- documentação AWS, Athena e FinOps;
- documentação final.
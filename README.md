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

As tabelas em nível municipal e de alunos foram consideradas, mas não foram usadas nesta primeira versão para evitar aumento excessivo de volume, custo e complexidade.

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
├── transform_silver.py
└── transform_gold.py
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

## Pipeline Gold

A etapa Gold gera as tabelas finais de indicadores para análise da alfabetização.

Nesta camada foram criadas duas saídas principais:

- `indicadores_alfabetizacao_uf`: tabela com taxa de alfabetização, média de português, distância em relação ao ponto de corte de 743 pontos e status da UF em relação a esse ponto de corte;
- `comparativo_metas_uf_brasil`: tabela com comparação entre taxa observada, meta de alfabetização da UF e referência nacional.

A tabela de indicadores considera o ponto de corte de 743 pontos citado no desafio como referência para classificar a proficiência média.

Alguns registros permanecem com valores nulos quando a fonte original não possui meta ou resultado disponível para aquele ano ou UF. Esses casos são mantidos para preservar a rastreabilidade da informação original.

Para executar a etapa Gold:

```bash
python src/transform_gold.py
```

## Como executar a pipeline

Com o ambiente virtual ativado, execute os scripts na seguinte ordem:

```bash
python src/ingest_bronze.py
python src/transform_silver.py
python src/transform_gold.py
```

## Qualidade dos dados

Nesta primeira versão, as validações de qualidade foram aplicadas na camada Silver.

As regras implementadas verificam:

- duplicidade nas chaves principais de cada tabela;
- percentuais fora do intervalo esperado de 0 a 100.

O resultado das validações é salvo em:

```bash
data/silver/quality_report_silver.csv
```

## Observações

Os arquivos de dados brutos e os arquivos gerados nas camadas Bronze, Silver e Gold não são versionados no GitHub, seguindo boas práticas para projetos de dados.

A coluna `rede` possui dicionário oficial indicado pela Base dos Dados, mas a tabela de tradução não pôde ser acessada via download manual. Por isso, nesta versão do projeto, os códigos da tabela `uf` foram preservados sem tradução.

A ingestão principal foi tratada como batch, pois os dados oficiais de alfabetização são publicados de forma periódica. A parte de streaming será representada em uma etapa posterior por eventos operacionais da pipeline, como execução de cargas, validações de qualidade, alertas e atualização da camada Gold.

## Streaming e Monitoramento

Como os dados oficiais de alfabetização são publicados de forma periódica, a parte de streaming foi representada por eventos operacionais da pipeline.

O script `simulate_streaming_monitoring.py` gera eventos em formato JSONL para simular mensagens que poderiam ser enviadas para uma fila ou tópico em uma arquitetura real.

Os eventos representam situações como:

- ingestão Bronze concluída;
- transformação Silver concluída;
- validação de qualidade concluída;
- atualização das tabelas Gold;
- execução geral da pipeline finalizada.

Além dos eventos JSONL, também é gerado um log tabular de monitoramento com informações como etapa, status, tabela processada e quantidade de registros.

Para executar a simulação de streaming e monitoramento:

```bash
python src/simulate_streaming_monitoring.py
```
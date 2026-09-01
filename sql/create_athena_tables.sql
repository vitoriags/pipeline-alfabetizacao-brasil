-- Criação do banco usado no Athena para consultar as tabelas Gold do projeto.
CREATE DATABASE IF NOT EXISTS alfabetizacao_brasil;


-- Tabela Gold com indicadores de alfabetização por UF.
-- Os dados estão armazenados em Parquet no S3 e são consultados pelo Athena.
CREATE EXTERNAL TABLE IF NOT EXISTS alfabetizacao_brasil.indicadores_alfabetizacao_uf (
    ano BIGINT,
    sigla_uf STRING,
    serie_codigo STRING,
    rede_codigo STRING,
    taxa_alfabetizacao DOUBLE,
    media_portugues DOUBLE,
    distancia_ponto_corte DOUBLE,
    status_ponto_corte STRING
)
STORED AS PARQUET
LOCATION 's3://pipeline-alfabetizacao-brasil-vitoria-20260830/gold/indicadores_alfabetizacao_uf/';


-- Tabela Gold com comparação entre metas das UFs e referência nacional.
CREATE EXTERNAL TABLE IF NOT EXISTS alfabetizacao_brasil.comparativo_metas_uf_brasil (
    ano BIGINT,
    sigla_uf STRING,
    rede_descricao STRING,
    taxa_alfabetizacao DOUBLE,
    meta_referencia_ano DOUBLE,
    distancia_para_meta_uf DOUBLE,
    status_meta_uf STRING,
    taxa_alfabetizacao_brasil DOUBLE,
    meta_referencia_brasil DOUBLE,
    diferenca_taxa_uf_brasil DOUBLE,
    percentual_participacao DOUBLE,
    percentual_participacao_brasil DOUBLE
)
STORED AS PARQUET
LOCATION 's3://pipeline-alfabetizacao-brasil-vitoria-20260830/gold/comparativo_metas_uf_brasil/';

-- Tabela Gold com indicadores de alfabetização por município.
CREATE EXTERNAL TABLE IF NOT EXISTS alfabetizacao_brasil.indicadores_alfabetizacao_municipio (
    ano BIGINT,
    id_municipio STRING,
    serie_codigo STRING,
    rede_codigo STRING,
    taxa_alfabetizacao DOUBLE,
    media_portugues DOUBLE,
    distancia_ponto_corte DOUBLE,
    status_ponto_corte STRING
)
STORED AS PARQUET
LOCATION 's3://pipeline-alfabetizacao-brasil-vitoria-20260830/gold/indicadores_alfabetizacao_municipio/';


-- Tabela Gold com comparação entre metas municipais e referência nacional.
CREATE EXTERNAL TABLE IF NOT EXISTS alfabetizacao_brasil.comparativo_metas_municipio_brasil (
    ano BIGINT,
    id_municipio STRING,
    rede_descricao STRING,
    taxa_alfabetizacao DOUBLE,
    meta_referencia_ano DOUBLE,
    distancia_para_meta_municipio DOUBLE,
    status_meta_municipio STRING,
    taxa_alfabetizacao_brasil DOUBLE,
    meta_referencia_brasil DOUBLE,
    diferenca_taxa_municipio_brasil DOUBLE,
    nivel_alfabetizacao DOUBLE,
    percentual_participacao DOUBLE,
    percentual_participacao_brasil DOUBLE
)
STORED AS PARQUET
LOCATION 's3://pipeline-alfabetizacao-brasil-vitoria-20260830/gold/comparativo_metas_municipio_brasil/';
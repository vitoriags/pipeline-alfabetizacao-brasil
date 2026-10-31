from pathlib import Path

import pandas as pd

BRONZE_DIR = Path("data/bronze")
SILVER_DIR = Path("data/silver")

INDICADORES = {
    "93": "populacao_residente",
    "6318": "area_km2",
    "614": "densidade_demografica",
}


def transform_ibge_silver() -> None:
    # carregando os indicadores municipais da Bronze
    df = pd.read_parquet(BRONZE_DIR / "ibge_censo_2022.parquet")

    # verificando os códigos dos indicadores
    codigos = set(df["codigo_indicador"].astype(str).unique())

    if codigos != set(INDICADORES):
        raise ValueError("Os indicadores recebidos não correspondem aos esperados.")

    # verificando duplicidades por município e indicador
    chave = ["ano_referencia", "id_municipio", "codigo_indicador"]

    if df.duplicated(subset=chave).any():
        raise ValueError("Foram encontrados indicadores duplicados.")

    # renomeando os indicadores e convertendo os valores
    df["indicador"] = df["codigo_indicador"].map(INDICADORES)
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")

    if df["valor"].isna().any():
        raise ValueError("Foram encontrados valores numéricos inválidos.")

    # criando uma linha por município
    df_silver = df.pivot(
        index=["ano_referencia", "id_municipio", "nome_municipio"],
        columns="indicador",
        values="valor",
    ).reset_index()

    df_silver.columns.name = None

    # padronizando os tipos das colunas
    df_silver["ano_referencia"] = df_silver["ano_referencia"].astype("int64")
    df_silver["id_municipio"] = df_silver["id_municipio"].astype("string")
    df_silver["populacao_residente"] = df_silver["populacao_residente"].astype("int64")

    # mantendo os metadados da ingestão
    df_silver["data_ingestao"] = df["data_ingestao"].iloc[0]
    df_silver["arquivo_origem"] = df["arquivo_origem"].iloc[0]

    # salvando os indicadores territoriais na Silver
    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    output_path = SILVER_DIR / "ibge_censo_2022.parquet"
    df_silver.to_parquet(output_path, index=False)

    print(f"Tabela Silver salva em: {output_path}")
    print(f"Registros gerados: {len(df_silver)}")
    print(f"Duplicidades: {df_silver.duplicated(subset=['id_municipio']).sum()}")


def transform_ibge_renda_silver() -> None:
    # carregando a renda municipal da Bronze
    df = pd.read_parquet(BRONZE_DIR / "ibge_renda_2022.parquet")

    # verificando o código do indicador de renda mediana
    if set(df["codigo_indicador"].astype(str)) != {"13534"}:
        raise ValueError("O indicador de renda não corresponde ao esperado.")

    # padronizando os nomes e tipos das colunas
    df = df.rename(
        columns={"valor": "renda_mediana_per_capita"}
    )

    df["ano_referencia"] = df["ano_referencia"].astype("int64")
    df["id_municipio"] = df["id_municipio"].astype("string")
    df["nome_municipio"] = df["nome_municipio"].astype("string")

    df["renda_mediana_per_capita"] = pd.to_numeric(
        df["renda_mediana_per_capita"],
        errors="coerce",
    )

    # verificando a qualidade dos dados
    if df["id_municipio"].duplicated().any():
        raise ValueError("Foram encontrados municípios duplicados.")

    if df["renda_mediana_per_capita"].isna().any():
        raise ValueError("Foram encontrados valores de renda ausentes.")

    if (df["renda_mediana_per_capita"] <= 0).any():
        raise ValueError("Foram encontrados valores de renda inválidos.")

    if not df["ano_referencia"].eq(2022).all():
        raise ValueError("O ano de referência não corresponde a 2022.")

    # selecionando as colunas da Silver
    columns = [
        "ano_referencia",
        "id_municipio",
        "nome_municipio",
        "renda_mediana_per_capita",
        "data_ingestao",
        "arquivo_origem",
    ]

    df_silver = df[columns].copy()

    # salvando a renda municipal na Silver
    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    output_path = SILVER_DIR / "ibge_renda_2022.parquet"
    df_silver.to_parquet(output_path, index=False)

    print(f"Tabela Silver salva em: {output_path}")
    print(f"Registros gerados: {len(df_silver)}")
    print(f"Duplicidades: {df_silver['id_municipio'].duplicated().sum()}")
    print(f"Valores ausentes: {df_silver['renda_mediana_per_capita'].isna().sum()}")


if __name__ == "__main__":
    transform_ibge_silver()
    transform_ibge_renda_silver()
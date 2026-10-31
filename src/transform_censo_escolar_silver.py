from pathlib import Path

import pandas as pd

BRONZE_DIR = Path("data/bronze")
SILVER_DIR = Path("data/silver")

INDICADORES = [
    "biblioteca_sala_leitura",
    "internet_alunos",
    "internet_aprendizagem",
    "laboratorio_informatica",
]


def transform_censo_escolar_silver() -> None:
    # carregando os dados da Bronze
    df = pd.read_parquet(
        BRONZE_DIR / "censo_escolar_anos_iniciais.parquet"
    )

    # selecionando escolas estaduais e municipais
    df["rede"] = df["rede"].astype("string")
    df = df[df["rede"].isin(["2", "3"])].copy()

    if df.empty:
        raise ValueError("Nenhuma escola pública foi encontrada.")

    # verificando duplicidades
    if df.duplicated(subset=["ano", "id_escola"]).any():
        raise ValueError("Foram encontradas escolas duplicadas.")

    # verificando os valores dos indicadores
    for coluna in INDICADORES:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

        if df[coluna].isna().any():
            raise ValueError(f"Valores ausentes em {coluna}.")

        if not df[coluna].isin([0, 1]).all():
            raise ValueError(f"Valores inesperados em {coluna}.")

    # convertendo a quantidade de matrículas
    coluna_matriculas = "quantidade_matricula_fundamental_anos_iniciais"

    df[coluna_matriculas] = pd.to_numeric(
        df[coluna_matriculas],
        errors="coerce",
    )

    if df[coluna_matriculas].isna().any():
        raise ValueError("Foram encontradas matrículas ausentes.")

    if (df[coluna_matriculas] <= 0).any():
        raise ValueError("Foram encontradas matrículas inválidas.")

    # identificando escolas da rede municipal
    df["escola_municipal"] = (df["rede"] == "3").astype("int64")

    # agregando os indicadores por município e ano
    df_silver = df.groupby(
        ["ano", "id_municipio"],
        as_index=False,
    ).agg(
        escolas_publicas_anos_iniciais=("id_escola", "size"),
        matriculas_publicas_anos_iniciais=(
            coluna_matriculas,
            "sum",
        ),
        pct_escolas_com_biblioteca=(
            "biblioteca_sala_leitura",
            "mean",
        ),
        pct_escolas_com_internet_alunos=(
            "internet_alunos",
            "mean",
        ),
        pct_escolas_com_internet_aprendizagem=(
            "internet_aprendizagem",
            "mean",
        ),
        pct_escolas_com_laboratorio_informatica=(
            "laboratorio_informatica",
            "mean",
        ),
        pct_escolas_municipais=(
            "escola_municipal",
            "mean",
        ),
    )

    # convertendo as proporções em percentuais
    colunas_percentuais = [
        "pct_escolas_com_biblioteca",
        "pct_escolas_com_internet_alunos",
        "pct_escolas_com_internet_aprendizagem",
        "pct_escolas_com_laboratorio_informatica",
        "pct_escolas_municipais",
    ]

    df_silver[colunas_percentuais] = (
        df_silver[colunas_percentuais] * 100
    ).round(2)

    # identificando o ano do Censo e da avaliação
    df_silver = df_silver.rename(
        columns={"ano": "ano_censo"}
    )

    df_silver["ano_avaliacao"] = df_silver["ano_censo"] + 1

    # verificando duplicidades na base agregada
    chave = ["ano_avaliacao", "id_municipio"]

    if df_silver.duplicated(subset=chave).any():
        raise ValueError("Foram encontrados municípios duplicados.")

    # mantendo os metadados da origem
    df_silver["data_ingestao"] = df["data_ingestao"].iloc[0]
    df_silver["arquivo_origem"] = df["arquivo_origem"].iloc[0]

    # salvando a tabela na Silver
    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    output_path = SILVER_DIR / "censo_escolar_municipio.parquet"

    df_silver.to_parquet(output_path, index=False)

    print(f"Tabela Silver salva em: {output_path}")
    print(f"Escolas públicas processadas: {len(df)}")
    print(f"Registros municipais gerados: {len(df_silver)}")
    print(f"Duplicidades: {df_silver.duplicated(subset=chave).sum()}")

    print("\nCobertura por ano:")

    cobertura = df_silver.groupby(
        ["ano_censo", "ano_avaliacao"]
    ).agg(
        municipios=("id_municipio", "nunique"),
        escolas=("escolas_publicas_anos_iniciais", "sum"),
    )

    print(cobertura.to_string())

    print("\nValores ausentes:")
    print(df_silver.isna().sum().to_string())


if __name__ == "__main__":
    transform_censo_escolar_silver()
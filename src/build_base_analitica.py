from pathlib import Path

import pandas as pd

GOLD_DIR = Path("data/gold")
SILVER_DIR = Path("data/silver")

INDICADORES_EDUCACIONAIS = [
    "escolas_publicas_anos_iniciais",
    "matriculas_publicas_anos_iniciais",
    "pct_escolas_com_biblioteca",
    "pct_escolas_com_internet_alunos",
    "pct_escolas_com_internet_aprendizagem",
    "pct_escolas_com_laboratorio_informatica",
    "pct_escolas_municipais",
]


def build_alunos_contexto_municipal() -> pd.DataFrame:
    # carregando os alunos válidos da Gold
    alunos = pd.read_parquet(
        GOLD_DIR / "alunos_avaliacoes_validas.parquet"
    )

    # carregando os indicadores territoriais
    territorio = pd.read_parquet(
        SILVER_DIR / "ibge_censo_2022.parquet",
        columns=[
            "ano_referencia",
            "id_municipio",
            "nome_municipio",
            "populacao_residente",
            "area_km2",
            "densidade_demografica",
        ],
    )

    # carregando a renda municipal
    renda = pd.read_parquet(
        SILVER_DIR / "ibge_renda_2022.parquet",
        columns=[
            "ano_referencia",
            "id_municipio",
            "renda_mediana_per_capita",
        ],
    )

    # integrando os dados municipais do IBGE
    ibge = territorio.merge(
        renda,
        on=["ano_referencia", "id_municipio"],
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    if (ibge["_merge"] != "both").any():
        raise ValueError("Municípios sem correspondência na renda.")

    ibge = ibge.drop(columns="_merge")

    ibge = ibge.rename(
        columns={"ano_referencia": "ano_referencia_ibge"}
    )

    # relacionando o contexto municipal aos alunos
    df = alunos.merge(
        ibge,
        on="id_municipio",
        how="left",
        validate="many_to_one",
        indicator=True,
    )

    if (df["_merge"] != "both").any():
        raise ValueError("Alunos sem correspondência nos dados do IBGE.")

    df = df.drop(columns="_merge")

    if len(df) != len(alunos):
        raise ValueError("A integração do IBGE alterou a quantidade de alunos.")

    indicadores_ibge = [
        "populacao_residente",
        "area_km2",
        "densidade_demografica",
        "renda_mediana_per_capita",
    ]

    if df[indicadores_ibge].isna().any().any():
        raise ValueError("Foram encontrados indicadores do IBGE ausentes.")

    return df


def build_base_analitica() -> pd.DataFrame:
    # carregando os alunos com contexto municipal
    alunos = build_alunos_contexto_municipal()

    # carregando os indicadores educacionais da Silver
    censo = pd.read_parquet(
        SILVER_DIR / "censo_escolar_municipio.parquet",
        columns=[
            "ano_censo",
            "ano_avaliacao",
            "id_municipio",
            *INDICADORES_EDUCACIONAIS,
        ],
    )

    # verificando as chaves do Censo Escolar
    chave = ["ano_avaliacao", "id_municipio"]

    if censo.duplicated(subset=chave).any():
        raise ValueError("Foram encontrados municípios duplicados no Censo Escolar.")

    # verificando se o Censo é do ano anterior à avaliação
    if not (censo["ano_censo"] == censo["ano_avaliacao"] - 1).all():
        raise ValueError("Os anos do Censo Escolar não correspondem ao esperado.")

    # integrando os indicadores educacionais aos alunos
    df = alunos.merge(
        censo,
        left_on=["ano", "id_municipio"],
        right_on=["ano_avaliacao", "id_municipio"],
        how="left",
        validate="many_to_one",
        indicator=True,
    )

    # verificando a correspondência dos registros
    sem_correspondencia = (df["_merge"] != "both").sum()

    if sem_correspondencia > 0:
        raise ValueError(
            f"{sem_correspondencia} alunos sem correspondência no Censo Escolar."
        )

    df = df.drop(columns=["_merge", "ano_avaliacao"])

    # verificando se todos os alunos foram preservados
    if len(df) != len(alunos):
        raise ValueError("A integração alterou a quantidade de alunos.")

    # verificando valores ausentes
    if df[INDICADORES_EDUCACIONAIS].isna().any().any():
        raise ValueError("Foram encontrados indicadores educacionais ausentes.")

    # verificando o intervalo dos percentuais
    colunas_percentuais = [
        coluna
        for coluna in INDICADORES_EDUCACIONAIS
        if coluna.startswith("pct_")
    ]

    for coluna in colunas_percentuais:
        if not df[coluna].between(0, 100).all():
            raise ValueError(f"Percentuais inválidos em {coluna}.")

    return df


def main() -> None:
    # construindo a base analítica enriquecida
    df = build_base_analitica()

    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    output_path = GOLD_DIR / "base_analitica_alfabetizacao.parquet"

    # salvando a base final desta etapa
    df.to_parquet(output_path, index=False)

    print(f"Tabela Gold salva em: {output_path}")
    print(f"Registros gerados: {len(df)}")
    print(f"Municípios: {df['id_municipio'].nunique()}")
    print(f"Colunas: {len(df.columns)}")

    print("\nDistribuição por ano da avaliação e ano do Censo:")
    print(
        df.groupby(["ano", "ano_censo"])
        .size()
        .to_string()
    )

    print("\nIndicadores educacionais integrados:")
    for coluna in INDICADORES_EDUCACIONAIS:
        print(f"- {coluna}")

    print("\nValores ausentes nos indicadores educacionais:")
    print(df[INDICADORES_EDUCACIONAIS].isna().sum().to_string())


if __name__ == "__main__":
    main()
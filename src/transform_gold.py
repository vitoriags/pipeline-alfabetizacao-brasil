from pathlib import Path

import pandas as pd


SILVER_DIR = Path("data/silver")
GOLD_DIR = Path("data/gold")

PONTO_CORTE_ALFABETIZACAO = 743


def read_silver_table(table_name: str) -> pd.DataFrame:
    return pd.read_parquet(SILVER_DIR / f"{table_name}.parquet")


def save_gold_table(df: pd.DataFrame, table_name: str) -> None:
    output_path = GOLD_DIR / f"{table_name}.parquet"
    df.to_parquet(output_path, index=False)

    print(f"Tabela Gold salva em: {output_path}")
    print(f"Registros gerados: {len(df)}")


def build_indicadores_alfabetizacao_uf(df_uf: pd.DataFrame) -> pd.DataFrame:
    df = df_uf.copy()

    # O ponto de corte de 743 pontos é usado como referência para avaliar a proficiência média.
    df["distancia_ponto_corte"] = df["media_portugues"] - PONTO_CORTE_ALFABETIZACAO

    df["status_ponto_corte"] = "abaixo_do_ponto_corte"
    df.loc[
        df["media_portugues"] >= PONTO_CORTE_ALFABETIZACAO,
        "status_ponto_corte",
    ] = "acima_ou_igual_ao_ponto_corte"

    columns = [
        "ano",
        "sigla_uf",
        "serie_codigo",
        "rede_codigo",
        "taxa_alfabetizacao",
        "media_portugues",
        "distancia_ponto_corte",
        "status_ponto_corte",
    ]

    return df[columns]


def build_indicadores_alfabetizacao_municipio(df_municipio: pd.DataFrame) -> pd.DataFrame:
    df = df_municipio.copy()

    # A lógica municipal segue a mesma referência usada na tabela de UF,
    # mas em uma granularidade mais detalhada.
    df["distancia_ponto_corte"] = df["media_portugues"] - PONTO_CORTE_ALFABETIZACAO

    df["status_ponto_corte"] = "abaixo_do_ponto_corte"
    df.loc[
        df["media_portugues"] >= PONTO_CORTE_ALFABETIZACAO,
        "status_ponto_corte",
    ] = "acima_ou_igual_ao_ponto_corte"

    columns = [
        "ano",
        "id_municipio",
        "serie_codigo",
        "rede_codigo",
        "taxa_alfabetizacao",
        "media_portugues",
        "distancia_ponto_corte",
        "status_ponto_corte",
    ]

    return df[columns]


def add_meta_referencia_ano(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["meta_referencia_ano"] = pd.NA

    # As metas estão em colunas separadas por ano.
    # Aqui eu trago para uma única coluna a meta correspondente ao ano do registro.
    for ano in df["ano"].dropna().unique():
        meta_column = f"meta_alfabetizacao_{int(ano)}"

        if meta_column in df.columns:
            df.loc[df["ano"] == ano, "meta_referencia_ano"] = df.loc[
                df["ano"] == ano,
                meta_column,
            ]

    df["meta_referencia_ano"] = pd.to_numeric(df["meta_referencia_ano"])

    return df


def add_status_meta(df: pd.DataFrame, distance_column: str, status_column: str) -> pd.DataFrame:
    df = df.copy()

    df[status_column] = "sem_meta_ou_resultado"
    valid_rows = df[distance_column].notna()

    df.loc[
        valid_rows & (df[distance_column] >= 0),
        status_column,
    ] = "atingiu_ou_superou_meta"

    df.loc[
        valid_rows & (df[distance_column] < 0),
        status_column,
    ] = "abaixo_da_meta"

    return df


def build_comparativo_metas_uf_brasil(
    df_meta_uf: pd.DataFrame,
    df_meta_brasil: pd.DataFrame,
) -> pd.DataFrame:
    meta_uf = add_meta_referencia_ano(df_meta_uf)
    meta_brasil = add_meta_referencia_ano(df_meta_brasil)

    meta_uf["distancia_para_meta_uf"] = (
        meta_uf["taxa_alfabetizacao"] - meta_uf["meta_referencia_ano"]
    )

    meta_uf = add_status_meta(
        meta_uf,
        distance_column="distancia_para_meta_uf",
        status_column="status_meta_uf",
    )

    brasil_reference = meta_brasil[
        [
            "ano",
            "rede_descricao",
            "taxa_alfabetizacao",
            "meta_referencia_ano",
            "percentual_participacao",
        ]
    ].rename(
        columns={
            "taxa_alfabetizacao": "taxa_alfabetizacao_brasil",
            "meta_referencia_ano": "meta_referencia_brasil",
            "percentual_participacao": "percentual_participacao_brasil",
        }
    )

    df = meta_uf.merge(
        brasil_reference,
        on=["ano", "rede_descricao"],
        how="left",
    )

    df["diferenca_taxa_uf_brasil"] = (
        df["taxa_alfabetizacao"] - df["taxa_alfabetizacao_brasil"]
    )

    columns = [
        "ano",
        "sigla_uf",
        "rede_descricao",
        "taxa_alfabetizacao",
        "meta_referencia_ano",
        "distancia_para_meta_uf",
        "status_meta_uf",
        "taxa_alfabetizacao_brasil",
        "meta_referencia_brasil",
        "diferenca_taxa_uf_brasil",
        "percentual_participacao",
        "percentual_participacao_brasil",
    ]

    return df[columns]


def build_comparativo_metas_municipio_brasil(
    df_meta_municipio: pd.DataFrame,
    df_meta_brasil: pd.DataFrame,
) -> pd.DataFrame:
    meta_municipio = add_meta_referencia_ano(df_meta_municipio)
    meta_brasil = add_meta_referencia_ano(df_meta_brasil)

    # Esta tabela ajuda a analisar municípios em relação às próprias metas
    # e também em comparação com a referência nacional.
    meta_municipio["distancia_para_meta_municipio"] = (
        meta_municipio["taxa_alfabetizacao"] - meta_municipio["meta_referencia_ano"]
    )

    meta_municipio = add_status_meta(
        meta_municipio,
        distance_column="distancia_para_meta_municipio",
        status_column="status_meta_municipio",
    )

    brasil_reference = meta_brasil[
        [
            "ano",
            "rede_descricao",
            "taxa_alfabetizacao",
            "meta_referencia_ano",
            "percentual_participacao",
        ]
    ].rename(
        columns={
            "taxa_alfabetizacao": "taxa_alfabetizacao_brasil",
            "meta_referencia_ano": "meta_referencia_brasil",
            "percentual_participacao": "percentual_participacao_brasil",
        }
    )

    df = meta_municipio.merge(
        brasil_reference,
        on=["ano", "rede_descricao"],
        how="left",
    )

    df["diferenca_taxa_municipio_brasil"] = (
        df["taxa_alfabetizacao"] - df["taxa_alfabetizacao_brasil"]
    )

    columns = [
        "ano",
        "id_municipio",
        "rede_descricao",
        "taxa_alfabetizacao",
        "meta_referencia_ano",
        "distancia_para_meta_municipio",
        "status_meta_municipio",
        "taxa_alfabetizacao_brasil",
        "meta_referencia_brasil",
        "diferenca_taxa_municipio_brasil",
        "nivel_alfabetizacao",
        "percentual_participacao",
        "percentual_participacao_brasil",
    ]

    return df[columns]


def main() -> None:
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    df_uf = read_silver_table("uf")
    df_municipio = read_silver_table("municipio")
    df_meta_uf = read_silver_table("meta_alfabetizacao_uf")
    df_meta_brasil = read_silver_table("meta_alfabetizacao_brasil")
    df_meta_municipio = read_silver_table("meta_alfabetizacao_municipio")

    indicadores_uf = build_indicadores_alfabetizacao_uf(df_uf)
    indicadores_municipio = build_indicadores_alfabetizacao_municipio(df_municipio)

    comparativo_metas_uf = build_comparativo_metas_uf_brasil(
        df_meta_uf,
        df_meta_brasil,
    )

    comparativo_metas_municipio = build_comparativo_metas_municipio_brasil(
        df_meta_municipio,
        df_meta_brasil,
    )

    save_gold_table(indicadores_uf, "indicadores_alfabetizacao_uf")
    save_gold_table(indicadores_municipio, "indicadores_alfabetizacao_municipio")
    save_gold_table(comparativo_metas_uf, "comparativo_metas_uf_brasil")
    save_gold_table(comparativo_metas_municipio, "comparativo_metas_municipio_brasil")


if __name__ == "__main__":
    main()
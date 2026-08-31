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


def build_comparativo_metas_uf_brasil(
    df_meta_uf: pd.DataFrame,
    df_meta_brasil: pd.DataFrame,
) -> pd.DataFrame:
    meta_uf = add_meta_referencia_ano(df_meta_uf)
    meta_brasil = add_meta_referencia_ano(df_meta_brasil)

    meta_uf["distancia_para_meta_uf"] = (
        meta_uf["taxa_alfabetizacao"] - meta_uf["meta_referencia_ano"]
    )

    meta_uf["status_meta_uf"] = "sem_meta_ou_resultado"
    valid_rows = meta_uf["distancia_para_meta_uf"].notna()

    meta_uf.loc[
        valid_rows & (meta_uf["distancia_para_meta_uf"] >= 0),
        "status_meta_uf",
    ] = "atingiu_ou_superou_meta"

    meta_uf.loc[
        valid_rows & (meta_uf["distancia_para_meta_uf"] < 0),
        "status_meta_uf",
    ] = "abaixo_da_meta"

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


def main() -> None:
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    df_uf = read_silver_table("uf")
    df_meta_uf = read_silver_table("meta_alfabetizacao_uf")
    df_meta_brasil = read_silver_table("meta_alfabetizacao_brasil")

    indicadores_uf = build_indicadores_alfabetizacao_uf(df_uf)
    comparativo_metas = build_comparativo_metas_uf_brasil(df_meta_uf, df_meta_brasil)

    save_gold_table(indicadores_uf, "indicadores_alfabetizacao_uf")
    save_gold_table(comparativo_metas, "comparativo_metas_uf_brasil")


if __name__ == "__main__":
    main()
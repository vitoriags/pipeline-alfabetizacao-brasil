from pathlib import Path

import pandas as pd


BRONZE_DIR = Path("data/bronze")
SILVER_DIR = Path("data/silver")


def read_bronze_table(table_name: str) -> pd.DataFrame:
    return pd.read_parquet(BRONZE_DIR / f"{table_name}.parquet")


def save_silver_table(df: pd.DataFrame, table_name: str) -> None:
    output_path = SILVER_DIR / f"{table_name}.parquet"
    df.to_parquet(output_path, index=False)
    print(f"Tabela Silver salva em: {output_path}")


def standardize_uf(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df = df.rename(
        columns={
            "serie": "serie_codigo",
            "rede": "rede_codigo",
        }
    )

    df["ano"] = df["ano"].astype("int64")
    df["sigla_uf"] = df["sigla_uf"].astype("string").str.upper().str.strip()
    df["serie_codigo"] = df["serie_codigo"].astype("string")
    df["rede_codigo"] = df["rede_codigo"].astype("string")

    return df


def standardize_meta_uf(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.rename(columns={"rede": "rede_descricao"})

    df["ano"] = df["ano"].astype("int64")
    df["sigla_uf"] = df["sigla_uf"].astype("string").str.upper().str.strip()
    df["rede_descricao"] = df["rede_descricao"].astype("string").str.strip()

    return df


def standardize_meta_brasil(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df = df.rename(columns={"rede": "rede_descricao"})

    df["ano"] = df["ano"].astype("int64")
    df["rede_descricao"] = df["rede_descricao"].astype("string").str.strip()

    return df


def validate_duplicates(df: pd.DataFrame, table_name: str, key_columns: list[str]) -> dict:
    duplicated_rows = df.duplicated(subset=key_columns).sum()

    return {
        "tabela": table_name,
        "regra": "duplicidade_chave",
        "colunas": ", ".join(key_columns),
        "status": "ok" if duplicated_rows == 0 else "erro",
        "qtd_ocorrencias": int(duplicated_rows),
    }


def validate_percentage_range(df: pd.DataFrame, table_name: str, columns: list[str]) -> list[dict]:
    results = []

    for column in columns:
        values = df[column].dropna()
        invalid_rows = ((values < 0) | (values > 100)).sum()

        results.append(
            {
                "tabela": table_name,
                "regra": "percentual_entre_0_e_100",
                "colunas": column,
                "status": "ok" if invalid_rows == 0 else "erro",
                "qtd_ocorrencias": int(invalid_rows),
            }
        )

    return results


def main() -> None:
    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    df_uf = standardize_uf(read_bronze_table("uf"))
    df_meta_uf = standardize_meta_uf(read_bronze_table("meta_alfabetizacao_uf"))
    df_meta_brasil = standardize_meta_brasil(read_bronze_table("meta_alfabetizacao_brasil"))

    save_silver_table(df_uf, "uf")
    save_silver_table(df_meta_uf, "meta_alfabetizacao_uf")
    save_silver_table(df_meta_brasil, "meta_alfabetizacao_brasil")

    # relatório de qualidade da camada silver
    quality_results = [
        validate_duplicates(
            df_uf,
            "uf",
            ["ano", "sigla_uf", "serie_codigo", "rede_codigo"],
        ),
        validate_duplicates(
            df_meta_uf,
            "meta_alfabetizacao_uf",
            ["ano", "sigla_uf", "rede_descricao"],
        ),
        validate_duplicates(
            df_meta_brasil,
            "meta_alfabetizacao_brasil",
            ["ano", "rede_descricao"],
        ),
    ]

    uf_percentage_columns = [
        "taxa_alfabetizacao",
        "proporcao_aluno_nivel_0",
        "proporcao_aluno_nivel_1",
        "proporcao_aluno_nivel_2",
        "proporcao_aluno_nivel_3",
        "proporcao_aluno_nivel_4",
        "proporcao_aluno_nivel_5",
        "proporcao_aluno_nivel_6",
        "proporcao_aluno_nivel_7",
        "proporcao_aluno_nivel_8",
    ]

    meta_percentage_columns = [
        "taxa_alfabetizacao",
        "meta_alfabetizacao_2024",
        "meta_alfabetizacao_2025",
        "meta_alfabetizacao_2026",
        "meta_alfabetizacao_2027",
        "meta_alfabetizacao_2028",
        "meta_alfabetizacao_2029",
        "meta_alfabetizacao_2030",
        "percentual_participacao",
    ]

    quality_results.extend(validate_percentage_range(df_uf, "uf", uf_percentage_columns))
    quality_results.extend(
        validate_percentage_range(df_meta_uf, "meta_alfabetizacao_uf", meta_percentage_columns)
    )
    quality_results.extend(
        validate_percentage_range(df_meta_brasil, "meta_alfabetizacao_brasil", meta_percentage_columns)
    )

    quality_report = pd.DataFrame(quality_results)
    quality_report.to_csv(SILVER_DIR / "quality_report_silver.csv", index=False)

    print("Relatório de qualidade salvo em: data/silver/quality_report_silver.csv")


if __name__ == "__main__":
    main()
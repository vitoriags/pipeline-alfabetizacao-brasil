import os
from datetime import datetime, timezone
from pathlib import Path

import basedosdados as bd

BRONZE_DIR = Path("data/bronze")

SOURCE_TABLE = "basedosdados.br_inep_censo_escolar.escola"


def ingest_censo_escolar() -> None:
    # verificando a configuração do BigQuery
    project_id = os.getenv("BD_BILLING_PROJECT_ID")

    if not project_id:
        raise ValueError("A variável BD_BILLING_PROJECT_ID não foi definida.")

    # selecionando escolas com matrículas nos anos iniciais
    query = f"""
    SELECT
        ano,
        id_municipio,
        id_escola,
        rede,
        tipo_localizacao,
        quantidade_matricula_fundamental_anos_iniciais,
        biblioteca_sala_leitura,
        internet_alunos,
        internet_aprendizagem,
        laboratorio_informatica
    FROM `{SOURCE_TABLE}`
    WHERE ano IN (2022, 2023)
      AND quantidade_matricula_fundamental_anos_iniciais > 0
      AND id_municipio IS NOT NULL
      AND id_escola IS NOT NULL
    """

    # carregando os dados do Censo Escolar
    df = bd.read_sql(
        query=query,
        billing_project_id=project_id,
    )

    if df.empty:
        raise ValueError("Nenhum registro foi encontrado no Censo Escolar.")

    # padronizando os identificadores
    df["ano"] = df["ano"].astype("int64")
    df["id_municipio"] = df["id_municipio"].astype("string")
    df["id_escola"] = df["id_escola"].astype("string")

    # verificando duplicidades por escola e ano
    duplicidades = df.duplicated(
        subset=["ano", "id_escola"]
    ).sum()

    if duplicidades > 0:
        raise ValueError(
            f"Foram encontradas {duplicidades} escolas duplicadas."
        )

    # registrando a origem dos dados
    df["data_ingestao"] = datetime.now(timezone.utc)
    df["arquivo_origem"] = SOURCE_TABLE

    # salvando os dados na Bronze
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)

    output_path = BRONZE_DIR / "censo_escolar_anos_iniciais.parquet"
    df.to_parquet(output_path, index=False)

    print(f"\nTabela Bronze salva em: {output_path}")
    print(f"Registros processados: {len(df)}")
    print(f"Duplicidades: {duplicidades}")

    # verificando a cobertura por ano
    print("\nCobertura por ano:")

    cobertura = df.groupby("ano").agg(
        escolas=("id_escola", "size"),
        municipios=("id_municipio", "nunique"),
    )

    print(cobertura.to_string())

    # verificando as redes de ensino
    print("\nRedes de ensino:")
    print(df["rede"].value_counts(dropna=False).to_string())

    # verificando os valores ausentes
    print("\nValores ausentes nos indicadores:")

    indicadores = [
        "tipo_localizacao",
        "biblioteca_sala_leitura",
        "internet_alunos",
        "internet_aprendizagem",
        "laboratorio_informatica",
    ]

    print(df[indicadores].isna().sum().to_string())


if __name__ == "__main__":
    ingest_censo_escolar()
import os
from datetime import datetime, timezone
from pathlib import Path

import basedosdados as bd
import pandas as pd

RAW_DIR = Path("data/raw")
BRONZE_DIR = Path("data/bronze")
ALUNOS_TABLE_ID = "basedosdados.br_inep_avaliacao_alfabetizacao.alunos"
BILLING_PROJECT_ENV = "BD_BILLING_PROJECT_ID"

# Tabelas escolhidas para o MVP do projeto.
# A camada Bronze mantém os dados próximos da fonte, apenas mudando o formato de armazenamento.
SOURCES = {
    "uf": "br_inep_avaliacao_alfabetizacao_uf.csv.gz",
    "meta_alfabetizacao_uf": "br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_uf.csv.gz",
    "meta_alfabetizacao_brasil": "br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_brasil.csv.gz",
    "municipio": "br_inep_avaliacao_alfabetizacao_municipio.csv.gz",
    "meta_alfabetizacao_municipio": "br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_municipio.csv.gz",
}

def ingest_to_bronze(table_name: str, file_name: str) -> None:
    input_path = RAW_DIR / file_name
    output_path = BRONZE_DIR / f"{table_name}.parquet"

    print(f"Iniciando ingestão da tabela: {table_name}")

    df = pd.read_csv(input_path, compression="gzip")

    # Metadados simples para rastrear a origem e o momento da ingestão.
    df["data_ingestao"] = datetime.now(timezone.utc)
    df["arquivo_origem"] = file_name

    # usando parquet por ser mais eficiente para armazenamento e consulta
    df.to_parquet(output_path, index=False)

    print(f"Tabela {table_name} salva em: {output_path}")
    print(f"Registros processados: {len(df)}")

def get_billing_project_id() -> str:
    billing_project_id = os.getenv(BILLING_PROJECT_ENV)

    if not billing_project_id:
        raise ValueError(
            f"A variável de ambiente {BILLING_PROJECT_ENV} não foi definida."
        )

    return billing_project_id

def load_alunos_from_bigquery(limit: int | None = None) -> pd.DataFrame:
    billing_project_id = get_billing_project_id()

    query = f"""
        SELECT
            ano,
            id_municipio,
            id_escola,
            id_aluno,
            caderno,
            serie,
            rede,
            presenca,
            preenchimento_caderno,
            alfabetizado,
            proficiencia,
            peso_aluno
        FROM `{ALUNOS_TABLE_ID}`
    """

    if limit is not None:
        query += f"\nLIMIT {limit}"

    return bd.read_sql(
        query=query,
        billing_project_id=billing_project_id,
    )

def ingest_alunos_to_bronze() -> None:
    output_path = BRONZE_DIR / "alunos.parquet"

    print("Iniciando ingestão da tabela: alunos")

    df = load_alunos_from_bigquery()

    # Mantendo o mesmo padrão de rastreabilidade das demais fontes Bronze.
    df["data_ingestao"] = datetime.now(timezone.utc)
    df["arquivo_origem"] = ALUNOS_TABLE_ID

    df.to_parquet(output_path, index=False)

    print(f"Tabela alunos salva em: {output_path}")
    print(f"Registros processados: {len(df)}")


def main() -> None:
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)

    for table_name, file_name in SOURCES.items():
        ingest_to_bronze(table_name, file_name)

    ingest_alunos_to_bronze()


if __name__ == "__main__":
    main()
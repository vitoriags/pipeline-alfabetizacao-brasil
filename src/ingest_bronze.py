from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


RAW_DIR = Path("data/raw")
BRONZE_DIR = Path("data/bronze")

# Tabelas escolhidas para o MVP do projeto.
# A camada Bronze mantém os dados próximos da fonte, apenas mudando o formato de armazenamento.
SOURCES = {
    "uf": "br_inep_avaliacao_alfabetizacao_uf.csv.gz",
    "meta_alfabetizacao_uf": "br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_uf.csv.gz",
    "meta_alfabetizacao_brasil": "br_inep_avaliacao_alfabetizacao_meta_alfabetizacao_brasil.csv.gz",
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


def main() -> None:
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)

    for table_name, file_name in SOURCES.items():
        ingest_to_bronze(table_name, file_name)


if __name__ == "__main__":
    main()
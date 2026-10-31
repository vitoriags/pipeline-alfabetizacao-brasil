from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

BRONZE_DIR = Path("data/bronze")

IBGE_API_URL = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/4714"
    "/periodos/2022/variaveis/93|6318|614"
)

IBGE_RENDA_URL = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/10295"
    "/periodos/2022/variaveis/13534"
)


def ingest_ibge_censo_2022() -> None:
    # consultando os indicadores municipais do Censo 2022
    response = requests.get(
        IBGE_API_URL,
        params={"localidades": "N6[all]"},
        timeout=120,
    )
    response.raise_for_status()

    dados = response.json()
    registros = []

    # organizando os dados retornados pela API
    for indicador in dados:
        for municipio in indicador["resultados"][0]["series"]:
            registros.append(
                {
                    "ano_referencia": 2022,
                    "id_municipio": str(municipio["localidade"]["id"]),
                    "nome_municipio": municipio["localidade"]["nome"],
                    "codigo_indicador": str(indicador["id"]),
                    "nome_indicador": indicador["variavel"],
                    "valor": municipio["serie"].get("2022"),
                }
            )

    df = pd.DataFrame(registros)

    # adicionando os metadados da ingestão
    df["data_ingestao"] = datetime.now(timezone.utc)
    df["arquivo_origem"] = IBGE_API_URL

    BRONZE_DIR.mkdir(parents=True, exist_ok=True)

    output_path = BRONZE_DIR / "ibge_censo_2022.parquet"
    df.to_parquet(output_path, index=False)

    print(f"Tabela Bronze salva em: {output_path}")
    print(f"Registros processados: {len(df)}")
    print(f"Municípios: {df['id_municipio'].nunique()}")
    print(f"Indicadores: {df['codigo_indicador'].nunique()}")


def ingest_ibge_renda_2022() -> None:
    # consultando a renda mediana municipal do Censo 2022
    params = {
        "localidades": "N6[all]",
        "classificacao": "2[6794]|86[95251]|58[95253]",
    }

    response = requests.get(
        IBGE_RENDA_URL,
        params=params,
        timeout=120,
    )
    response.raise_for_status()

    dados = response.json()
    registros = []

    # organizando os resultados por município
    for indicador in dados:
        for resultado in indicador["resultados"]:
            for municipio in resultado["series"]:
                registros.append(
                    {
                        "ano_referencia": 2022,
                        "id_municipio": str(
                            municipio["localidade"]["id"]
                        ),
                        "nome_municipio": municipio["localidade"]["nome"],
                        "codigo_indicador": str(indicador["id"]),
                        "nome_indicador": indicador["variavel"],
                        "valor": municipio["serie"].get("2022"),
                    }
                )

    df = pd.DataFrame(registros)

    # verificando a quantidade de municípios e possíveis duplicidades
    if len(df) != 5570 or df["id_municipio"].duplicated().any():
        raise ValueError("A tabela de renda possui cobertura inesperada.")

    # adicionando os metadados da ingestão
    df["data_ingestao"] = datetime.now(timezone.utc)
    df["arquivo_origem"] = response.url

    BRONZE_DIR.mkdir(parents=True, exist_ok=True)

    output_path = BRONZE_DIR / "ibge_renda_2022.parquet"
    df.to_parquet(output_path, index=False)

    print(f"Tabela Bronze salva em: {output_path}")
    print(f"Registros processados: {len(df)}")
    print(f"Municípios: {df['id_municipio'].nunique()}")


if __name__ == "__main__":
    ingest_ibge_censo_2022()
    ingest_ibge_renda_2022()
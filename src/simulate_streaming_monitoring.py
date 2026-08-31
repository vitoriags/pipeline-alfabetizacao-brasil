import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd


BRONZE_DIR = Path("data/bronze")
SILVER_DIR = Path("data/silver")
GOLD_DIR = Path("data/gold")

STREAMING_DIR = Path("data/streaming")
MONITORING_DIR = Path("data/monitoring")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def count_parquet_rows(path: Path) -> int:
    if not path.exists():
        return 0

    return len(pd.read_parquet(path))


def create_event(event_type: str, stage: str, status: str, details: dict) -> dict:
    return {
        "event_id": str(uuid4()),
        "event_timestamp": now_utc(),
        "event_type": event_type,
        "stage": stage,
        "status": status,
        "details": details,
    }


def write_jsonl(events: list[dict], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8") as file:
        for event in events:
            file.write(json.dumps(event, ensure_ascii=False) + "\n")


def build_pipeline_events() -> list[dict]:
    events = []

    bronze_tables = [
        "uf",
        "meta_alfabetizacao_uf",
        "meta_alfabetizacao_brasil",
    ]

    silver_tables = [
        "uf",
        "meta_alfabetizacao_uf",
        "meta_alfabetizacao_brasil",
    ]

    gold_tables = [
        "indicadores_alfabetizacao_uf",
        "comparativo_metas_uf_brasil",
    ]

    # Como os dados oficiais são publicados de forma periódica,
    # o streaming foi simulado com eventos operacionais da pipeline.
    # A ideia é representar mensagens de acompanhamento que poderiam ser enviadas
    # para uma fila ou tópico em uma arquitetura real.
    for table in bronze_tables:
        rows = count_parquet_rows(BRONZE_DIR / f"{table}.parquet")

        events.append(
            create_event(
                event_type="bronze_ingestion_completed",
                stage="bronze",
                status="success" if rows > 0 else "warning",
                details={
                    "table": table,
                    "records_processed": rows,
                },
            )
        )

    for table in silver_tables:
        rows = count_parquet_rows(SILVER_DIR / f"{table}.parquet")

        events.append(
            create_event(
                event_type="silver_transformation_completed",
                stage="silver",
                status="success" if rows > 0 else "warning",
                details={
                    "table": table,
                    "records_processed": rows,
                },
            )
        )

    # O relatório de qualidade da Silver também gera um evento.
    # Assim, a pipeline consegue sinalizar se alguma regra falhou.
    quality_report_path = SILVER_DIR / "quality_report_silver.csv"

    if quality_report_path.exists():
        quality_report = pd.read_csv(quality_report_path)
        errors = quality_report[quality_report["status"] != "ok"]

        events.append(
            create_event(
                event_type="quality_validation_completed",
                stage="silver",
                status="success" if errors.empty else "warning",
                details={
                    "total_rules": len(quality_report),
                    "rules_with_error": len(errors),
                },
            )
        )

    for table in gold_tables:
        rows = count_parquet_rows(GOLD_DIR / f"{table}.parquet")

        events.append(
            create_event(
                event_type="gold_table_updated",
                stage="gold",
                status="success" if rows > 0 else "warning",
                details={
                    "table": table,
                    "records_processed": rows,
                },
            )
        )

    events.append(
        create_event(
            event_type="pipeline_run_completed",
            stage="pipeline",
            status="success",
            details={
                "message": "Execução simulada de eventos da pipeline concluída.",
            },
        )
    )

    return events


def build_monitoring_log(events: list[dict]) -> pd.DataFrame:
    rows = []

    # A partir dos eventos JSON, também crio uma visão tabular de monitoramento.
    # Facilitando a leitura do status da pipeline e pode ser usado em análises futuras.
    for event in events:
        details = event["details"]

        rows.append(
            {
                "event_id": event["event_id"],
                "event_timestamp": event["event_timestamp"],
                "event_type": event["event_type"],
                "stage": event["stage"],
                "status": event["status"],
                "table": details.get("table"),
                "records_processed": details.get("records_processed"),
                "total_rules": details.get("total_rules"),
                "rules_with_error": details.get("rules_with_error"),
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    STREAMING_DIR.mkdir(parents=True, exist_ok=True)
    MONITORING_DIR.mkdir(parents=True, exist_ok=True)

    events = build_pipeline_events()

    streaming_output_path = STREAMING_DIR / "pipeline_events.jsonl"
    monitoring_output_path = MONITORING_DIR / "pipeline_monitoring_log.csv"

    write_jsonl(events, streaming_output_path)

    monitoring_log = build_monitoring_log(events)
    monitoring_log.to_csv(monitoring_output_path, index=False)

    print(f"Eventos streaming salvos em: {streaming_output_path}")
    print(f"Log de monitoramento salvo em: {monitoring_output_path}")
    print(f"Eventos gerados: {len(events)}")


if __name__ == "__main__":
    main()
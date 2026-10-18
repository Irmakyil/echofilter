"""Create a privacy-preserving label-only derivative of DepremKit Gold.

Usage: python scripts/prepare_depremkit_benchmark.py path/to/gold_dataset.tsv
The output deliberately excludes tweet IDs, source ordering, tweet text, and raw spans.
"""

from __future__ import annotations

import argparse
import ast
import random
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LABELS = {
    "Konu Dışı": "Off-topic",
    "Bilgi Paylaşımı": "Information sharing",
    "Yardım Çağrısı": "Help request",
    "Bağış ve Gönüllülük": "Donation and volunteering",
    "İhtiyaç": "Need",
}
ENTITY_LABELS = {
    "il": "province",
    "ilçe": "district",
    "mahalle veya köy": "neighborhood_or_village",
    "bulvar veya cadde veya sokak": "street_or_road",
    "apartman veya bina veya site": "building",
    "no": "address_number",
    "kişi": "person",
    "kişi durumu": "person_status",
    "ihtiyaç": "need_entity",
    "yer": "place",
}


def prepare(input_path: Path, output_path: Path) -> None:
    source = pd.read_csv(input_path, sep="\t", keep_default_na=False)
    required = {"binary_label", "multiclass_label", "ner_label"}
    if not required.issubset(source.columns):
        raise ValueError(f"Source file is missing required columns: {sorted(required - set(source.columns))}")

    records = []
    for _, row in source.iterrows():
        record = {
            "binary_rescue_label": int(row["binary_label"]),
            "message_category": LABELS.get(row["multiclass_label"], "Unknown"),
        }
        tags = []
        for entity in ast.literal_eval(row["ner_label"] or "[]"):
            if isinstance(entity, (list, tuple)) and len(entity) == 3:
                tags.append(ENTITY_LABELS.get(str(entity[2]), "other"))
        for column in ENTITY_LABELS.values():
            record[f"{column}_count"] = tags.count(column)
        records.append(record)

    random.Random(2026).shuffle(records)
    for index, record in enumerate(records, start=1):
        record["sample_id"] = f"depremkit_sample_{index:04d}"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    columns = ["sample_id", "binary_rescue_label", "message_category"] + [f"{name}_count" for name in ENTITY_LABELS.values()]
    pd.DataFrame(records, columns=columns).to_csv(output_path, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source_tsv", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "depremkit_gold_anonymized.csv")
    arguments = parser.parse_args()
    prepare(arguments.source_tsv, arguments.output)
    print(f"Wrote anonymized label-only benchmark to {arguments.output}")

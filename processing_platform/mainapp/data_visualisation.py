# mainapp/data_visualisation.py
from __future__ import annotations

import re
from pathlib import Path
from collections import defaultdict
from datetime import date
from typing import Iterable, Tuple, List, Dict, Any

import pandas as pd
from django.db import transaction
from django.db.models import Avg, Q
from django.db.utils import NotSupportedError

from .models import ZonalStat, Field_visualisation

VARIABLES: List[str] = [
    "mean", "median", "std", "cv", "iqr", "kurtosis", "majority", "maximum",
    "minimum", "minority", "q25", "q75", "range_stat", "skewness", "sum_stat",
    "variance", "top_5_mean", "top_5_median", "top_5_std",
    "top_10", "top_10_mean", "top_10_median", "top_10_std",
    "top_15", "top_15_mean", "top_15_median", "top_15_std",
    "top_20",
    "top_25", "top_25_mean", "top_25_median", "top_25_std",
    "top_35", "top_35_mean", "top_35_median", "top_35_std",
    "top_50", "top_50_mean", "top_50_median", "top_50_std",
]

_COLMAP: Dict[str, str] = {
    "id": "idx", "location": "location", "camera": "camera", "flight_height": "flight_height",
    "project": "project", "flight": "flight", "date": "date", "spectrum": "spectrum",
    "count": "count", "cv": "cv", "iqr": "iqr", "kurtosis": "kurtosis", "majority": "majority",
    "max": "maximum", "mean": "mean", "median": "median", "min": "minimum",
    "minority": "minority", "q25": "q25", "q75": "q75", "range": "range_stat",
    "skewness": "skewness", "std": "std", "sum": "sum_stat",
    "top_10": "top_10", "top_10_mean": "top_10_mean", "top_10_median": "top_10_median", "top_10_std": "top_10_std",
    "top_15": "top_15", "top_15_mean": "top_15_mean", "top_15_median": "top_15_median", "top_15_std": "top_15_std",
    "top_20": "top_20",
    "top_25": "top_25", "top_25_mean": "top_25_mean", "top_25_median": "top_25_median", "top_25_std": "top_25_std",
    "top_35": "top_35", "top_35_mean": "top_35_mean", "top_35_median": "top_35_median", "top_35_std": "top_35_std",
    "top_50": "top_50", "top_50_mean": "top_50_mean", "top_50_median": "top_50_median", "top_50_std": "top_50_std",
    "top_5_mean": "top_5_mean", "top_5_median": "top_5_median", "top_5_std": "top_5_std",
    "variance": "variance", "variety": "variety",
}

_NUMERIC_TARGETS = set(_COLMAP.values()) - {"idx", "count", "variety", "date", "location", "camera", "spectrum", "project"}
_INT_COLUMNS = {"idx", "count", "variety"}

def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns
        .str.strip()
        .str.replace(r"\s+", "_", regex=True)
        .str.replace(r"[^\w]+", "_", regex=True)
        .str.lower()
    )
    return df
@transaction.atomic
def import_excel_to_db(file) -> Tuple[int, int]:
    df = pd.read_excel(file)
    df = _clean_columns(df)

    missing = [c for c in _COLMAP.keys() if c not in df.columns]
    if missing:
        raise ValueError(f"Mangler kolonner i Excel: {', '.join(sorted(missing))}")

    df = df.rename(columns=_COLMAP)

    for col in ["location", "camera", "project", "flight", "spectrum", "flight_height"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date

    for col in _NUMERIC_TARGETS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors="coerce")

    for col in _INT_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # map project -> Field_visualisation.id
    unique_projects = sorted(df["project"].dropna().astype(str).str.strip().unique())
    existing = dict(Field_visualisation.objects.filter(name__in=unique_projects).values_list("name", "id"))
    to_create = [Field_visualisation(name=name) for name in unique_projects if name and name not in existing]
    if to_create:
        Field_visualisation.objects.bulk_create(to_create, ignore_conflicts=True)
        existing.update(dict(Field_visualisation.objects.filter(name__in=unique_projects).values_list("name", "id")))
    df["field_id"] = df["project"].map(existing).astype("Int64")

    # dropp rader uten nøkkelverdier
    df = df.dropna(subset=["date", "idx", "spectrum"])

    # dedupliser på unik-nøkkel (behold siste forekomst)
    df = df.drop_duplicates(subset=["date", "idx", "spectrum"], keep="last")

    # velg kolonner som matcher modellen
    cols_for_model = [c for c in df.columns if c in set(_COLMAP.values()) | {"field_id"}]

    # erstatt NaN/<NA> med None (Django liker None)
    df = df.where(pd.notna(df), None)

    records = df[cols_for_model].to_dict("records")
    objs = [ZonalStat(**rec) for rec in records]

    try:
        created = ZonalStat.objects.bulk_create(
            objs,
            batch_size=1000,
            update_conflicts=True,
            update_fields=[c for c in cols_for_model if c not in {"date", "idx", "spectrum", "field_id"}],
            unique_fields=["date", "idx", "spectrum"],
        )
        created_count = len(created)
        attempted = len(objs)
        updated_or_skipped = attempted - created_count
        return created_count, updated_or_skipped
    except NotSupportedError:
        created = ZonalStat.objects.bulk_create(objs, batch_size=1000, ignore_conflicts=True)
        return len(created), len(objs) - len(created)

def build_chart_data(start_date: date, end_date: date, field_name: str, specters: Iterable[str], variables: Iterable[str]):
    variables = [v for v in (variables or ["mean"]) if v in VARIABLES]

    base = Q(date__gte=start_date, date__lte=end_date)
    if specters:
        base &= Q(spectrum__in=list(specters))
    if field_name:
        base &= Q(field__name=field_name) | Q(location=field_name)

    annotations = {f"{v}_avg": Avg(v) for v in variables}
    qs = (
        ZonalStat.objects.filter(base)
        .values("date", "spectrum")
        .annotate(**annotations)
        .order_by("date", "spectrum")
    )

    vals: Dict[str, Dict[str, Dict[date, float | None]]] = {v: defaultdict(dict) for v in variables}
    dates: List[date] = []

    for row in qs:
        d, s = row["date"], row["spectrum"]
        dates.append(d)
        for v in variables:
            x = row[f"{v}_avg"]
            vals[v][s][d] = float(x) if x is not None else None

    labels = sorted(set(dates))
    specters_in_qs = sorted(set(r["spectrum"] for r in qs))
    use_specters = list(specters) if specters else specters_in_qs

    datasets = [
        {"label": f"{s} – {v}", "data": [vals[v].get(s, {}).get(d, None) for d in labels]}
        for s in use_specters for v in variables
    ]
    return {"labels": [d.isoformat() for d in labels], "datasets": datasets}, use_specters, variables
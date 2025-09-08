# mainapp/data_visualisation.py
from __future__ import annotations

from typing import Tuple, List, Dict, Any
import pandas as pd
from django.db import transaction
from django.db.utils import NotSupportedError
from django.db.models import Avg
from .models import ZonalStat, FieldVisualisation, Spectrum

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
    "id": "idx",
    "location": "location",
    "camera": "camera",
    "flight_height": "flight_height",
    "project": "project",
    "flight": "flight",
    "date": "date",
    "spectrum": "spectrum",
    "count": "count",
    "cv": "cv",
    "iqr": "iqr",
    "kurtosis": "kurtosis",
    "majority": "majority",
    "max": "maximum",
    "mean": "mean",
    "median": "median",
    "min": "minimum",
    "minority": "minority",
    "q25": "q25",
    "q75": "q75",
    "range": "range_stat",
    "skewness": "skewness",
    "std": "std",
    "sum": "sum_stat",
    "top_10": "top_10",
    "top_10_mean": "top_10_mean",
    "top_10_median": "top_10_median",
    "top_10_std": "top_10_std",
    "top_15": "top_15",
    "top_15_mean": "top_15_mean",
    "top_15_median": "top_15_median",
    "top_15_std": "top_15_std",
    "top_20": "top_20",
    "top_25": "top_25",
    "top_25_mean": "top_25_mean",
    "top_25_median": "top_25_median",
    "top_25_std": "top_25_std",
    "top_35": "top_35",
    "top_35_mean": "top_35_mean",
    "top_35_median": "top_35_median",
    "top_35_std": "top_35_std",
    "top_50": "top_50",
    "top_50_mean": "top_50_mean",
    "top_50_median": "top_50_median",
    "top_50_std": "top_50_std",
    "top_5_mean": "top_5_mean",
    "top_5_median": "top_5_median",
    "top_5_std": "top_5_std",
    "variance": "variance",
    "variety": "variety",
}

_NUMERIC = set(_COLMAP.values()) - {
    "idx", "count", "variety", "date",
    "location", "camera", "spectrum", "project", "flight", "flight_height",
}
_INTS = {"idx", "count", "variety"}


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize a DataFrame's column names for robust mapping.

    - Strips whitespace
    - Replaces internal whitespace with underscores
    - Replaces non-word characters with underscores
    - Lowercases everything

    Example:
      "Flight Height (m)" -> "flight_height_m"
    """
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
    """
    Import an Excel sheet into the database as ZonalStat rows, creating
    FieldVisualisation and Spectrum rows on demand.

    Pipeline
    --------
    1) Read Excel into a DataFrame and normalize headers (`_clean_columns`).
    2) Validate required columns via `_COLMAP`; rename to model fields.
    3) Normalize/parse:
         - Trim text fields, lowercase spectrum, to_date(date)
         - Convert numeric strings (supports comma decimal)
         - Coerce Int64 fields for `idx`, `count`, `variety`
    4) Create/lookup FieldVisualisation by project name.
    5) Create/lookup Spectrum per (field_id, spectrum name).
    6) Drop duplicates on (spectrum_id, date, idx).
    7) Bulk upsert ZonalStat rows:
         - Uses Postgres `update_conflicts=True` if available
         - Fallback: ignore_conflicts

    Returns
    -------
    (created_count, updated_or_duplicated_count)
    """
    df = pd.read_excel(file)
    df = _clean_columns(df)

    missing = [c for c in _COLMAP if c not in df.columns]
    if missing:
        raise ValueError(f"Mangler kolonner i Excel: {', '.join(sorted(missing))}")

    df = df.rename(columns=_COLMAP)
    for col in ["location", "camera", "project", "flight", "flight_height", "spectrum"]:
        df[col] = df[col].astype(str).str.strip()

    df["spectrum"] = df["spectrum"].str.lower()
    df["project"] = df["project"].str.strip()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date




    for col in _NUMERIC:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors="coerce")
    for col in _INTS:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    df = df.dropna(subset=["project", "date", "idx", "spectrum"])
    projects = sorted(df["project"].unique())
    existing_fields = dict(
        FieldVisualisation.objects.filter(name__in=projects).values_list("name", "id")
    )
    to_create_fields = [FieldVisualisation(name=p) for p in projects if p and p not in existing_fields]
    if to_create_fields:
        FieldVisualisation.objects.bulk_create(to_create_fields, ignore_conflicts=True)
        existing_fields.update(
            dict(FieldVisualisation.objects.filter(name__in=projects).values_list("name", "id"))
        )
    df["field_id"] = df["project"].map(existing_fields).astype("Int64")
    pairs = sorted(
        {
            (int(fid), s)
            for fid, s in df[["field_id", "spectrum"]].itertuples(index=False, name=None)
            if pd.notna(fid) and s
        }
    )

    existing_specs: Dict[tuple, int] = {
        (field_id, name): sid
        for field_id, name, sid in Spectrum.objects.filter(
            field_id__in=[p[0] for p in pairs],
            name__in=[p[1] for p in pairs],
        ).values_list("field_id", "name", "id")
    }

    to_create_specs = [
        Spectrum(field_id=field_id, name=name)
        for (field_id, name) in pairs
        if (field_id, name) not in existing_specs
    ]
    if to_create_specs:
        Spectrum.objects.bulk_create(to_create_specs, ignore_conflicts=True)
        existing_specs.update({
            (f, n): i for f, n, i in Spectrum.objects.filter(
                field_id__in=[p[0] for p in pairs],
                name__in=[p[1] for p in pairs],
            ).values_list("field_id", "name", "id")
        })
    df["spectrum_id"] = [
        existing_specs[(int(fid), s)]
        for fid, s in df[["field_id", "spectrum"]].itertuples(index=False, name=None)
    ]
    df = df.drop_duplicates(subset=["spectrum_id", "date", "idx"], keep="last")

    allowed = (set(_COLMAP.values()) | {"spectrum_id"}) - {"spectrum"}  
    keep_cols = [c for c in df.columns if c in allowed]

    df = df.where(pd.notna(df), None)
    records = df[keep_cols].to_dict("records")
    objs = [ZonalStat(**rec) for rec in records]

    try:
        created = ZonalStat.objects.bulk_create(
            objs,
            batch_size=1000,
            update_conflicts=True,
            unique_fields=["date", "idx", "spectrum"],
            update_fields=[c for c in keep_cols if c not in {"spectrum_id", "date", "idx"}],
        )
        created_count = len(created)
        attempted = len(objs)
        return created_count, attempted - created_count
    except NotSupportedError:
        created = ZonalStat.objects.bulk_create(objs, batch_size=1000, ignore_conflicts=True)
        return len(created), len(objs) - len(created)


def build_chart_data(
    start_date, end_date, field_name: str, specters_req: list[str], variables_req: list[str]
):
    """
    Build box-plot friendly data from raw ZonalStat rows.

    Output structure (consumed by the frontend)
    -------------------------------------------
    {
      "dates": ["YYYY-MM-DD", ...],                 # unique sorted dates present in the result
      "series": [
        {
          "name": "<specter> · <variable>",         # e.g. "green · mean"
          "data": [                                  # aligns with 'dates' by index
            [v1, v2, ...],                           # all raw values for that date (no aggregation)
            [],
            ...
          ]
        },
        ...
      ]
    }

    Notes
    -----
    - Accepts multiple variables and multiple specters; creates one series per (specter × variable).
    - Returns raw values grouped per date to let the frontend compute box plots directly.
    """
    wanted_vars = [v for v in (variables_req or []) if v in VARIABLES]
    if not wanted_vars:
        wanted_vars = ["mean"]

    qs = (
        ZonalStat.objects
        .filter(date__gte=start_date, date__lte=end_date)
        .select_related("spectrum", "spectrum__field")
    )
    if field_name:
        qs = qs.filter(spectrum__field__name=field_name)

    available = [
        (s or "").strip().lower()
        for s in qs.values_list("spectrum__name", flat=True).distinct()
        if s
    ]
    if specters_req:
        specters = [s.strip().lower() for s in specters_req if s.strip().lower() in available]
    else:
        specters = sorted(available)

    if not specters:
        return {"dates": [], "series": []}, [], wanted_vars

    qs = qs.filter(spectrum__name__in=specters)
    fields = ["date", "spectrum__name"] + wanted_vars
    rows = qs.values(*fields).order_by("date")

    dates_set = {r["date"] for r in rows}
    dates = sorted(dates_set)
    labels = [d.isoformat() for d in dates]
    date_idx = {d: i for i, d in enumerate(dates)}

    series = []
    series_map = {}  
    for sp in specters:
        for v in wanted_vars:
            name = f"{sp} · {v}"
            series_map[(sp, v)] = len(series)
            series.append({"name": name, "data": [[] for _ in labels]})
    for r in rows:
        d = r["date"]
        sp = (r["spectrum__name"] or "").strip().lower()
        if d not in date_idx or sp not in specters:
            continue
        i = date_idx[d]
        for v in wanted_vars:
            val = r.get(v, None)
            if val is None:
                continue
            try:
                val = float(val)
            except Exception:
                continue
            series[series_map[(sp, v)]]["data"][i].append(val)

    return {"dates": labels, "series": series}, specters, wanted_vars

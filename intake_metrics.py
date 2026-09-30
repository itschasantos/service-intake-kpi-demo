"""Pure intake normalization and KPI calculations for the portfolio demonstration."""

from __future__ import annotations

from datetime import datetime, timezone
from numbers import Number
from typing import Any, Iterable

import pandas as pd


APPLICATION_COLUMNS = [
    "id",
    "uuid",
    "referenceNumber",
    "statusId",
    "source",
    "othersource",
    "region",
    "otherRegion",
    "intakeType",
    "applicationType",
    "createdOn",
    "modifiedOn",
    "initialServicesIsDone",
    "insuranceAuthorized",
    "assementScheduled",  # Spelling follows the supplied generic intake schema.
    "legallyAuthorized",
    "approved",
    "proceedWithService",
    "waitlisted",
    "lostopportunity",
    "onboardingCompleted",
]

TRUE_VALUES = {"1", "true", "yes", "y", "t"}


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    if isinstance(value, Number):
        return float(value) != 0
    return str(value).strip().lower() in TRUE_VALUES


def records_from_payload(payload: Any) -> list[dict[str, Any]]:
    """Accept common generic intake Web API response envelopes without assuming one beta contract."""
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []

    for key in ("data", "records", "items", "results", "value"):
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
        if isinstance(value, dict):
            nested = records_from_payload(value)
            if nested:
                return nested
    return []


def _text(value: Any, fallback: str = "Unknown") -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return fallback
    text = str(value).strip()
    return text or fallback


def derive_stage(row: pd.Series) -> str:
    """Derive a small, ordered intake funnel from application fields."""
    if as_bool(row.get("lostopportunity")):
        return "Lost opportunity"
    if as_bool(row.get("onboardingCompleted")):
        return "Onboarding complete"
    if as_bool(row.get("waitlisted")):
        return "Waitlisted"
    if as_bool(row.get("approved")) or as_bool(row.get("legallyAuthorized")):
        return "Approved / authorized"
    if as_bool(row.get("assementScheduled")):
        return "Assessment scheduled"
    if as_bool(row.get("insuranceAuthorized")):
        return "Insurance authorized"
    if as_bool(row.get("initialServicesIsDone")):
        return "Initial services complete"
    return "Application received"


def normalize_applications(records: Iterable[dict[str, Any]], now: datetime | None = None) -> pd.DataFrame:
    now = now or datetime.now(timezone.utc)
    frame = pd.DataFrame(list(records))
    if not frame.empty:
        # SQL drivers may alter identifier case. Restore supplied generic intake field names.
        canonical = {"".join(char for char in name.lower() if char.isalnum()): name for name in APPLICATION_COLUMNS}
        renames = {}
        for column in frame.columns:
            normalized = "".join(char for char in str(column).lower() if char.isalnum())
            if normalized in canonical:
                renames[column] = canonical[normalized]
        frame = frame.rename(columns=renames)
    if frame.empty:
        frame = pd.DataFrame(columns=APPLICATION_COLUMNS)
    for column in APPLICATION_COLUMNS:
        if column not in frame.columns:
            frame[column] = None

    frame = frame[APPLICATION_COLUMNS].copy()
    frame["createdOn"] = pd.to_datetime(frame["createdOn"], errors="coerce", utc=True)
    frame["modifiedOn"] = pd.to_datetime(frame["modifiedOn"], errors="coerce", utc=True)
    frame["region_display"] = frame.apply(
        lambda row: _text(row.get("region"), _text(row.get("otherRegion"))), axis=1
    )
    frame["source_display"] = frame.apply(
        lambda row: _text(row.get("source"), _text(row.get("othersource"))), axis=1
    )
    frame["stage"] = frame.apply(derive_stage, axis=1)
    frame["is_open"] = ~frame["stage"].isin(["Lost opportunity", "Onboarding complete"])
    frame["proceeding"] = frame["proceedWithService"].map(as_bool)
    frame["waitlisted_flag"] = frame["waitlisted"].map(as_bool)
    now_ts = pd.Timestamp(now)
    frame["age_days"] = (now_ts - frame["createdOn"]).dt.total_seconds().div(86400).clip(lower=0)
    frame["referenceNumber"] = frame["referenceNumber"].map(lambda value: _text(value, "Unassigned"))
    return frame


def filter_applications(
    frame: pd.DataFrame,
    start_date: str | None = None,
    end_date: str | None = None,
    region: str = "All",
) -> pd.DataFrame:
    filtered = frame.copy()
    if start_date:
        filtered = filtered[filtered["createdOn"] >= pd.Timestamp(start_date, tz="UTC")]
    if end_date:
        filtered = filtered[filtered["createdOn"] < pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)]
    if region and region != "All":
        filtered = filtered[filtered["region_display"] == region]
    return filtered


def summary_metrics(frame: pd.DataFrame) -> dict[str, float | int | None]:
    total = int(len(frame))
    open_count = int(frame["is_open"].sum()) if total else 0
    proceed_rate = round(float(frame["proceeding"].mean() * 100), 1) if total else None
    waitlisted = int(frame["waitlisted_flag"].sum()) if total else 0
    median_open_age = frame.loc[frame["is_open"], "age_days"].median() if total else None
    return {
        "applications": total,
        "open_intakes": open_count,
        "proceed_rate": proceed_rate,
        "waitlisted": waitlisted,
        "median_open_age": round(float(median_open_age), 1) if pd.notna(median_open_age) else None,
    }

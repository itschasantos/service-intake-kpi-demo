from datetime import datetime, timezone
from intake_metrics import normalize_applications, summary_metrics

# Entirely fabricated records; no real client or organization data.
records = [
    {"id": 1, "referenceNumber": "DEMO-001", "region": "Region A", "createdOn": "2026-01-01", "insuranceAuthorized": True, "proceedWithService": True},
    {"id": 2, "referenceNumber": "DEMO-002", "region": "Region B", "createdOn": "2026-01-05", "onboardingCompleted": True, "proceedWithService": True},
    {"id": 3, "referenceNumber": "DEMO-003", "region": "Region A", "createdOn": "2026-01-08", "waitlisted": True},
    {"id": 4, "referenceNumber": "DEMO-004", "region": "Region B", "createdOn": "2026-01-10", "lostopportunity": True},
]
frame = normalize_applications(records, now=datetime(2026, 1, 15, tzinfo=timezone.utc))
metrics = summary_metrics(frame)
assert metrics["applications"] == 4
assert metrics["open_intakes"] == 2
assert metrics["waitlisted"] == 1
assert metrics["proceed_rate"] == 50.0
assert metrics["median_open_age"] == 10.5
print(metrics)

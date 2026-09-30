# Service Intake KPI Demo

Adapted from existing intake normalization and KPI work. Handles mixed boolean values, funnel precedence, open intake age, and summary rates. The demonstration uses fabricated records and no live integrations. Schema names are generalized; the original assessment-field spelling is retained for compatibility. This presents calculation logic, not the full workplace dashboard.

## Run

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python demo.py
```

## Privacy and provenance

The calculation functions were extracted from prior operational projects; the demo and assertions were added for this portfolio. Original records, notebook outputs, credentials, endpoints, branding, and source documents are excluded. All example records are synthetic. Source files remain untouched. No organization performance claims are made.

No license is assigned pending confirmation of rights to redistribute the original work.

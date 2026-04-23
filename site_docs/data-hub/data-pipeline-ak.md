# data_pipeline_ak

`data_pipeline_ak` is the AkShare helper context inside `data_hub`.

## Current Scope

- provide AkShare-side import capability
- keep a lightweight fallback and extension point for data that does not belong in the TuShare runner
- currently focus on calendar-related imports

## Current Layout

- `apps/data_hub/data_pipeline_ak/calendar.py`
- `apps/data_hub/data_pipeline_ak/fetchers/calendar.py`
- `apps/data_hub/data_pipeline_ak/provider/client.py`
- `apps/data_hub/data_pipeline_ak/tests/test_calendar.py`

## Notes

This context is intentionally smaller than `data_pipeline_ts`. The current repo-level docs should describe it as an AkShare support module rather than a second full production scheduler.

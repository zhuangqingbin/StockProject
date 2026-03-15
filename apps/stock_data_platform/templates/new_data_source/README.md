# new data source template

Use these files when a notebook probe is ready to become a maintained source.

## Files

- `fetcher.py.template`
  - skeleton for a new `BaseDataFetch` implementation
- `daily_job.yaml.template`
  - skeleton for the new `daily_jobs.yaml` entry
- `test_fetcher.py.template`
  - skeleton for the fetcher or job regression test

## Intended flow

1. Validate the upstream source in `apps/stock_data_platform/notebooks/10_new_source_probe.ipynb`.
2. Copy the templates into the maintained runtime locations.
3. Replace placeholders with the real source name, table names, and fields.
4. Add the new job to `apps/stock_data_platform/jobs/daily_jobs.yaml`.
5. Add tests before enabling the source in scheduled runs.

from __future__ import annotations

from collections.abc import Mapping, Sequence

from apps.data_hub.data_pipeline_ts.jobs.catalog import ALL_JOBS, INFRASTRUCTURE_TARGETS
from apps.data_hub.data_pipeline_ts.jobs.specs import InfrastructureSpec, JobSpec


def _parse_csv_values(raw_values: str | None) -> list[str] | None:
    if not raw_values:
        return None
    values = [value.strip() for value in raw_values.split(",") if value.strip()]
    return values or None


def select_job_specs(
    job_specs: Sequence[JobSpec] | None = None,
    *,
    job_names: Sequence[str] | None = None,
    profiles: Sequence[str] | None = None,
) -> list[JobSpec]:
    available_specs = list(job_specs or ALL_JOBS)
    available_names = {spec.name for spec in available_specs}
    available_profiles = {spec.profile.value for spec in available_specs}

    selected_names = set(job_names or ())
    if selected_names:
        unknown_names = sorted(selected_names - available_names)
        if unknown_names:
            raise ValueError(f"Unknown job names: {', '.join(unknown_names)}")

    selected_profiles = set(profiles or ())
    if selected_profiles:
        unknown_profiles = sorted(selected_profiles - available_profiles)
        if unknown_profiles:
            raise ValueError(f"Unknown profiles: {', '.join(unknown_profiles)}")

    return [
        spec
        for spec in available_specs
        if (not selected_names or spec.name in selected_names)
        and (not selected_profiles or spec.profile.value in selected_profiles)
    ]


def select_infrastructure_specs(
    target_names: Sequence[str],
    *,
    infrastructure_specs: Mapping[str, InfrastructureSpec] | None = None,
) -> list[InfrastructureSpec]:
    available_specs = dict(infrastructure_specs or INFRASTRUCTURE_TARGETS)
    requested_names = [name for name in target_names if name]
    unknown_names = sorted(set(requested_names) - set(available_specs))
    if unknown_names:
        raise ValueError(f"Unknown infrastructure targets: {', '.join(unknown_names)}")
    return [available_specs[name] for name in requested_names]

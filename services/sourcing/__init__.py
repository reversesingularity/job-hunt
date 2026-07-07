"""Sourcing layer — API-first job ingestion."""

from services.sourcing.sources import (  # noqa: F401
    dedupe,
    from_adzuna,
    from_ashby,
    from_greenhouse,
    from_lever,
    gather_all,
)

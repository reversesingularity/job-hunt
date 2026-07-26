# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| `main` branch | Yes |

## Reporting a vulnerability

If you discover a security issue in this repository:

1. **Do not** open a public issue for credential leaks or exploit details
2. Contact the repository owner privately via GitHub Security Advisories or direct message
3. Include steps to reproduce and affected paths

## Secrets and credentials

Never commit:

- `.env` or any file containing API keys
- `data/master_cv.json` (personal fact bank)
- MotherDuck tokens, OpenAI keys, Adzuna credentials
- Database files with real application history (`jobhunt.db`)

Use `.env.example` as the template for required variable names only.

## Crown Copyright and government emblems (DE&I PMO)

OIA-2025-5483 reference PDFs under `dei-pmo-dashboard/docs/oia-reference/` are public/unclassified but remain **© Crown Copyright**. When displaying them (or framing the DE&I demo against that public release):

1. Keep the OIA attribution caption visible
2. Do not use NZDF logos or the NZ Government coat of arms in a way that implies official endorsement
3. Do not treat Crown PDFs as MIT-licensed application code

See [GOVERNANCE.md](GOVERNANCE.md) for the full security-vs-copyright policy.

Live demo: https://dei-pmo.reversesingularity.com

## Scraping and automation

Phase 2 stealth/apply features must not:

- Authenticate as the user on third-party sites without explicit consent
- Circumvent rate limits or access controls on non-public endpoints
- Submit applications without human approval when `REQUIRE_APPROVAL=true`

## Dependency updates

Keep `pip install -e ".[dev]"` and dashboard `requirements.txt` files current. Review supply-chain changes for sourcing and browser automation packages before merging.

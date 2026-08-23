# PUBLIC ARTIFACT — conrrad-citizen 0.4.2

> Historical P0.2C record. This file describes Wheel B (`0dbb7d…`),
> which is **not canonical**. Canonical Wheel A is documented in
> `CANONICAL_ARTIFACT_0_4_2.md`.

## Package
- PACKAGE=conrrad-citizen
- PACKAGE_VERSION=0.4.2
- WHEEL=conrrad_citizen-0.4.2-py3-none-any.whl

## Provenance
- SOURCE_REPOSITORY=GRECOITALICO/CONRRAD-CITIZEN
- SOURCE_BRANCH=p0/citizen-consolidation
- SOURCE_COMMIT=19c30a5522815dadb9fb6a9d6f68fbac7b3f6074
- BUILD_COMMIT=19c30a5522815dadb9fb6a9d6f68fbac7b3f6074
- SOURCE_COMMIT_VERIFIED=TRUE (wheel SOURCE_COMMIT == BUILD_COMMIT)

## Public distribution
- PYPI_STATUS=BLOCKED (403 Forbidden — invalid/non-existent token; 0.4.1 remains latest on PyPI)
- GITHUB_RELEASE_STATUS=PUBLISHED
- PUBLIC_DOWNLOAD_URL=https://github.com/GRECOITALICO/citizen/releases/download/conrrad-citizen-0.4.2/conrrad_citizen-0.4.2-py3-none-any.whl
- RELEASE_PAGE=https://github.com/GRECOITALICO/citizen/releases/tag/conrrad-citizen-0.4.2
- ARTIFACT_SHA256=0dbb7d46958575759ea90122dc38177066f812210c2496572ec35e1d8280e65c
- ARTIFACT_SHA256_VERIFIED=TRUE (anonymous curl; no gh auth)

## Note on prior P0.2B hash
The earlier private-release wheel hash
`0b4eb6d336352901e783f747bc5f2cc1775f0822ec1be17c145143ea6a4457ce`
stamped SOURCE_COMMIT=73b291645 while built from tip 19c30a552 (stamp-only delta).
This public rebuild stamps SOURCE_COMMIT == BUILD_COMMIT; therefore SHA256 differs by design.

## Installer
- PUBLIC_INSTALLER=TRUE
- install.sh downloads the public Release URL
- install.sh verifies EXPECTED_SHA256 before pip install
- No gh auth / private repo credentials required

## Clean verification (anonymous artifact)
- ANONYMOUS_DOWNLOAD=TRUE
- CLEAN_INSTALL=TRUE
- CLEAN_SERVE=TRUE
- PUBLIC_CLI=TRUE (`citizen` console_script from wheel)
- PUBLIC_SERVER=TRUE (`citizen serve` → living_server)
- PUBLIC_API_WORK=TRUE (POST /api/work)
- PUBLIC_UI_WORK=TRUE (RUN WORK → POST /api/work)
- INSTALLED_WORK=TRUE
- EVIDENCE=TRUE (event_type work_result)
- HISTORY=TRUE (ops/canonical_work_history.jsonl)
- IDENTITY=TRUE (citizen_id unchanged across routes)

## Gate
- P0_2C_COMPLETE=TRUE

# PUBLIC ARTIFACT RETRIEVAL — conrrad-citizen 0.4.2 (P0.2D)

> Historical P0.2D record. This file describes Wheel B (`0dbb7d…`),
> which is **not canonical**. Canonical Wheel A is documented in
> `CANONICAL_ARTIFACT_0_4_2.md`.

## Artifact
- PACKAGE=conrrad-citizen
- PACKAGE_VERSION=0.4.2
- FILENAME=conrrad_citizen-0.4.2-py3-none-any.whl
- SHA256=0dbb7d46958575759ea90122dc38177066f812210c2496572ec35e1d8280e65c

## Source provenance (inside wheel)
- SOURCE_REPOSITORY=GRECOITALICO/CONRRAD-CITIZEN
- SOURCE_BRANCH=p0/citizen-consolidation
- SOURCE_COMMIT=19c30a5522815dadb9fb6a9d6f68fbac7b3f6074
- SOURCE_COMMIT_VERIFIED=TRUE

## Public URL (anonymous, no redirect)
- PUBLIC_URL=https://raw.githubusercontent.com/GRECOITALICO/citizen/artifact-conrrad-citizen-0.4.2/release/0.4.2/conrrad_citizen-0.4.2-py3-none-any.whl
- IMMUTABLE_TAG=artifact-conrrad-citizen-0.4.2
- TREE_PATH=release/0.4.2/conrrad_citizen-0.4.2-py3-none-any.whl
- HTTP_STATUS=200
- CONTENT_LENGTH=102162
- DOWNLOAD_ANONYMOUS=TRUE
- REDIRECT_FOLLOW_REQUIRED=FALSE

## Why not GitHub Release download URL
- RELEASE_URL=https://github.com/GRECOITALICO/citizen/releases/download/conrrad-citizen-0.4.2/conrrad_citizen-0.4.2-py3-none-any.whl
- RELEASE_NO_FOLLOW_STATUS=302 (body empty without redirect follow)
- Release asset remains published for browsers/`curl -L`, but is not the auditor channel.

## Installer
- INSTALLER=https://raw.githubusercontent.com/GRECOITALICO/citizen/main/install.sh
- INSTALLER_UPDATED=TRUE (raw tagged URL + valid wheel temp filename)
- INSTALLER_SHA_VERIFICATION=TRUE
- INSTALLER_SOURCE_COMMIT_VERIFICATION=TRUE

## Clean verification
- CLEAN_INSTALL=TRUE (downloaded wheel only; no PYTHONPATH / no editable source)
- PUBLIC_CLI_WORK=TRUE (`citizen work --capability evidence.integrity_digest`)
- PUBLIC_API_WORK=TRUE (`POST /api/work`)
- PUBLIC_UI_WORK=TRUE (UI exposes RUN WORK; same `POST /api/work`)
- EVIDENCE=TRUE (`event_type=work_result`)
- HISTORY=TRUE (`ops/canonical_work_history.jsonl`)
- IDENTITY=TRUE (`citizen_id` stable across CLI/API/UI)

## Gate
- P0_2D_COMPLETE=TRUE
- NEXT_ACTION=PENSADOR_REAUDIT_PUBLIC_ARTIFACT

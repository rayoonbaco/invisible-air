# SV2-14 — Observation Evidence Contract

SV2-14 gives the scene a provider-neutral observation manifest before any external product geometry is ingested.

## Contract fields

- observation ID
- provider
- product type
- reported UTC time
- reported coordinates
- source URL
- retrieval UTC time
- geometry status
- quantification status
- confidence status
- missing-field list
- claim class and boundary

## Default behavior

The current case remains a source seed with an incomplete manifest. Missing fields are shown explicitly. The app does not invent a provider, source URL, timestamp, retrieval date, geometry, confidence, or quantified emissions result.

## Optional environment inputs

`AW_OBSERVATION_ID`, `AW_OBSERVATION_PROVIDER`, `AW_OBSERVATION_PRODUCT_TYPE`, `AW_OBSERVATION_TIME_UTC`, `AW_OBSERVATION_LAT`, `AW_OBSERVATION_LON`, `AW_OBSERVATION_SOURCE_URL`, `AW_OBSERVATION_RETRIEVED_AT_UTC`, `AW_OBSERVATION_GEOMETRY_STATUS`, `AW_OBSERVATION_QUANTIFICATION_STATUS`, and `AW_OBSERVATION_CONFIDENCE_STATUS`.

## Boundary

The observation contract is a provenance container. It is not itself methane detection, exact plume geometry, source attribution, emissions quantification, persistence evidence, or an enforcement finding.

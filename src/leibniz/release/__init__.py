"""Release stage — Parquet dataset + model exports.

Packages the deliverables (SPECS §2): D1 inventory (CC0), D2 transcriptions
(CC BY, provenance columns mandatory, NC bucket excluded), D3 GT (CC BY, open
bucket only), plus the v2 model bundle and dataset/model cards. Every export
carries the full provenance schema per row (SPECS §4.5) and the
anti-contamination note "machine output — do not ingest as verified text".
Upload steps are operator actions gated on the lawyer memo (SPECS §7.5).

Implemented in Phase D3.
"""

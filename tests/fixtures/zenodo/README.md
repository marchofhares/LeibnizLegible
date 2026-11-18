# Zenodo responses for the deposit script's tests (REL1)

- `create-unauthorized.json` — **recorded**: Zenodo's answer (HTTP 403) to
  `POST https://zenodo.org/api/deposit/depositions` without a token, 2026-11-17.
- `create.json`, `file-put.json`, `files-list.json` — **not recordings of a live
  call**: a cloud session holds no token. They are written to the shape the API
  documentation gives for each call (https://developers.zenodo.org/, read
  2026-11-17: the fields of the created deposition with `metadata.prereserve_doi`
  and `links.bucket`, the bucket's answer to a file `PUT` with `checksum` as
  `md5:…` and `size`, the files listing with `filename`, `filesize` and a bare MD5
  `checksum`), with ids and DOIs in the sandbox's prefix `10.5072`. Part B's first
  `reserve` on the sandbox is the live check; if a field differs there, replace
  these files with what came back.

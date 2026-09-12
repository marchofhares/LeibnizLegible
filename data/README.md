# `data/` — the working store (never committed)

Everything under `data/` is **generated or downloaded** and is **git-ignored**.
The repository is the memory of the *code and decisions*; the bulk data is
reproducible from the pipeline and the upstream sources. Only this `README.md`
and `.gitkeep` are tracked (they keep the directory present on a fresh clone).

Why it's excluded (SPECS §7, §10):

- **Size.** Image derivatives alone are an estimated ~200–400 GB.
- **Provenance.** Images are GWLB's (Public Domain Mark 1.0) and are loaded
  from GWLB's IIIF endpoints at serve time — we never rehost them.
- **Licensing.** NC-bucket derived text (Transkriptionspool etc.) lives here
  for internal TDM use only and must never leak into a CC BY release or the
  public UI.

## What lands here (created by later phases)

| Path                     | Written by | Contents                                             |
| ------------------------ | ---------- | ---------------------------------------------------- |
| `data/inventory.sqlite`  | A0+        | Canonical SQLite store (works, pages, lines, …)      |
| `data/oai/`              | A1         | Raw OAI-PMH METS/MODS XML, per set (cache-first)     |
| `data/manifests/`        | A1         | Cached IIIF Presentation manifests                   |
| `data/images/`           | A2         | Page image derivatives `{object_id}/{canvas_seq}.jpg`|
| `data/katalog/`          | A3         | Cached BBAW Ritter-Katalog HTML / TELOTA dump        |
| `data/models/`           | B1, C3     | HTR + segmentation model artifacts                   |
| `data/editions/`         | C2         | §70 volume text layers (IA hOCR, GWLB/Potsdam PDFs) + extracted piece texts |
| `data/gt/`               | B1, C2     | Ground-truth line/image pairs; `edition_cache.json` (record → reading text) |

## Rebuilding

Nothing here is precious. Delete a subtree and re-run the relevant stage; all
harvesting is cache-first and resumable, so re-fetches only pull what's missing.

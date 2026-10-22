# Arbeitskatalog fixtures (Phase A3b)

A cut of the Arbeitskatalog der Leibniz-Edition as the Leibniz-Edition Potsdam
exported it from its Access database on 19 October 2026 and provided it on 21
October (CSV via mdbtools), at
most thirty rows per table, chosen for the cases the mapping must get right:
the three records of the July 2026 scrape (33, 342), the Monadologie (LH 4, 1,
1a and 1b: 54786, 55406, 55407), the two records on LH 4, 6, 18 (41800, 59095),
a Marginalien record linked by PPN (1585), records with a double date, a
series-only Akademie-Ausgabe cell, a printed witness, a Landesarchiv link,
excerpts with a Wortlaut and an Ordnungsvermerk, and holdings in Göttingen,
Paris and Kopenhagen.

`pers_norm.csv` holds the persons-table rows of the names these records carry
(the website's "(KorrespDB)" and "(GND)" link markers come from it).
`site_records_live.json` holds 23 of these records as the website parser
(`leibniz.catalog.scrape.parse_result_table`) read them from the catalogue's
extended search on 21 October 2026 — the values the store's records carry —
so the mapping is tested against the website's own rendering.

Data from the Arbeitskatalog der Leibniz-Edition (Ritter-Katalog),
Berlin-Brandenburgische Akademie der Wissenschaften (Leibniz-Edition Potsdam I
/ TELOTA), https://leibniz-katalog.bbaw.de/ — licensed CC BY 4.0; the export
itself under the same licence, stated in writing by the head of the
Arbeitsstelle on 12 October 2026.

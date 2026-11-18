# Fixtures for R1 (decoding and the language models)

`edition_cache.jsonl` is a nine-record edition cache in the shape
`leibniz align edition-cache` writes (`record_id`, `text`, `refs` with the
printed piece and its channel), made for `tests/test_htr_lm.py` and the toy
model of R1 Part A. The record ids `k-109`, `k-4101` and `k-4402` are the
pieces of the fixture store (`tests/conftest.py`); the others exist only here.
The texts are a few sentences in 17th-century Latin, French and German
written for the tests (stock phrases of the kind the stopword lists place);
they are not edition text and no number counted on them says anything about
the Nachlass.

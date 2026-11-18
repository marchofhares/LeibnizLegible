"""The decoders behind one interface (R1 Task 1): synthetic softmax matrices.

Everything here runs in plain Python; the tests of flashlight-text, kenlm and
kraken itself skip where the optional stacks are absent.
"""

from __future__ import annotations

import io
import math
from types import SimpleNamespace

import pytest

from leibniz.htr import decoding as D

CHARS = [" ", "d", "o", "q", "u", "v", "e", "s", "t", " "]
TABLE = D.TokenTable.from_chars(CHARS)
LAB = {ch: i + 1 for i, ch in enumerate(CHARS)}

# A hand-made 3-gram: after q comes u, not v (log10 probabilities, ARPA).
ARPA = """\\data\\
ngram 1=11
ngram 2=4
ngram 3=1

\\1-grams:
-2.0\t<unk>
0\t<s>\t-0.3
-1.0\t</s>
-1.0\t<space>\t-0.3
-1.0\tq\t-0.3
-1.0\tu\t-0.3
-1.5\tv\t-0.3
-1.0\to\t-0.3
-1.0\td\t-0.3
-1.0\te\t-0.3
-1.0\ts\t-0.3

\\2-grams:
-0.3\t<s> q\t-0.2
-0.05\tq u\t-0.2
-2.5\tq v
-0.4\tu o\t-0.1

\\3-grams:
-0.05\tq u o

\\end\\
"""


def frame(dist: dict[str | None, float]) -> list[float]:
    """One frame: the named labels' posteriors (``None`` is the blank), the rest of
    the mass spread evenly over the other labels."""
    n = len(TABLE)
    named = {(0 if k is None else LAB[k]): v for k, v in dist.items()}
    rest = (1.0 - sum(named.values())) / (n - len(named))
    return [named.get(i, rest) for i in range(n)]


def peaked(text: str, *, p: float = 0.97, hold: int = 2) -> list[list[float]]:
    """A peaked posterior for ``text``: every character held ``hold`` frames, a blank
    after each."""
    frames = []
    for ch in text:
        frames.extend(frame({ch: p}) for _ in range(hold))
        frames.append(frame({None: p}))
    return frames


def as_cw(frames: list[list[float]]) -> list[list[float]]:
    """kraken's layout of one line: labels × frames."""
    return [list(col) for col in zip(*frames, strict=True)]


@pytest.fixture
def arpa_path(tmp_path):
    p = tmp_path / "hand.arpa"
    p.write_text(ARPA, encoding="utf-8")
    return p


def near_tie() -> list[list[float]]:
    """q, then u at 0.46 against v at 0.50, then o, d: greedy reads ``qvod``."""
    frames = peaked("q")
    frames += [frame({"u": 0.46, "v": 0.50}), frame({"u": 0.46, "v": 0.50}), frame({None: 0.97})]
    frames += peaked("od")
    return frames


# --------------------------------------------------------------------------- #
# greedy: today's behaviour
# --------------------------------------------------------------------------- #


def test_greedy_reads_runs_and_keeps_the_highest_posterior_of_each():
    frames = [
        frame({"q": 0.6}),
        frame({"q": 0.9}),
        frame({None: 0.8}),
        frame({"u": 0.7}),
        frame({"u": 0.5}),
        frame({"o": 0.95}),
        frame({None: 0.9}),
    ]
    res = D.decode_greedy(frames, TABLE)
    assert res.text == "quo"
    assert res.labels == [LAB["q"], LAB["u"], LAB["o"]]
    assert res.spans == [(0, 1), (3, 4), (5, 5)]
    assert res.char_scores == pytest.approx([0.9, 0.7, 0.95])
    assert res.score == pytest.approx(sum(math.log(max(f)) for f in frames))
    assert res.as_kraken()[0] == (LAB["q"], 0, 1, pytest.approx(0.9))
    assert res.as_tuple()[0] == "quo"
    # the confidence is the mean per-character posterior (SPECS §4.5)
    assert D.line_confidence(res) == pytest.approx((0.9 + 0.7 + 0.95) / 3)


def test_greedy_repeats_need_a_blank_between_and_an_empty_line_has_no_confidence():
    frames = [frame({"o": 0.9}), frame({None: 0.9}), frame({"o": 0.8}), frame({"o": 0.85})]
    assert D.decode_greedy(frames, TABLE).text == "oo"
    blank = D.decode_greedy([frame({None: 0.99})] * 4, TABLE)
    assert blank.text == "" and blank.char_scores == []
    assert D.line_confidence(blank) is None
    assert D.line_confidence(None) is None
    assert D.line_confidence([0.5, 1.0]) == 0.75


def test_greedy_equals_krakens_own_decoder_on_random_matrices():
    torch = pytest.importorskip("torch")
    ctc = pytest.importorskip("kraken.lib.ctc_decoder")
    gen = torch.Generator().manual_seed(20261117)
    for n_labels, width in ((12, 40), (30, 75), (5, 9)):
        out = torch.softmax(4.0 * torch.randn(n_labels, width, generator=gen), dim=0)
        theirs = ctc.greedy_decoder(out)[0]
        ours = D.Decoder(D.GREEDY)(out)[0]
        assert ours == theirs  # labels, spans and confidences, bit for bit
        # and in a batch with lengths, padding ignored
        batch = torch.stack([out, out])
        lens = torch.tensor([width, width - 3])
        assert D.Decoder(D.GREEDY)(batch, lens) == ctc.greedy_decoder(batch, lens)


def test_the_decoder_callable_answers_in_krakens_shape_and_keeps_its_results():
    dec = D.Decoder(D.GREEDY, TABLE)
    a, b = peaked("quod"), peaked("est")
    width = max(len(a), len(b))
    pad = [frame({None: 0.99})] * (width - len(b))
    out = dec([as_cw(a), as_cw(b + pad)], [len(a), len(b)])
    assert [len(line) for line in out] == [4, 3]
    assert all(len(tok) == 4 for line in out for tok in line)
    assert [r.text for r in dec.last] == ["quod", "est"]
    assert dec.last[1].n_frames == len(b)
    with pytest.raises(ValueError, match="seq_lens"):
        dec([as_cw(a), as_cw(a)])
    assert dec.params() == {"decoder": "greedy"}


# --------------------------------------------------------------------------- #
# the prefix beam
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("text", ["quod est", "sed quo", "e", "duo  est"])
def test_prefix_beam_without_a_model_equals_greedy_where_the_posterior_is_peaked(text):
    frames = peaked(text)
    g = D.decode_greedy(frames, TABLE)
    b = D.decode_prefix_beam(frames, TABLE, None)
    assert b.text == g.text == text
    assert b.labels == g.labels and b.spans == g.spans
    assert b.char_scores == pytest.approx(g.char_scores)
    assert D.line_confidence(b) == pytest.approx(D.line_confidence(g))
    assert b.lm_score is None
    # the prefix beam sums the alignments of the text: never below the best path
    assert b.score >= g.score - 1e-9


def test_a_hand_made_trigram_pulls_a_near_tie_to_the_modelled_spelling(arpa_path):
    frames = near_tie()
    assert D.decode_greedy(frames, TABLE).text == "qvod"
    assert D.decode_prefix_beam(frames, TABLE, None).text == "qvod"
    lm = D.ArpaLM.load(arpa_path)
    res = D.decode_prefix_beam(frames, TABLE, lm, lm_weight=1.5)
    assert res.text == "quod"
    # the character the model chose carries its own posterior, not the winner's
    assert res.char_scores[1] == pytest.approx(0.46)
    assert res.lm_score == pytest.approx(lm.sentence(["q", "u", "o", "d"]))
    assert res.score == pytest.approx(res.am_score + 1.5 * res.lm_score)
    # with no weight the model is not heard
    assert D.decode_prefix_beam(frames, TABLE, lm, lm_weight=0.0).text == "qvod"
    # the Decoder object says the same
    dec = D.Decoder(D.PREFIX_BEAM, TABLE, lm=lm, lm_weight=1.5, beam=10)
    assert dec.decode(as_cw(frames)).text == "quod"
    assert dec.params()["decoder"] == "prefix-beam" and dec.params()["lm_weight"] == 1.5


def test_forced_path_is_the_best_alignment_and_refuses_what_cannot_fit():
    frames = peaked("quo")
    labels = [LAB["q"], LAB["u"], LAB["o"]]
    assert D.forced_path(frames, labels) == D.greedy_path(frames)
    assert D.forced_path(frames, []) == [0] * len(frames)
    assert D.forced_path(frames[:2], labels) is None
    # a doubled letter needs its blank
    assert D.forced_path([frame({"o": 0.9})] * 2, [LAB["o"], LAB["o"]]) is None
    assert D.forced_path([frame({"o": 0.9})] * 3, [LAB["o"], LAB["o"]]) == [
        LAB["o"],
        0,
        LAB["o"],
    ]


def test_retemper_flattens_and_sharpens_and_matches_the_softmax_of_scaled_logits():
    f = [0.7, 0.2, 0.1]
    flat = D.retemper([f], 2.0)[0]
    sharp = D.retemper([f], 0.5)[0]
    assert sum(flat) == pytest.approx(1.0) and sum(sharp) == pytest.approx(1.0)
    assert flat[0] < 0.7 < sharp[0]
    logits = [math.log(p) + 3.0 for p in f]  # any constant per frame
    z = sum(math.exp(x / 2.0) for x in logits)
    assert flat == pytest.approx([math.exp(x / 2.0) / z for x in logits])
    assert D.retemper([f], 1.0) == [f]
    with pytest.raises(ValueError):
        D.retemper([f], 0.0)
    assert (
        D.Decoder(D.GREEDY, TABLE, temperature=2.0).decode_frames(peaked("quo")).char_scores[0]
        < 0.97
    )


def test_frames_of_turns_krakens_layout_and_cuts_the_padding():
    cw = [[0.1, 0.2, 0.3], [0.9, 0.8, 0.7]]
    assert D.frames_of(cw) == [[0.1, 0.9], [0.2, 0.8], [0.3, 0.7]]
    assert D.frames_of(cw, 2) == [[0.1, 0.9], [0.2, 0.8]]
    assert D.frames_of([]) == []


# --------------------------------------------------------------------------- #
# tokens and the codec round trip
# --------------------------------------------------------------------------- #


def test_token_names_and_their_inverse():
    assert D.lm_token(" ") == "<space>"
    assert D.lm_token(" ") == "<U+00A0>"
    assert D.lm_token("ã") == "ã"
    assert D.lm_token("\t") == "<U+0009>"
    for ch in (" ", " ", "q", "é", "ã", "-"):
        assert D.token_char(D.lm_token(ch)) == ch
    assert D.token_char("<ctc>") == "" and D.token_char("<unk>") == ""


def test_the_tokens_file_round_trips_the_codec(tmp_path):
    codec = SimpleNamespace(
        c2l={" ": [1], "q": [2], "u": [3], "é": [4], " ": [5], "ſ": [6], "ch": [7, 8]}
    )
    table = D.TokenTable.from_codec(codec)
    assert table.names[0] == "<ctc>" and table.chars[0] == ""
    assert table.names[1] == "<space>" and table.space == 1
    assert table.names[5] == "<U+00A0>"
    # labels that only occur inside a multi-label entry write nothing by themselves
    assert table.chars[7] == "" and table.names[7] == "<unk>"
    assert len(table) == 9
    path = table.write(tmp_path / "tokens.txt")
    lines = path.read_text(encoding="utf-8").split("\n")
    assert lines[0] == "<ctc>" and lines[1] == "<space>" and lines[-1] == ""
    back = D.TokenTable.read(path)
    assert back.names == table.names
    assert back.chars == table.chars
    assert back.text([2, 3, 1, 4]) == "qu é"
    with pytest.raises(ValueError, match="blank"):
        D.TokenTable(["a"], ["a"])


def test_a_real_kraken_codec_round_trips(tmp_path):
    codec_mod = pytest.importorskip("kraken.lib.codec")
    codec = codec_mod.PytorchCodec(" abcdefſé-,.")
    table = D.TokenTable.from_codec(codec)
    assert len(table) == codec.max_label + 1
    for ch, labels in codec.c2l.items():
        assert table.chars[labels[0]] == ch
    assert D.TokenTable.read(table.write(tmp_path / "t.txt")).chars == table.chars
    # decode a label sequence both ways
    labels = [codec.c2l[c][0] for c in "cafſé"]
    theirs = "".join(t[0] for t in codec.decode([(lab, 0, 0, 1.0) for lab in labels]))
    assert table.text(labels) == theirs == "cafſé"


def test_the_aligners_fold_maps_labels_onto_the_folded_alphabet():
    assert D.fold_char("V", "align") == "u"
    assert D.fold_char("J", "align") == "i"
    assert D.fold_char("é", "align") == "e"
    assert D.fold_char("ſ", "align") == "s"
    assert D.fold_char(" ", "align") == " "
    assert D.fold_char(",", "align") is None  # punctuation has no token there
    assert D.fold_char("&", "align") is None  # nor has what the fold spells out
    assert D.fold_char("x", "none") == "x"
    with pytest.raises(ValueError):
        D.fold_char("x", "other")
    table = D.TokenTable.from_chars([" ", "V", "u", ","], fold="align")
    assert table.names == ["<ctc>", "<space>", "u", "u", "<unk>"]
    assert table.chars[2] == "V"  # the reader's own character is what is written


# --------------------------------------------------------------------------- #
# the n-gram interface
# --------------------------------------------------------------------------- #


def test_arpa_reader_scores_with_backoff_and_unknowns(arpa_path):
    lm = D.ArpaLM.load(arpa_path)
    assert lm.order == 3
    assert isinstance(lm, D.NGramLM)
    s0 = lm.start()
    s1, a = lm.score(s0, "q")
    assert a == pytest.approx(-0.3)  # the bigram <s> q
    s2, b = lm.score(s1, "u")
    assert b == pytest.approx(-0.2 + -0.05)  # no trigram <s> q u: the backoff of <s> q
    _, c = lm.score(s2, "o")
    assert c == pytest.approx(-0.05)  # the trigram q u o
    _, d = lm.score(s1, "v")
    assert d == pytest.approx(-0.2 + -2.5)
    # q v o: no trigram, no bigram v o: back off twice to the unigram
    s3, _ = lm.score(s1, "v")
    _, e = lm.score(s3, "o")
    assert e == pytest.approx(0.0 + -0.3 + -1.0)
    # an unknown token is <unk>
    _, u = lm.score(s0, "ж")
    assert u == pytest.approx(-0.3 + -2.0)
    # <s> q · q u (backed off) · q u o · d after u o (two backoffs) · the end after o d
    assert lm.sentence(["q", "u", "o", "d"]) == pytest.approx(
        -0.3 + (-0.2 - 0.05) - 0.05 + (-0.1 - 0.3 - 1.0) + (-0.3 - 1.0)
    )


def test_arpa_reader_agrees_with_kenlm(arpa_path):
    kenlm = pytest.importorskip("kenlm")
    ours = D.ArpaLM.load(arpa_path)
    theirs = kenlm.Model(str(arpa_path))
    wrapped = D.KenLMModel(arpa_path)
    for tokens in (["q", "u", "o", "d"], ["q", "v", "o", "d"], ["e", "s", "ж", "<space>", "q"], []):
        want = theirs.score(" ".join(tokens), bos=True, eos=True)
        assert ours.sentence(tokens) == pytest.approx(want, abs=1e-5)
        state, total = wrapped.start(), 0.0
        for tok in tokens:
            state, s = wrapped.score(state, tok)
            total += s
        assert total + wrapped.finish(state) == pytest.approx(want, abs=1e-5)
    assert isinstance(D.load_lm(arpa_path), D.KenLMModel)


def test_load_lm_without_kenlm_reads_the_arpa_beside_a_binary(arpa_path, monkeypatch):
    def no_kenlm(_path):
        raise ModuleNotFoundError("kenlm")

    monkeypatch.setattr(D, "KenLMModel", no_kenlm)
    assert isinstance(D.load_lm(arpa_path), D.ArpaLM)
    binary = arpa_path.with_suffix(".bin")
    binary.write_bytes(b"\x00")
    assert isinstance(D.load_lm(binary), D.ArpaLM)
    arpa_path.unlink()
    with pytest.raises(ModuleNotFoundError, match="decode"):
        D.load_lm(binary)


# --------------------------------------------------------------------------- #
# the spec a command line gives
# --------------------------------------------------------------------------- #


def test_spec_from_options_and_its_errors(arpa_path, tmp_path):
    assert D.spec_from_options(None).is_greedy
    assert D.spec_from_options("greedy").suffix == ""
    spec = D.spec_from_options("beam-lm", arpa_path, 1.2, 20)
    assert (spec.kind, spec.lm_weight, spec.beam) == ("beam-lm", 1.2, 20)
    assert spec.suffix == "+beam-lm"
    assert spec.params() == {
        "decoder": "beam-lm",
        "lm": str(arpa_path),
        "lm_weight": 1.2,
        "beam": 20,
        "fold": "none",
    }
    assert D.spec_from_options("prefix-beam").lm is None
    narrow = D.spec_from_options("prefix-beam", beam_tokens=5)
    assert narrow.params()["beam_tokens"] == 5
    assert narrow.build(table=TABLE).beam_tokens == 5
    assert "beam_tokens" not in spec.params()
    with pytest.raises(ValueError, match="unknown --decoder"):
        D.spec_from_options("viterbi")
    with pytest.raises(ValueError, match="needs --lm"):
        D.spec_from_options("beam-lm")
    with pytest.raises(ValueError, match="no such file"):
        D.spec_from_options("beam-lm", tmp_path / "missing.bin")
    with pytest.raises(ValueError, match="--lm needs"):
        D.spec_from_options("greedy", arpa_path)
    with pytest.raises(ValueError, match="codec"):
        D.DecoderSpec(kind="prefix-beam").build()
    assert D.DecoderSpec().build().kind == "greedy"


def test_the_fold_comes_from_the_models_sidecar(arpa_path):
    assert D.lm_meta(arpa_path) is None
    arpa_path.with_suffix(".json").write_text('{"fold": "align", "order": 3}', encoding="utf-8")
    assert D.lm_meta(arpa_path)["order"] == 3
    spec = D.DecoderSpec(kind="prefix-beam", lm=str(arpa_path))
    assert spec.resolved_fold() == "align"
    codec = SimpleNamespace(c2l={" ": [1], "V": [2], "o": [3], "d": [4], "q": [5]})
    dec = spec.build(codec)
    assert dec.table.names[2] == "u" and dec.table.chars[2] == "V"
    assert D.DecoderSpec(kind="prefix-beam", lm=str(arpa_path), fold="none").resolved_fold() == (
        "none"
    )


# --------------------------------------------------------------------------- #
# flashlight-text with KenLM (the `decode` extra)
# --------------------------------------------------------------------------- #


def test_flashlight_beam_equals_greedy_on_a_peaked_posterior_and_hears_the_model(arpa_path):
    pytest.importorskip("flashlight.lib.text.decoder")
    pytest.importorskip("kenlm")
    pytest.importorskip("numpy")
    frames = peaked("quod est")
    g = D.decode_greedy(frames, TABLE)
    no_lm = D.Decoder(D.BEAM_LM, TABLE, lm=None)
    r = no_lm.decode_frames(frames)
    assert r.text == g.text and r.labels == g.labels and r.spans == g.spans
    assert r.char_scores == pytest.approx(g.char_scores)
    assert r.score == pytest.approx(g.score, abs=1e-3)  # the best path, as greedy's
    assert r.lm_score is None

    tie = near_tie()
    assert no_lm.decode_frames(tie).text == "qvod"
    with_lm = D.Decoder(D.BEAM_LM, TABLE, lm=arpa_path, lm_weight=1.5)
    res = with_lm.decode_frames(tie)
    assert res.text == "quod"
    assert res.char_scores[1] == pytest.approx(0.46)
    lm = D.ArpaLM.load(arpa_path)
    assert res.lm_score == pytest.approx(lm.sentence(["q", "u", "o", "d"]), abs=1e-4)
    assert res.score == pytest.approx(res.am_score + 1.5 * res.lm_score, abs=1e-3)
    # the two beams agree with each other
    assert D.decode_prefix_beam(tie, TABLE, lm, lm_weight=1.5).text == res.text
    assert with_lm.params()["beam_threshold"] == D.DEFAULT_BEAM_THRESHOLD
    # kraken's protocol, from its layout
    out = with_lm([as_cw(tie)], [len(tie)])
    assert "".join(TABLE.chars[tok[0]] for tok in out[0]) == "quod"
    assert with_lm.decode_frames([]).text == ""


def test_beam_lm_needs_a_space_in_the_codec_and_says_what_to_install(monkeypatch):
    pytest.importorskip("flashlight.lib.text.decoder")
    with pytest.raises(ValueError, match="no space"):
        D.Decoder(D.BEAM_LM, D.TokenTable.from_chars(["a", "b"]))
    with pytest.raises(ValueError, match="needs the codec"):
        D.Decoder(D.BEAM_LM)
    with pytest.raises(ValueError, match="unknown decoder"):
        D.Decoder("viterbi")


# --------------------------------------------------------------------------- #
# the engine: a real kraken recogniser with random weights
# --------------------------------------------------------------------------- #


def _line_png(seed: int) -> bytes:
    from PIL import Image, ImageDraw

    im = Image.new("L", (260 + 40 * seed, 60), 255)
    draw = ImageDraw.Draw(im)
    for k in range(10 + seed):
        x = 10 + k * 22
        draw.line((x, 10 + (k * 7 + seed * 3) % 30, x + 12, 50 - (k * 5) % 25), fill=0, width=3)
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


@pytest.fixture(scope="module")
def tiny_model(tmp_path_factory):
    """A kraken recognition model with random weights and a small codec, as a file."""
    torch = pytest.importorskip("torch")
    vgsl = pytest.importorskip("kraken.lib.vgsl")
    codec_mod = pytest.importorskip("kraken.lib.codec")
    writers = pytest.importorskip("kraken.models.writers")
    torch.manual_seed(20261117)
    codec = codec_mod.PytorchCodec(" doquvest")
    net = vgsl.TorchVGSLModel(
        vgsl=f"[1,48,0,1 Cr3,3,8 Mp2,2 S1(1x0)1,3 Lbx16 O1c{codec.max_label + 1}]",
        codec=codec.c2l,
        model_type=["recognition"],
        seg_type="baselines",
        one_channel_mode="L",
    )
    path = tmp_path_factory.mktemp("tiny") / "tiny.safetensors"
    writers.write_safetensors([net], path)
    return path


@pytest.mark.filterwarnings("ignore")
def test_the_engine_reads_as_before_and_takes_a_decoder(tiny_model, arpa_path):
    from leibniz.htr.engines import KrakenEngine

    images = [_line_png(s) for s in range(4)]
    before = KrakenEngine(str(tiny_model), batch_size=3).transcribe_conf(images)
    # an explicit greedy spec changes nothing: kraken's own decoder stays in place
    eng = KrakenEngine(str(tiny_model), batch_size=3, decoder=D.DecoderSpec())
    assert eng.transcribe_conf(images) == before
    assert eng._decoder is None
    # the scored reading carries the same text and the same confidence
    scored = eng.transcribe_scored(images)
    assert [(r.text, D.line_confidence(r)) for r in scored] == before
    assert all(r.n_frames > 0 and r.score < 0 for r in scored)
    # the posteriors, frames × labels, each frame a distribution
    post = eng.posteriors(images)
    assert post[0].shape == (scored[0].n_frames, 10)
    assert float(post[0].sum(axis=1).min()) == pytest.approx(1.0, abs=1e-4)
    regreedy = D.decode_greedy(post[0].tolist())
    assert regreedy.char_scores == pytest.approx(scored[0].char_scores, abs=1e-6)
    # a prefix beam with a model, through kraken's decoder hook
    beam = KrakenEngine(
        str(tiny_model),
        decoder=D.DecoderSpec(kind="prefix-beam", lm=str(arpa_path), lm_weight=1.5, beam=8),
    )
    rows = beam.transcribe_conf(images)
    assert len(rows) == 4 and beam._decoder is not None
    assert all(c is None or 0.0 <= c <= 1.0 for _, c in rows)
    assert [r.text for r in beam.transcribe_scored(images)] == [t for t, _ in rows]
    # a softmax temperature reaches the recogniser: flatter posteriors, lower confidence
    warm = KrakenEngine(str(tiny_model), temperature=2.0).transcribe_conf(images)
    assert warm[0][1] < before[0][1]

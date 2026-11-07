"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""

"""Test tambahan: regresi bug dan kasus tepi."""
from crud import ast_nodes as ast
from crud.lexer import LexError, TokenType as T, tokenize
from crud.parser import parse_sql
from crud.pipeline import analyze_source
from crud.resolver import Resolver
import pytest


def parse_one(sql):
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    return script.statements[0]


def resolve(sql):
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    return script, Resolver().resolve_script(script)


def cols(node):
    return [n for n in ast.iter_nodes(node) if isinstance(n, ast.ColumnRef)]


# ---- regresi bug --------------------------------------------------------
def test_keyword_tidak_peka_huruf():
    assert [(t.type, t.value) for t in tokenize("Select x FrOm t")[:4:2]] == [
        (T.KEYWORD, "SELECT"), (T.KEYWORD, "FROM")]


def test_operator_tidak_sama_satu_token():
    assert [t.value for t in tokenize("a <> b")[:3]] == ["a", "<>", "b"]


def test_kutip_ganda_dalam_string():
    toks = tokenize("'O''Brien' x")
    assert (toks[0].type, toks[0].value) == (T.STRING, "O'Brien") and toks[1].value == "x"


def test_and_lebih_kuat_dari_or():
    w = parse_one("SELECT a FROM t WHERE a = 1 OR b = 2 AND c = 3").where
    assert w.op == "OR" and w.right.op == "AND"
    w = parse_one("SELECT a FROM t WHERE a = 1 AND b = 2 OR c = 3").where
    assert w.op == "OR" and w.left.op == "AND"


def test_recovery_berhenti_di_titik_koma():
    script = parse_sql("SELECT FROM a;\nSELECT x FROM b;\nSELECT FROM c;\nDELETE FROM d;")
    assert len(script.errors) == 2
    assert [type(s).__name__ for s in script.statements] == ["Select", "Delete"]


def test_left_outer_join():
    s = parse_one("SELECT a.id FROM a LEFT OUTER JOIN b ON b.k = a.id")
    assert s.joins[0].kind == "LEFT"


def test_shadowing_alias_terdalam_menang():
    script, diags = resolve("SELECT x.id FROM a x WHERE x.id IN (SELECT x.k FROM b x)")
    inner = [c for c in cols(script) if c.name == "k"][0]
    outer = [c for c in cols(script) if c.name == "id"][0]
    assert inner.resolved == "b" and outer.resolved == "a" and diags == []


def test_alias_delete_tidak_bocor_ke_statement_berikutnya():
    _, diags = resolve("DELETE FROM a s WHERE s.x = 1; SELECT s.id FROM b u")
    assert [d.level for d in diags] == ["error"] and "'s'" in diags[0].message


def test_update_subquery_dibaca_R():
    res = analyze_source("UPDATE a SET x = (SELECT y FROM b) WHERE id IN (SELECT id FROM c)")
    assert res.statements[0].tables == {"a": "U", "b": "R", "c": "R"}


def test_insert_select_crud():
    res = analyze_source("INSERT INTO arsip (id) SELECT id FROM pesanan")
    assert res.parse_errors == [] and res.statements[0].tables == {"arsip": "C", "pesanan": "R"}


def test_komentar_blok_dan_kolom_tanpa_qualifier():
    assert [t.value for t in tokenize("/* a * b */ x")[:-1]] == ["x"]
    script, _ = resolve("SELECT nama FROM crm.pelanggan")
    assert cols(script)[0].resolved == "crm.pelanggan"


# ---- kasus tepi ----------------------------------------------------------
def test_tepi_komentar_blok_tidak_ditutup():
    # Pembuka tanpa penutup harus LexError di posisi pembuka, bukan loop/diam.
    with pytest.raises(LexError) as info:
        tokenize("SELECT 1\n  /* belum ditutup")
    assert (info.value.line, info.value.col) == (2, 3)


def test_tepi_komentar_blok_bintang_beruntun():
    # '/***/' dan '/**/' berisiko salah karena '*' dekat penutup.
    assert [t.value for t in tokenize("/***/ a /**/ b")[:-1]] == ["a", "b"]


def test_tepi_string_hanya_kutip_dan_kosong():
    # '' (kosong) vs '''' (satu kutip): dua kasus yang mudah tertukar.
    assert tokenize("''")[0].value == "" and tokenize("''''")[0].value == "'"


def test_tepi_kolom_ambigu_dan_derived_tanpa_alias():
    # Dua tabel di scope terdalam: resolved harus None + warning, bukan menebak.
    script, diags = resolve("SELECT nama FROM a, b")
    assert cols(script)[0].resolved is None
    assert [d.level for d in diags] == ["warning"] and "ambigu" in diags[0].message


def test_tepi_subquery_from_tidak_melihat_tabel_saudara():
    # Spek 4.4: p belum ada saat subquery di FROM di-resolve.
    _, diags = resolve("SELECT p.id FROM a p, (SELECT q.id FROM b q WHERE q.id = p.id) d")
    assert any("'p'" in d.message and d.level == "error" for d in diags)

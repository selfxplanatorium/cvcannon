"""Unit tests for the cvcannon pipeline helpers in scripts/cv.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_cv():
    spec = importlib.util.spec_from_file_location("cvcannon_cv", ROOT / "scripts" / "cv.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


cv = load_cv()

SAMPLE_IMG = '<img src="../../../PROFILE/portrait.png" alt="Portrait" class="profile-pic">'


def test_validate_slug_accepts_valid():
    assert cv.validate_slug("acme-platform-engineer") == "acme-platform-engineer"


@pytest.mark.parametrize("bad", ["", "Acme", "-lead", "a_b", "a b", "A1", "a/b"])
def test_validate_slug_rejects_invalid(bad):
    with pytest.raises(SystemExit):
        cv.validate_slug(bad)


@pytest.fixture
def tmp_repo(tmp_path, monkeypatch):
    """Point cv.ROOT at a temp directory so fail() can format relative paths."""
    monkeypatch.setattr(cv, "ROOT", tmp_path)
    return tmp_path


def test_portrait_img_src_reads_class_and_src():
    assert cv.portrait_img_src(SAMPLE_IMG) == "../../../PROFILE/portrait.png"
    assert cv.portrait_img_src("<p>no image here</p>") is None


def test_apply_portrait_src_rewrites_existing_image(monkeypatch):
    monkeypatch.setattr(cv, "portrait_file", lambda: Path("portrait.webp"))
    result = cv.apply_portrait_src(SAMPLE_IMG, "../../PROFILE/")
    assert 'src="../../PROFILE/portrait.webp"' in result


def test_remove_portrait_img_drops_the_element():
    result = cv.remove_portrait_img(SAMPLE_IMG)
    assert "profile-pic" not in result
    assert "<img" not in result


def test_scaffold_template_without_portrait_removes_image(monkeypatch):
    monkeypatch.setattr(cv, "portrait_file", lambda: None)
    result = cv.scaffold_cv_source(template="default", bundle=cv.TEMPLATES / "default")
    assert cv.portrait_img_src(result) is None
    assert "../../ASSETS/fonts/Lexend-Regular.ttf" in result


def test_scaffold_template_with_portrait_keeps_and_points_image(monkeypatch):
    monkeypatch.setattr(cv, "portrait_file", lambda: Path("portrait.webp"))
    result = cv.scaffold_cv_source(template="default", bundle=cv.TEMPLATES / "default")
    assert cv.portrait_img_src(result) == "../../PROFILE/portrait.webp"


def write_app(target: Path, cv_body: str, letter_body: str) -> None:
    (target / "cv.html").write_text(f"<html><body><p>{cv_body}</p></body></html>")
    (target / "cover-letter.html").write_text(
        f'<html><body><p class="body-text">Dear team, {letter_body}</p></body></html>'
    )


def test_writing_check_rejects_banned_phrase(tmp_path):
    write_app(tmp_path, "Leveraged systems to ship.", "word " * 260)
    with pytest.raises(SystemExit):
        cv.writing_check(tmp_path)


def test_writing_check_rejects_em_dash(tmp_path):
    write_app(tmp_path, "Managed systems — end to end.", "word " * 260)
    with pytest.raises(SystemExit):
        cv.writing_check(tmp_path)


def test_writing_check_accepts_clean_documents(tmp_path):
    write_app(tmp_path, "Managed production systems and automated deployments.", "word " * 260)
    cv.writing_check(tmp_path)


def test_cover_letter_body_words_counts_only_body(tmp_path):
    path = tmp_path / "cover-letter.html"
    path.write_text(
        '<html><body><p>ignored</p>'
        '<p class="body-text">one two three four five</p></body></html>'
    )
    assert cv.cover_letter_body_words(path) == 5
    empty = tmp_path / "empty.html"
    empty.write_text('<html><body><p>no body-text class</p></body></html>')
    assert cv.cover_letter_body_words(empty) is None


def test_phrase_hits_respects_word_boundaries():
    assert cv.phrase_hits("We leveraged the platform.", cv.BANNED_EVERYWHERE) == ["leveraged"]
    assert cv.phrase_hits("Fine-tuned the pipeline.", cv.BANNED_EVERYWHERE) == []


def test_validate_html_rejects_unresolved_placeholder(tmp_repo):
    path = tmp_repo / "cv.html"
    path.write_text("<html><body><p>{{Full Name}}</p><p>[Role]</p></body></html>")
    with pytest.raises(SystemExit):
        cv.validate_html(path, cv=False)


def test_validate_html_rejects_remote_dependency(tmp_repo):
    path = tmp_repo / "cv.html"
    path.write_text(
        '<html><head><link href="https://fonts.example/x.css"></head>'
        "<body><p>ok</p></body></html>"
    )
    with pytest.raises(SystemExit):
        cv.validate_html(path, cv=False)


def test_validate_html_accepts_clean_document(tmp_repo):
    path = tmp_repo / "cv.html"
    path.write_text("<html><body><p>Clean, local, no placeholders.</p></body></html>")
    cv.validate_html(path, cv=False)


def test_build_all_fails_without_applications(tmp_repo, monkeypatch):
    monkeypatch.setattr(cv, "APPLICATIONS", tmp_repo)
    with pytest.raises(SystemExit):
        cv.build_all()


def test_application_slugs_skips_incomplete_folders(monkeypatch, tmp_path):
    (tmp_path / "complete").mkdir()
    (tmp_path / "complete" / "cv.html").write_text("<html></html>")
    (tmp_path / "empty").mkdir()
    monkeypatch.setattr(cv, "APPLICATIONS", tmp_path)
    assert cv.application_slugs() == ["complete"]

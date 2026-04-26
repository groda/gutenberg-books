"""Tests for the gutenberg-books library."""

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest
import requests

from gutenberg_books import GutenbergBooks


# ----------------------------------------------------------------------
# Mocked tests (fast, always run)
# ----------------------------------------------------------------------
@pytest.fixture
def sample_csv() -> str:
    """Small realistic catalog snippet for mocking."""
    return """Title,Authors,Subjects,Language,Bookshelves,Type
"Book One","Author A (1800-1850)","Fiction; Adventure","en","Classic Literature","Text"
"Book Two","Author B (1900-1950)","History","en; fr","","Text"
"Book Three","Author C","Science Fiction; Fantasy","en","Modern","Text"
"""


@pytest.fixture
def mock_gzip_response(sample_csv):
    """Return a gzipped response that mimics the real Gutenberg catalog download."""
    import gzip
    import io

    compressed = gzip.compress(sample_csv.encode("utf-8"))
    mock_resp = MagicMock()
    mock_resp.content = compressed
    mock_resp.raise_for_status.return_value = None
    return mock_resp


@pytest.fixture
def temp_cache(tmp_path):
    """Use pytest temporary directory as cache (clean every test)."""
    return tmp_path / "GutenbergBooks"


def test_init_creates_cache_dir_and_loads_catalog(
    monkeypatch, temp_cache, mock_gzip_response
):
    """First run: downloads catalog and creates cache."""
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_gzip_response)
    gb = GutenbergBooks(cache_dir=temp_cache)
    assert temp_cache.exists()
    assert gb.catalog_file.exists()
    assert len(gb.catalog) == 3


def test_subsequent_init_uses_cache(temp_cache, monkeypatch, mock_gzip_response):
    """Second run should load from cache without hitting the network."""
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_gzip_response)
    GutenbergBooks(cache_dir=temp_cache)          # first run

    monkeypatch.undo()                            # remove network mock
    gb = GutenbergBooks(cache_dir=temp_cache)
    assert len(gb.catalog) == 3


def test_get_subjects_authors_languages_bookshelves(
    temp_cache, monkeypatch, mock_gzip_response
):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_gzip_response)
    gb = GutenbergBooks(cache_dir=temp_cache)

    assert "Fiction" in gb.get_subjects()
    assert "Author A (1800-1850)" in gb.get_authors()
    assert "en" in gb.get_languages()


def test_topn_methods(temp_cache, monkeypatch, mock_gzip_response):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_gzip_response)
    gb = GutenbergBooks(cache_dir=temp_cache)

    subjects = gb.topn_subjects(2)
    assert list(subjects["Subject"]) == ["Fiction", "Adventure"]

    authors = gb.topn_authors(3)
    assert len(authors) == 3


def test_random_weighted_methods(temp_cache, monkeypatch, mock_gzip_response):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_gzip_response)
    gb = GutenbergBooks(cache_dir=temp_cache)

    subjects = gb.random_subjects(n=2, seed=42)
    assert len(subjects) == 2

    authors = gb.random_authors(n=1, seed=123)
    assert len(authors) == 1


def test_random_books(temp_cache, monkeypatch, mock_gzip_response):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_gzip_response)
    gb = GutenbergBooks(cache_dir=temp_cache)
    books = gb.random_books(n=2, seed=7)
    assert len(books) == 2


def test_search_books(temp_cache, monkeypatch, mock_gzip_response):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_gzip_response)
    gb = GutenbergBooks(cache_dir=temp_cache)

    results = gb.search_books(subject="Fiction", language="en")
    assert len(results) == 2

    results = gb.search_books(title="Book One")
    assert results["Title"].iloc[0] == "Book One"


def test_books_matching_subject_and_author(temp_cache, monkeypatch, mock_gzip_response):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_gzip_response)
    gb = GutenbergBooks(cache_dir=temp_cache)

    assert len(gb.books_matching_subject("adventure")) == 1
    assert len(gb.books_matching_author("Author A")) == 1


def test_books_matching_year(temp_cache, monkeypatch, mock_gzip_response):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_gzip_response)
    gb = GutenbergBooks(cache_dir=temp_cache)

    year_1820 = gb.books_matching_year(1820)
    assert len(year_1820) == 1
    assert "Book One" in year_1820["Title"].values


def test_download_book(temp_cache, monkeypatch, mock_gzip_response):
    """Test book download with mocked HTTP (catalog + book)."""
    catalog_resp = mock_gzip_response

    book_resp = MagicMock()
    book_resp.text = "This is the full text of the book."
    book_resp.raise_for_status.return_value = None

    def mock_requests_get(url: str, timeout=None, **kwargs):
        if "pg_catalog.csv.gz" in url:
            return catalog_resp
        if "pg12345" in url:
            return book_resp
        raise ValueError(f"Unexpected URL in test: {url}")

    monkeypatch.setattr(requests, "get", mock_requests_get)

    gb = GutenbergBooks(cache_dir=temp_cache)

    # New return type: Path
    path = gb.download_book(12345)
    assert path.exists()
    assert path.name == "pg12345.txt"

    assert path.read_text(encoding="utf-8") == "This is the full text of the book."

    # Also verify it doesn't re-download (and still returns the path)
    path2 = gb.download_book(12345)
    assert path2 == path  # same file


def test_is_book_downloaded(temp_cache, monkeypatch, mock_gzip_response):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_gzip_response)
    gb = GutenbergBooks(cache_dir=temp_cache)

    (temp_cache / "pg999.txt").touch()
    assert gb.is_book_downloaded(999) is True
    assert gb.is_book_downloaded(12345) is False


# ----------------------------------------------------------------------
# Real catalog tests (download once per session)
# ----------------------------------------------------------------------
@pytest.fixture(scope="session")
def real_catalog_dir(tmp_path_factory):
    """Download the real Gutenberg catalog once per test session."""
    cache_dir = tmp_path_factory.mktemp("real_gutenberg")
    # GutenbergBooks will download and cache the real catalog on first init
    gb = GutenbergBooks(cache_dir=cache_dir)
    return cache_dir


@pytest.fixture(scope="session")
def real_gb(real_catalog_dir):
    """Return a GutenbergBooks instance using the real catalog (reused)."""
    return GutenbergBooks(cache_dir=real_catalog_dir)


@pytest.mark.real
def test_real_catalog_loads(real_gb):
    """Smoke test: real catalog loads and has expected size."""
    assert len(real_gb.catalog) > 60000          # ≈70k books
    assert "Title" in real_gb.catalog.columns
    assert "Authors" in real_gb.catalog.columns
    assert "Language" in real_gb.catalog.columns


@pytest.mark.real
def test_real_topn_subjects(real_gb):
    """Top subjects on real data (just check it runs and returns DataFrame)."""
    df = real_gb.topn_subjects(10)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 10
    assert "Subject" in df.columns
    assert df["Count"].iloc[0] > 1000            #  most common subject for more that 1000 books
    df['Subject'].str.contains('fiction')        # Among the top 10 most common subjects is "Science fiction"


@pytest.mark.real
def test_real_books_matching_year(real_gb):
    """Year matching works on real author birth-death data."""
    # 1813 = year Jane Austen was writing Pride & Prejudice
    df = real_gb.books_matching_year(1813)
    assert len(df) > 50                          # many authors alive in 1813


@pytest.mark.real
def test_real_download_small_book(real_gb, tmp_path):
    """Download a real small book (we know it exists and is tiny)."""
    book_id = 1342          # Pride and Prejudice

    # New return type: Path
    path = real_gb.download_book(book_id)
    assert path.exists()
    assert path.name == f"pg{book_id}.txt"

    # Real book is > 100 KB
    assert path.stat().st_size > 100_000


@pytest.mark.real
def test_real_download_a_few_books(real_gb, tmp_path):
    """Download a real small book (we know it exists and is tiny)."""
    n = 10          # number of books to download

    # New return type: Path
    paths = real_gb.download_n_books(n=n, subject="Science Fiction", random_delay_sec=5)

    assert len(paths) == n
    for p in paths:
        assert p.exists()


@pytest.mark.real
def test_real_download_a_few_books(real_gb, tmp_path):
    """Download a real small book (we know it exists and is tiny)."""
    n = 10          # number of books to download

    # New return type: Path
    paths = real_gb.download_n_books(n=n, subject="Science Fiction", random_delay_sec=5)

    assert len(paths) == n
    for p in paths:
        assert p.exists()

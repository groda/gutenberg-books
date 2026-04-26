"""gutenberg-books - Easy access to Project Gutenberg catalog and books."""

from __future__ import annotations

import gzip
import io
import logging
from pathlib import Path

import pandas as pd
import requests
import random
import time

__version__ = "0.1.0"

logger = logging.getLogger(__name__)

GUTENBERG_CATALOG_URL = "https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv.gz"
DEFAULT_CACHE_DIR = "GutenbergBooks"


class GutenbergBooks:
    """Main class for exploring and downloading Project Gutenberg books."""

    def __init__(self, cache_dir: str | Path | None = None) -> None:
        """Initialize the catalog (downloads/caches if needed)."""
        self.cache_dir = Path(cache_dir or DEFAULT_CACHE_DIR).resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.catalog_file: Path = self.cache_dir / "pg_catalog.csv"
        self.catalog: pd.DataFrame = self._fetch_catalog()

        # Pre-compute unique lists once (fast and convenient)
        self.all_subjects: list[str] = self.get_subjects()
        self.all_authors: list[str] = self.get_authors()
        self.all_languages: list[str] = self.get_languages()
        self.all_bookshelves: list[str] = self.get_bookshelves()

    def _fetch_catalog(self) -> pd.DataFrame:
        """Load catalog from cache or download fresh."""
        if self.catalog_file.exists():
            logger.info("Loading catalog from cache: %s", self.catalog_file)
            return pd.read_csv(self.catalog_file, quotechar='"')

        logger.info("Downloading fresh catalog from %s", GUTENBERG_CATALOG_URL)
        try:
            response = requests.get(GUTENBERG_CATALOG_URL, timeout=60)
            response.raise_for_status()
            compressed = response.content
            decompressed = gzip.decompress(compressed)
            df = pd.read_csv(io.StringIO(decompressed.decode("utf-8")), quotechar='"')
            df.to_csv(self.catalog_file, index=False)
            logger.info("Catalog saved to %s", self.catalog_file)
            return df
        except Exception as e:
            logger.error("Failed to fetch catalog: %s", e)
            raise

    def refresh_catalog(self) -> None:
        """Force-refresh the catalog from the server."""
        if self.catalog_file.exists():
            self.catalog_file.unlink()
        self.catalog = self._fetch_catalog()
        self.all_subjects = self.get_subjects()
        self.all_authors = self.get_authors()
        self.all_languages = self.get_languages()
        self.all_bookshelves = self.get_bookshelves()

    def get_subjects(self) -> list[str]:
        return self.catalog["Subjects"].str.split("; ").explode().dropna().unique().tolist()

    def get_authors(self) -> list[str]:
        return self.catalog["Authors"].str.split("; ").explode().dropna().unique().tolist()

    def get_languages(self) -> list[str]:
        return self.catalog["Language"].str.split("; ").explode().dropna().unique().tolist()

    def get_bookshelves(self) -> list[str]:
        return self.catalog["Bookshelves"].str.split("; ").explode().dropna().unique().tolist()

    def get_types(self) -> list[str]:
        return self.catalog["Type"].dropna().unique().tolist()

    def _top_n(self, column: str, n: int) -> pd.DataFrame:
        exploded = self.catalog[column].str.split("; ").explode().dropna()
        counts = exploded.value_counts().reset_index(name="Count")
        counts = counts.rename(columns={counts.columns[0]: column})
        return counts.head(n)

    def topn_subjects(self, n: int) -> pd.DataFrame:
        df = self._top_n("Subjects", n)
        return df.rename(columns={"Subjects": "Subject"})

    def topn_authors(self, n: int) -> pd.DataFrame:
        df = self._top_n("Authors", n)
        return df.rename(columns={"Authors": "Author"})

    def topn_languages(self, n: int) -> pd.DataFrame:
        return self._top_n("Language", n)

    def topn_bookshelves(self, n: int) -> pd.DataFrame:
        df = self._top_n("Bookshelves", n)
        return df.rename(columns={"Bookshelves": "Bookshelf"})

    def _random_weighted(self, column: str, n: int, seed: int) -> pd.DataFrame:
        exploded = self.catalog[column].str.split("; ").explode().dropna()
        counts = exploded.value_counts().reset_index(name="Count")
        counts = counts.rename(columns={counts.columns[0]: column})
        return counts.sample(n=n, weights="Count", replace=False, random_state=seed)

    def random_subjects(self, n: int, seed: int) -> pd.DataFrame:
        return self._random_weighted("Subjects", n, seed).rename(columns={"Subjects": "Subject"})

    def random_authors(self, n: int, seed: int) -> pd.DataFrame:
        return self._random_weighted("Authors", n, seed).rename(columns={"Authors": "Author"})

    def random_books(self, n: int, seed: int) -> pd.DataFrame:
        return self.catalog.sample(n=n, replace=False, random_state=seed)

    def search_books(self, language: str | None = None, subject: str | None = None, title: str | None = None) -> pd.DataFrame:
        df = self.catalog.copy()
        if language:
            df = df[df["Language"].str.contains(language, case=False, na=False)]
        if subject:
            df = df[df["Subjects"].str.contains(subject, case=False, na=False)]
        if title:
            df = df[df["Title"].str.contains(title, case=False, na=False)]
        return df

    def books_matching_subject(self, substr: str) -> pd.DataFrame:
        return self.catalog[self.catalog["Subjects"].str.contains(substr, case=False, na=False)]

    def books_matching_author(self, substr: str) -> pd.DataFrame:
        return self.catalog[self.catalog["Authors"].str.contains(substr, case=False, na=False)]

    def books_matching_year(self, given_year: int) -> pd.DataFrame:
        catalog_copy = self.catalog.copy()
        temp = catalog_copy["Authors"].str.extractall(r"(?:\w+\s+)?(\d{4})\s*-\s*(\d{4})")
        temp = temp.reset_index()
        temp.columns = ["level_0", "match", "Birth_Year", "Death_Year"]
        merged = pd.merge(catalog_copy, temp, left_index=True, right_on="level_0")
        merged["Birth_Year"] = pd.to_numeric(merged["Birth_Year"], errors="coerce")
        merged["Death_Year"] = pd.to_numeric(merged["Death_Year"], errors="coerce")
        matching = merged[(merged["Birth_Year"] <= given_year) & (merged["Death_Year"] >= given_year)]
        matching = matching.drop(columns=["level_0", "match"], errors="ignore")
        return matching

    def is_book_downloaded(self, book_id: int) -> bool:
        book_file = self.cache_dir / f"pg{book_id}.txt"
        return book_file.exists()

    def download_book(self, book_id: int, random_delay_sec: int = 0) -> Path:
        """Download a single plain-text book. Returns the path to the file.

        If the book is already cached, it is returned immediately.
        If random_delay_sec > 0, a random pause (0–random_delay_sec seconds)
        is added after every operation (cached or downloaded) to be polite to Gutenberg.
        """
        book_file: Path = self.cache_dir / f"pg{book_id}.txt"

        if book_file.exists():
            logger.info("Book %d already in cache.", book_id)
            if random_delay_sec > 0:
                delay = random.uniform(0, random_delay_sec)
                time.sleep(delay)
            return book_file

        url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
        try:
            if random_delay_sec > 0:
                delay = random.uniform(0, random_delay_sec)
                logger.info("Pausing %.1fs before download (politeness delay)...", delay)
                time.sleep(delay)

            logger.info("Downloading book %d → %s", book_id, book_file.name)
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            book_file.write_text(resp.text, encoding="utf-8")
            logger.info("Successfully downloaded book %d", book_id)
            return book_file
        except Exception as e:
            logger.error("Failed to download book %d: %s", book_id, e)
            raise RuntimeError(f"Failed to download book {book_id}") from e

    def download_books(self, books: list[int], random_delay_sec: int = 5) -> list[Path]:
        """Download a list of books (by ID) with polite random delays.

        WARNING: Bulk downloads from the main Gutenberg site can get your IP blocked.
        Use with reasonable delays and only when necessary.
        See: https://www.gutenberg.org/policy/robot_access.html
        """
        logger.warning(
            "⚠️  Downloading %d books from Project Gutenberg. "
            "Respect their robot policy: https://www.gutenberg.org/policy/robot_access.html",
            len(books),
        )
        return [self.download_book(b, random_delay_sec) for b in books]

    def download_n_books(
        self, n: int, subject: str, random_delay_sec: int = 5
    ) -> list[Path]:
        """Download the first N books matching a subject (case-insensitive)."""
        matching = self.books_matching_subject(subject)
        if matching.empty:
            logger.warning("No books found for subject: %s", subject)
            return []

        book_ids = matching.head(n)["Text#"].astype(int).tolist()
        return self.download_books(book_ids, random_delay_sec)

    def download_size_books(
        self, size_mb: int = 128, subject: str | None = None, random_delay_sec: int = 5
    ) -> list[Path]:
        """Download books (optionally by subject) until the total size reaches ~size_mb.

        Useful for creating test datasets for big-data / ML pipelines.
        Books already in cache are reused (and count toward the size).
        """
        logger.warning(
            "⚠️  Downloading books until ~%d MB from Project Gutenberg. "
            "Respect their robot policy: https://www.gutenberg.org/policy/robot_access.html",
            size_mb,
        )

        if subject:
            df = self.books_matching_subject(subject)
        else:
            df = self.catalog

        book_ids = df["Text#"].astype(int).tolist()

        target_bytes = size_mb * 1024 * 1024
        total_size = 0
        paths: list[Path] = []

        for book_id in book_ids:
            if total_size >= target_bytes:
                break

            path = self.download_book(book_id, random_delay_sec)
            file_size = path.stat().st_size
            total_size += file_size
            paths.append(path)

        logger.info(
            "Finished: %d books, total size ≈ %.1f MB (requested %d MB)",
            len(paths),
            total_size / (1024 * 1024),
            size_mb,
        )
        return paths

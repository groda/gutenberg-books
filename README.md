# gutenberg-books

**Easy access to the entire Project Gutenberg catalog + book downloading**

A lightweight, modern Python library that lets you explore **70,000+** public-domain books from Project Gutenberg with zero hassle.

- Search by subject, author, language, title, or year  
- Weighted random sampling (realistic distribution)  
- One-line book downloading with automatic caching  
- Fully offline after the first run  

[![PyPI version](https://img.shields.io/pypi/v/gutenberg-books.svg)](https://pypi.org/project/gutenberg-books/)
[![Python versions](https://img.shields.io/pypi/pyversions/gutenberg-books.svg)](https://pypi.org/project/gutenberg-books/)

## Installation

```bash
pip install gutenberg-books
```

## Quick Start

```python
from gutenberg_books import GutenbergBooks

# Initialize (downloads ~12 MB catalog on first run and caches it)
gb = GutenbergBooks()                    # default cache: ./GutenbergBooks

# Top 5 most common subjects / authors
print(gb.topn_subjects(5))
print(gb.topn_authors(5))

# Random books (weighted by popularity)
print(gb.random_books(n=3, seed=42))

# Search examples
pride = gb.search_books(subject="Pride and Prejudice")
print(pride[["Title", "Authors", "Language"]].head())

# Books whose authors were alive in a specific year
print(gb.books_matching_year(1813))   # e.g., year Jane Austen was writing

# Download a full book (plain text)
gb.download_book(1342)   # Pride and Prejudice – Jane Austen
```

All returned data are **pandas DataFrames** — easy to filter, export to CSV, or analyse further.

## Features

| Feature                        | Method                              | Description |
|-------------------------------|-------------------------------------|-------------|
| Top-N lists                   | `topn_subjects(n)`, `topn_authors(n)` etc. | Most frequent subjects, authors, languages, bookshelves |
| Weighted random               | `random_subjects(n, seed)`, `random_authors(n, seed)` | Realistic sampling according to real distribution |
| Random books                  | `random_books(n, seed)`            | Pure random selection from catalog |
| Search                        | `search_books(language=..., subject=..., title=...)` | Flexible multi-criteria search |
| Subject / Author filter       | `books_matching_subject(substr)`   | Case-insensitive substring match |
| Year-based search             | `books_matching_year(year)`        | Books where any author was alive |
| Book download                 | `download_book(book_id)`           | Downloads `pg{book_id}.txt` to cache |
| Catalog refresh               | `refresh_catalog()`                | Force update from Gutenberg |

## Advanced Usage

```python
# All unique values
print(gb.all_subjects[:10])
print(gb.all_authors[:10])

# Check if book is already cached
print(gb.is_book_downloaded(1342))

# Change cache location
gb = GutenbergBooks(cache_dir="~/my_gutenberg_cache")
```

## Project Structure

```
GutenbergBooks/          # ← your cache folder (auto-created)
├── pg_catalog.csv       # cached catalog (~12 MB)
├── pg1342.txt           # example downloaded book
└── ...
```

## Development

### Quick setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR-USERNAME/gutenberg-books.git
cd gutenberg-books

# 2. Install in editable mode with all extras
pip install -e ".[test,docs]"


### Running Tests

```bash
pip install -e ".[test]"
# pip install -e ".[test]" --force-reinstall
pytest
```

All tests use mocked network responses and temporary directories, so they run fast and offline.
text


## License

MIT © groda

---

**Made with ❤️ for book lovers and data enthusiasts.**

Want to contribute? Open a PR on GitHub!

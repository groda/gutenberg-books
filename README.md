# gutenberg-books

**Easy access to the entire Project Gutenberg catalog + book downloading**

A lightweight, modern Python library that lets you explore **70,000+** public-domain books from Project Gutenberg with zero hassle.

- Search by subject, author, language, title, or year  
- Weighted random sampling (realistic distribution)  
- Polite book downloading with built-in delays (respects Gutenberg's robot policy)  
- Fully offline after the first run  

[![PyPI version](https://img.shields.io/pypi/v/gutenberg-books.svg)](https://pypi.org/project/gutenberg-books/)
[![Python versions](https://img.shields.io/pypi/pyversions/gutenberg-books.svg)](https://pypi.org/project/gutenberg-books/)
[![License](https://img.shields.io/pypi/l/gutenberg-books.svg)](https://github.com/groda/gutenberg-books/blob/main/LICENSE)

## Installation

```bash
pip install gutenberg-books
```

## Quick Start

```python
from gutenberg_books import GutenbergBooks

# Initialize (downloads ~12 MB catalog on first run and caches it)
gb = GutenbergBooks()                    # default cache: ./GutenbergBooks

# Explore the catalog
print(gb.topn_subjects(5))
print(gb.topn_authors(5))

# Random books (weighted by popularity)
print(gb.random_books(n=3, seed=42))

# Search
results = gb.search_books(subject="Pride and Prejudice")
print(results[["Title", "Authors", "Language"]])

# Books whose authors were alive in a specific year
print(gb.books_matching_year(1813))   # e.g. Jane Austen era

# Download books (safe & polite)
gb.download_book(1342)                    # Pride and Prejudice
paths = gb.download_n_books(10, subject="Science Fiction", random_delay_sec=5)
paths = gb.download_size_books(size_mb=16, random_delay_sec=5)
```

All returned data are **pandas DataFrames** — easy to filter, save to CSV, or use in ML pipelines.

## Main Features

| Feature                        | Method                              | Description |
|--------------------------------|-------------------------------------|-------------|
| Top-N lists                    | `topn_subjects(n)`, `topn_authors(n)` etc. | Most frequent subjects, authors, languages, bookshelves |
| Weighted random                | `random_subjects(n, seed)`, `random_authors(n, seed)` | Realistic sampling |
| Search                         | `search_books(...)`                 | Multi-criteria search |
| Subject / Author filter        | `books_matching_subject(substr)`    | Case-insensitive |
| Year-based search              | `books_matching_year(year)`         | Authors alive in that year |
| Download single book           | `download_book(book_id, random_delay_sec=5)` | Returns `Path` to file |
| Download multiple books        | `download_books(book_ids, ...)`     | List of IDs |
| Download by subject            | `download_n_books(n, subject, ...)` | First N matching books |
| Download until total size      | `download_size_books(size_mb, ...)` | Great for big-data test sets |

**Important**: The download methods include random delays by default to respect [Project Gutenberg's robot access policy](https://www.gutenberg.org/policy/robot_access.html).

## Advanced Usage

```python
# Use custom cache location
gb = GutenbergBooks(cache_dir="~/my_gutenberg_cache")

# Refresh catalog
gb.refresh_catalog()

# All unique values (pre-computed)
print(gb.all_subjects[:10])
print(gb.all_authors[:10])
```

## Development

See the [Development section](https://github.com/groda/gutenberg-books#development) in the repository for how to run tests, build the package, and contribute.

## License

MIT © groda

---

**Made with ❤️ for book lovers, data scientists, and developers.**

Want to contribute? Open a PR on GitHub!


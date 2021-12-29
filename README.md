sgf2ebook
=========

Basic script to convert a Go game record in `SGF` format to a simple e-book in `EPUB` format.

The ebook will be structured with one SVG diagram per page showing one new move.

Requirements
------------

The script requires the Rust executable [sgf-render](https://github.com/julianandrews/sgf-render) to convert SGF files to SVG diagrams. Downloading the latest version of `sgf-render` to this folder should be enough.

The script uses Python libraries defined in `requirements.txt`, namely jinja2 for templates and `sente` to parse the SGF files and obtain the moves sequence.

Use
---

Run the script with

```bash
python sgf2ebook -i sgf/ -o epub/
```

This invocation would look for input SGF files in a `sgf/` subdirectory and save
EPUB files in a `epub/` subdirectory.

Notes
-----

The path to sgf-render is stored in variable `SGF_RENDER_EXECUTABLE` at the
beginning of the script, change it there if needed.

The EPUB files are generated from template files located in `epub_template`. I
tried using calibre's `ebook-convert` utility to convert from HTML to EPUB and
generating a one-page ebook but I prefer to create a multi-page one to use my
book reader tools.

Todo list
---------

Possible improvements, in order of my personal priorities, include:
* [X] adding the game metadata on the first page
* [X] adding move comments
* [ ] adding internal links to jump 1/10/50 moves
* [ ] adding support for variation sequences
* [ ] adding a book cover

But given my limited time, don't expect anything.

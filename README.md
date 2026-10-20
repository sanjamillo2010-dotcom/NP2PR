# np2pr

**NP → PR: turn a "No Print" D&D character sheet into a "Print Ready" PDF.**

The character sheets exported from the AideDD character builder come out as a single, very tall page (`Name_NP.pdf`) with all 3 pages stacked on top of each other. That can't be printed properly. **np2pr** splits it into separate pages (`Name_PR.pdf`) that print cleanly on A4 or US Letter.

> Unofficial tool, not affiliated with AideDD.

## Features

- Auto-detects the gaps between the stacked pages (falls back to an equal split)
- Trims the empty side margins and scales every page by the same amount
- Vector output: text stays sharp, nothing is turned into an image
- GUI and command line
- Batch conversion of several files at once
- Works on Windows, macOS and Linux

## Install

Requires Python 3.8+.

```
pip install pymupdf
```

Then download `np2pr.py`.

## Usage

### GUI

Run it with no arguments:

```
python np2pr.py
```

Add one or more PDFs, choose the paper size and the number of pages, and click **Convert to Print Ready**.

### Command line

```
python np2pr.py Benladen_NP.pdf              # -> Benladen_PR.pdf (A4, 3 pages)
python np2pr.py *.pdf --size letter          # several files, US Letter
python np2pr.py Benladen_NP.pdf -o out/      # write results into out/
python np2pr.py Benladen_NP.pdf --pages 4    # sheet with 4 stacked pages
```

| Option | Description | Default |
| --- | --- | --- |
| `files` | Input PDF(s) | none (opens the GUI) |
| `--size {a4,letter}` | Paper size | `a4` |
| `--pages N` | Number of stacked pages | `3` |
| `-o, --outdir DIR` | Output folder | next to the input |
| `-h, --help` | Show help | |

Output files are named by replacing `_NP` with `_PR` (`Benladen_NP.pdf` becomes `Benladen_PR.pdf`).

## How it works

1. Renders a small preview of the tall page and looks for fully blank horizontal bands.
2. Cuts at the blank band closest to each expected page boundary (or at equal thirds if none is found).
3. Finds the horizontal extent of the content and crops the side margins.
4. Places each slice on its own A4/Letter page using vector-preserving PDF embedding.

## License

MIT, see [LICENSE](LICENSE).

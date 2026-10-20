#!/usr/bin/env python3
"""
np2pr - turn a "No Print" character sheet (NP: all pages stacked on ONE giant
page) into a "Print Ready" PDF (PR: separate real pages).

    Benladen_NP.pdf  ->  Benladen_PR.pdf   (3 pages, A4 or Letter)

Usage
-----
  GUI  :  python np2pr.py                      (no arguments -> opens a window)
  CLI  :  python np2pr.py Benladen_NP.pdf
          python np2pr.py *.pdf --size letter --pages 3 -o out_folder

Requires:  pip install pymupdf
Vector quality is kept (text stays sharp, nothing is rasterised).
"""
import argparse
import os
import sys

try:
    import pymupdf as fitz  # new name
except ImportError:  # older installs
    try:
        import fitz
    except ImportError:
        sys.exit("Missing dependency. Run:  pip install pymupdf")

import numpy as np

SIZES = {"a4": (595.28, 841.89), "letter": (612.0, 792.0)}


def _blank_bands(gray, min_len):
    """Return [(start, end)] of fully blank rows (in render pixels)."""
    blank = (gray < 250).sum(axis=1) == 0
    bands, start = [], None
    for i, b in enumerate(blank):
        if b and start is None:
            start = i
        elif not b and start is not None:
            if i - start >= min_len:
                bands.append((start, i))
            start = None
    if start is not None and len(blank) - start >= min_len:
        bands.append((start, len(blank)))
    return bands


def find_slices(page, n_pages, scale=0.5):
    """Find n_pages vertical slices (in PDF points) + a horizontal content box."""
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csGRAY)
    gray = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
    H = page.rect.height
    W = page.rect.width

    # horizontal extent of ALL content (so margins are trimmed uniformly)
    cols = np.where((gray < 250).sum(axis=0) > 0)[0]
    x0 = cols[0] / scale if len(cols) else 0
    x1 = (cols[-1] + 1) / scale if len(cols) else W

    # cut lines: ideal = equal split, snapped to the nearest blank band centre
    bands = _blank_bands(gray, min_len=int(10 * scale))
    centres = [((a + b) / 2) / scale for a, b in bands]
    cuts = [0.0]
    for k in range(1, n_pages):
        ideal = H * k / n_pages
        near = [c for c in centres if abs(c - ideal) < H / n_pages * 0.15]
        cuts.append(min(near, key=lambda c: abs(c - ideal)) if near else ideal)
    cuts.append(H)
    return list(zip(cuts[:-1], cuts[1:])), (x0, x1)


def convert(src, dst=None, size="a4", n_pages=3, margin_pt=18, log=print):
    doc = fitz.open(src)
    if len(doc) != 1:
        log(f"  note: {os.path.basename(src)} has {len(doc)} pages, using page 1 only")
    page = doc[0]

    if dst is None:
        base, ext = os.path.splitext(src)
        dst = (base[:-3] if base.upper().endswith("_NP") else base) + "_PR" + ext

    slices, (x0, x1) = find_slices(page, n_pages)
    pad = 8  # small breathing room around the detected content
    x0, x1 = max(0, x0 - pad), min(page.rect.width, x1 + pad)

    out = fitz.open()
    pw, ph = SIZES[size]
    # use one uniform scale for every page so sizes stay consistent
    crop_w = x1 - x0
    crop_h = max(b - a for a, b in slices)
    s = min((pw - 2 * margin_pt) / crop_w, (ph - 2 * margin_pt) / crop_h)

    for a, b in slices:
        clip = fitz.Rect(x0, a, x1, b)
        w, h = clip.width * s, clip.height * s
        left, top = (pw - w) / 2, (ph - h) / 2
        newp = out.new_page(width=pw, height=ph)
        newp.show_pdf_page(fitz.Rect(left, top, left + w, top + h), doc, 0, clip=clip)

    out.save(dst, deflate=True, garbage=3)
    log(f"  OK  {os.path.basename(src)} -> {dst}  ({len(slices)} pages, {size.upper()})")
    return dst


# ----------------------------------------------------------------- GUI ----
def run_gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title("NP → PR  (Print Ready character sheet)")
    root.geometry("560x380")
    files = []

    size_var = tk.StringVar(value="a4")
    pages_var = tk.IntVar(value=3)

    frm = ttk.Frame(root, padding=12)
    frm.pack(fill="both", expand=True)

    lb = tk.Listbox(frm, height=8)
    lb.pack(fill="both", expand=True)

    def add():
        for f in filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")]):
            if f not in files:
                files.append(f)
                lb.insert("end", f)

    def clear():
        files.clear()
        lb.delete(0, "end")

    row = ttk.Frame(frm)
    row.pack(fill="x", pady=6)
    ttk.Button(row, text="Add PDF(s)…", command=add).pack(side="left")
    ttk.Button(row, text="Clear", command=clear).pack(side="left", padx=6)
    ttk.Label(row, text="Paper:").pack(side="left", padx=(20, 4))
    ttk.Combobox(row, textvariable=size_var, values=["a4", "letter"],
                 width=7, state="readonly").pack(side="left")
    ttk.Label(row, text="Pages:").pack(side="left", padx=(12, 4))
    ttk.Spinbox(row, from_=1, to=10, textvariable=pages_var, width=4).pack(side="left")

    logbox = tk.Text(frm, height=6, state="disabled")
    logbox.pack(fill="both", expand=True)

    def log(msg):
        logbox.config(state="normal")
        logbox.insert("end", msg + "\n")
        logbox.see("end")
        logbox.config(state="disabled")
        root.update_idletasks()

    def go():
        if not files:
            messagebox.showinfo("NP → PR", "Add at least one PDF first.")
            return
        for f in files:
            try:
                convert(f, size=size_var.get(), n_pages=pages_var.get(), log=log)
            except Exception as e:  # noqa: BLE001
                log(f"  ERROR {os.path.basename(f)}: {e}")
        log("Done. The _PR files are next to the originals.")

    ttk.Button(frm, text="Convert to Print Ready", command=go).pack(pady=6)
    root.mainloop()


# ----------------------------------------------------------------- CLI ----
def main():
    ap = argparse.ArgumentParser(
        prog="np2pr",
        description="Split a stacked NP (No Print) character sheet into a "
                    "multi-page PR (Print Ready) PDF.",
        epilog="examples:\n"
               "  python np2pr.py                          open the GUI\n"
               "  python np2pr.py Benladen_NP.pdf          -> Benladen_PR.pdf (A4, 3 pages)\n"
               "  python np2pr.py *.pdf --size letter      convert several, US Letter\n"
               "  python np2pr.py a_NP.pdf -o out/         write results into out/\n"
               "  python np2pr.py a_NP.pdf --pages 4       sheet has 4 stacked pages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("files", nargs="*", help="input PDF(s), e.g. Benladen_NP.pdf")
    ap.add_argument("--size", choices=SIZES, default="a4", help="paper size (default a4)")
    ap.add_argument("--pages", type=int, default=3, help="number of pages stacked (default 3)")
    ap.add_argument("-o", "--outdir", help="output folder (default: next to the input)")
    args = ap.parse_args()

    if not args.files:
        return run_gui()

    for f in args.files:
        dst = None
        if args.outdir:
            os.makedirs(args.outdir, exist_ok=True)
            name = os.path.splitext(os.path.basename(f))[0]
            name = name[:-3] if name.upper().endswith("_NP") else name
            dst = os.path.join(args.outdir, name + "_PR.pdf")
        convert(f, dst, args.size, args.pages)


if __name__ == "__main__":
    main()

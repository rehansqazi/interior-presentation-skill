# AGENTS.md

Instructions for any AI coding agent (Codex, Cursor, Copilot, Gemini CLI, Claude Code, etc.) working in this repo or asked to build an interior presentation with it.

## What this repo does

`interior-presentation/scripts/build_deck.py` turns a project folder of reference images into an interior design concept board, written out as both a self-contained HTML file and a PDF (1440x810 slides). The full workflow is in [`interior-presentation/SKILL.md`](interior-presentation/SKILL.md). Follow that file whatever agent you are; it is plain Markdown.

There is also a no-install browser version at `docs/index.html` (served by GitHub Pages). It applies the same folder rules and layout in client-side JavaScript. **If you change layout or folder rules in `build_deck.py`, make the same change in `docs/index.html`** (the slide CSS is mirrored between the two).

## Setup

```bash
pip install pillow playwright
playwright install chromium
# optional, only for PDF plans: brew install poppler  |  apt install poppler-utils
```

## Building a presentation for a user

1. Ask for (or locate) the project root folder. Its expected layout:
   - `company/`: logos (`logo main.png` is used in the sidebar and on the cover; other logos go at the bottom of the cover) and `details.txt` with `key: value` lines (`project`, `client`, `subtitle`, `kicker`, `color`).
   - Every other folder (nested to any depth, e.g. floor → room → wall) that contains images becomes one slide, titled by the folder name, with its parent folders shown as a small location line. A leading number like `01 ` sets the order and is removed from the title.
   - Each top-level folder with sub-folders (e.g. a floor) gets a numbered divider slide.
   - Images whose names contain `sketch`, `plan`, `layout`, `drawing`, `elevation` or `section` go in the left plan panel. A `notes.txt` in a folder adds a notes column to that slide.
2. Run:
   ```bash
   python3 interior-presentation/scripts/build_deck.py "<project root>" "<output dir>" [--title "NAME"] [--side "#d1cdc1"]
   ```
3. Check the printed slide list against the folders, then look at the rendered pages, e.g. `pdftoppm -r 30 -png "<out>/<TITLE> PPT.pdf" preview`.
4. Give the user both output files. Don't invent notes text unless they ask for it.

## Testing changes to the script

```bash
python3 interior-presentation/scripts/build_deck.py "example/CLIENT RESIDENCE" out/
```
The run should report 7 slides (cover, 2 floor dividers, 4 content slides) with no errors. If you change the layout, regenerate `docs/preview.png` from the example output, and open `docs/index.html` in a browser and choose `example/CLIENT RESIDENCE` to check that the web version still matches.

## Conventions

- Keep the script a single dependency-light file (Pillow + Playwright only).
- Don't commit generated `*PPT.html` / `*PPT.pdf` files or real client images. Use placeholder images in `example/`.

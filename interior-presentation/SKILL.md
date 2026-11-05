---
name: interior-presentation
description: Build an interior design concept presentation (HTML + PDF) from a project folder of reference images, organised into section folders plus a company folder for logos and details.
---

# Interior concept presentation from a folder

Builds a board in a clean architectural-board style: a beige sidebar with the slide title in spaced vertical letters, the main logo at the bottom of the sidebar, and a white content area. Plans and sketches go in a bordered left panel, reference images fill a grid, and any notes go in a right column. The cover slide shows hero images, the project title and the logos. Output is `<PROJECT> PPT.html` and `<PROJECT> PPT.pdf` (1440x810 slides) saved in the project folder.

## Folder convention (tell the user this if they ask how to set it up)

```
<PROJECT ROOT>/                 e.g. "CLIENT RESIDENCE"
  company/                      logos + details (folder name: company / company details / company info)
    logo main.png               "main" or "primary" in the name -> sidebar + top-right of cover
    logo partner.png            other logos -> bottom-right of the cover
    details.txt                 "key: value" lines: project, client, subtitle, kicker, color (sidebar hex)
  01 BEDROOM/                   each folder that contains images = one slide, titled by folder name
    01 BED BACK WALL/           subfolders become their own slides (nest as deep as needed)
      bed back sketch.jpg       name contains sketch/plan/layout/drawing/elevation/section -> left panel
      ref 1.jpg ...
      notes.txt                 optional; paragraphs separated by a blank line -> notes column
    02 WARDROBE WALL/
  02 WALK IN CLOSET/
  03 BATH/
```
- A leading number (`01 `, `02_`) sets the order and is removed from the title.
- A PDF whose name contains "plan" or "sketch" is turned into an image from its first page and used as the plan.
- Folders with more than 6 reference images are split across extra slides.
- DWG files are ignored. If the user wants plans, ask them to export the plan from AutoCAD as a PDF or PNG into the right folder.

## Steps

1. **Find the root folder.** Use the path the user gives. List it recursively and check that it contains a `company` folder and section folders. If something is missing (no company folder, no logos, an empty section), tell the user and continue with what's there.
2. **Make sure the files are reachable.** The script needs Python 3 with Pillow and Playwright (Chromium), plus `pdftoppm` (poppler) for PDF plans. Run it wherever those are installed. If the project lives on a computer that can't run it, copy the folder (images, PDFs and txt/md/json files, keeping the structure) to an environment that can. Install anything missing with `pip install pillow playwright && playwright install chromium`.
3. **Run the bundled script** `scripts/build_deck.py` (in this skill's folder):
   `python3 scripts/build_deck.py "<project root>" "<project root>"` (optional: `--title "NAME"`, `--side "#d1cdc1"`).
   It prints the slide list, so check it against the folders.
4. **Check the result.** Render the PDF pages with `pdftoppm -r 30` and look at them. Look for awkward crops, empty slides, and titles too long for the sidebar (the font shrinks automatically, but very long names can still crowd it). Fix problems by adjusting the script for this run, and suggest folder renames if needed.
5. **Deliver.** Put both files in the project root, or give them to the user if they can't be written there. In one or two sentences, tell the user the slide count, anything that was skipped, and that adding notes.txt files or plans and re-running will update the deck.

Don't write descriptive notes text yourself unless the user asks. Slides without a notes.txt simply have no notes column.

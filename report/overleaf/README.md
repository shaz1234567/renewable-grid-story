# Overleaf package: The Renewable Grid, Hour by Hour

This folder is self-contained. It requires only:

- `main.tex`
- `references.bib`
- the six PNG files in `images/`

## Exact Overleaf upload and compile steps

1. Sign in at <https://www.overleaf.com/>.
2. Click **New Project** and choose **Upload Project**.
3. Upload `renewable-grid-story-overleaf.zip` from the parent `report/` folder. Do not unzip it first.
4. Open the uploaded project and click **Menu** in the upper-left.
5. Under **Settings**, set **Compiler** to **pdfLaTeX**.
6. Set **Main document** to `main.tex` if Overleaf does not select it automatically.
7. Click **Recompile**. Overleaf runs BibTeX automatically; if citations initially display as question marks, click **Recompile** once more.
8. Confirm that the bibliography appears at the end and that all six numbered figures render.
9. Use **Download PDF** to save the compiled submission.

No shell escape, custom fonts, external data files, or nonstandard document class is required. The source uses a conservative `article`/pdfLaTeX/BibTeX setup supported by Overleaf.

## Manual upload alternative

If uploading files instead of the ZIP:

1. Create a blank Overleaf project.
2. Upload `main.tex` and `references.bib` into the project root.
3. Create an `images` folder in Overleaf.
4. Upload all six PNG files from the local `images/` folder into that Overleaf folder without renaming them.
5. Select pdfLaTeX and compile as described above.

The Markdown and PDF reports outside this folder are the preserved source artifacts and are not needed for Overleaf compilation.

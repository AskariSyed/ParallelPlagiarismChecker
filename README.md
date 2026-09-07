# Parallel Plagiarism Checker

A Streamlit-based application that compares uploaded source files in parallel and reports pairwise similarity percentages to help identify potential plagiarism.

## Features

- Upload multiple code files from the UI.
- Parallel preprocessing and pairwise comparison.
- Similarity results table with filtering and top-N views.
- Per-file highest-match summary.
- Highlighted matching text view for selected file pairs.
- CSV export for generated result views.
- Basic processing metrics (time and CPU usage) by stage.

## Supported file types

- `.py`
- `.cpp`
- `.h`
- `.cc`
- `.cxx`
- `.java`

## Project structure

- `app/app.py` — Streamlit app entry point.
- `app/helper.py` — UI workflow, file handling, reporting helpers.
- `utils/preprocessing.py` — language-specific cleanup and normalization.
- `utils/comparison.py` — similarity comparison and CSV output.
- `utils/handwritten_pdf_handler.py` — OCR helper for handwritten PDFs.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
pip install plotly psutil pymupdf pillow pytesseract
```

If you plan to use OCR features, install the Tesseract binary on your system as well.

## Run

From the repository root:

```bash
streamlit run app/app.py
```

Then open the local Streamlit URL shown in your terminal.

## Output

- Uploaded files are stored in `data/uploads/`.
- Preprocessed files are stored in `data/preprocessed/`.
- Main similarity output is written to `data/results/similarity_results.csv`.

## Notes

- Similarity is currently computed using Python’s `difflib.SequenceMatcher`.
- Uploaded file size limit is 10 MB per file.

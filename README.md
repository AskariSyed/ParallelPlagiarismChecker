# Parallel Plagiarism Checker

A Streamlit application for detecting potential code plagiarism by preprocessing uploaded source files and comparing every file pair in parallel.

---

## What this project does

This tool helps instructors and reviewers quickly inspect similarity between programming submissions.  
It accepts multiple source files, normalizes the code to reduce superficial differences, computes pairwise similarity scores, and presents interactive views for analysis.

---

## Key capabilities

- Multi-file upload from the Streamlit sidebar.
- Extension and file-size validation before processing.
- Parallel preprocessing of submitted files.
- Parallel pairwise similarity computation.
- Summary metrics (total files, total pairs, highest similarity, high-similarity pair count).
- Interactive filtering by similarity range.
- Top-N most similar pair view.
- Per-file highest plagiarism match view.
- Side-by-side file comparison with optional highlighted matching text blocks.
- CSV downloads for filtered tables and top matches.
- Processing metrics by stage (elapsed time + CPU usage).

---

## Supported languages / file types

- Python (`.py`)
- C/C++ (`.cpp`, `.h`, `.cc`, `.cxx`)
- Java (`.java`)

Upload limit: **10 MB per file**.

---

## How similarity is calculated

1. Each file is preprocessed (comments/import boilerplate removal by language + whitespace normalization + lowercase conversion).
2. All file combinations are generated (`nC2` pairs).
3. Every pair is compared with `difflib.SequenceMatcher`.
4. Similarity is reported as a percentage (`0`–`100`).

The persisted CSV result stores:

- `File 1`
- `File 2`
- `Similarity %`

---

## Preprocessing behavior

Implemented in `utils/preprocessing.py`:

- **Python**
  - Removes `# ...` comments
  - Removes `import ...` and `from ... import ...` lines
- **C/C++**
  - Removes `// ...` and `/* ... */` comments
  - Removes `#include ...`
  - Removes `using namespace ...;`
- **Java**
  - Removes `// ...` and `/* ... */` comments
  - Removes `import ...;`
  - Removes `package ...;`
- **All files**
  - Converts to lowercase
  - Collapses multiple whitespace into single spaces

---

## UI workflow

1. Start app and upload multiple code files.
2. App validates extension and size.
3. Files are saved to `data/uploads/`.
4. Preprocessed outputs are written to `data/preprocessed/`.
5. Pairwise results are written to `data/results/similarity_results.csv`.
6. Dashboard sections render:
   - Summary statistics
   - Highest match per file
   - Similarity range filtering
   - Top-N most similar pairs
   - Similarities for one selected file
7. Users can download generated CSV views from the UI.

---

## Project structure

```text
ParallelPlagiarismChecker/
├── app/
│   ├── app.py                      # Streamlit entry point
│   ├── helper.py                   # Upload workflow, metrics, UI sections
│   └── highest_match_per_file_Result.csv
├── utils/
│   ├── preprocessing.py            # Cleaning/normalization + parallel preprocessing
│   ├── comparison.py               # Parallel pair comparison + CSV persistence
│   └── handwritten_pdf_handler.py  # OCR utility for handwritten PDFs
├── requirements.txt
└── README.md
```

---

## Installation

From repository root:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install plotly psutil pymupdf pillow pytesseract
```

### Optional OCR dependency

`utils/handwritten_pdf_handler.py` uses Tesseract OCR.  
If you use OCR flow, install system Tesseract separately (binary/engine), in addition to `pytesseract`.

---

## Run locally

```bash
streamlit run app/app.py
```

Then open the local Streamlit URL shown in terminal.

---

## Output artifacts

- `data/uploads/` → raw uploaded files
- `data/preprocessed/` → normalized files used for comparison
- `data/results/similarity_results.csv` → base pairwise similarity output
- `data/results/highest_match_per_file_Result.csv` → highest match summary per file
- `data/progress.json` → stage progress metadata during processing

---

## Technical notes and limitations

- Similarity is text-sequence based (`SequenceMatcher`), not semantic/AST aware.
- Boilerplate removal is rule-based regex preprocessing and may not catch all patterns.
- Runtime grows with file count because pair comparisons are combinational (`nC2`).
- OCR helper exists as a utility module and is not directly integrated into the Streamlit upload flow.

---

## Future improvement ideas

- Token/AST-based similarity for stronger plagiarism detection.
- Language-aware normalization beyond regex cleanup.
- Threshold-based alerting and report generation.
- Persistent history of runs and comparisons.
- Better duplicate-file detection and clustering views.

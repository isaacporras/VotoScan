# VotoScan

VotoScan is a Python desktop tool that helps automate vote tracking for the Legislative Assembly of Costa Rica from screenshots of the voting board.

It uses OCR to extract deputy names, matches them against a roster, assigns each vote, and exports the results as JSON, Excel, a labeled seat map, and a PDF report.

## What It Does

Given a screenshot of a plenary vote, VotoScan:

1. Detects the vote sections on screen.
2. Extracts deputy names with OCR.
3. Matches OCR output against the official deputy roster.
4. Classifies votes as `in_favor`, `against`, `abstention`, or `absent`.
5. Generates structured output files.

## Current Interface

The app now runs through a simple Tkinter interface.

From the UI you can:

- choose the voting screenshot
- choose the output folder
- set a session name
- process the image with a loading indicator
- preview the generated report image in the window
- open the generated PDF

Default output folder:

- `Downloads` on Windows

## Outputs

Each run generates these files in the selected output folder:

- `results.json`
- `results.xlsx`
- `asamblea_seats_labeled.png` if the seat template exists
- `voting_report.pdf`

## Project Structure

```text
VotoScan/
|-- assets/
|   |-- examples/
|   |   `-- votacion_1_example.PNG
|   `-- templates/
|       `-- asamblea_seats_template.png
|-- data/
|   `-- deputies.json
|-- models/
|   |-- __init__.py
|   |-- assembly.py
|   |-- political_party.py
|   |-- vote_choice.py
|   |-- voter.py
|   `-- voting_session.py
|-- tests/
|-- gui_app.py
|-- main.py
|-- paths.py
|-- processor.py
|-- seat_renderer.py
`-- text_extractor.py
```

## Requirements

Install Python dependencies:

```powershell
python -m pip install pytesseract pillow openpyxl
```

On Windows, install Tesseract OCR:

```powershell
winget install UB-Mannheim.TesseractOCR
```

If `tesseract.exe` is not in your `PATH`, you will need to add it manually.

## How To Run

Start the desktop app with:

```powershell
python main.py
```

Then:

1. Select a screenshot of the voting board.
2. Select the output folder.
3. Optionally change the session name.
4. Click `Process`.
5. Wait for the loading indicator to finish.
6. Review the preview and open the PDF if needed.

## Data Files

Deputy roster:

- `data/deputies.json`

Seat template:

- `assets/templates/asamblea_seats_template.png`

Example screenshot:

- `assets/examples/votacion_1_example.PNG`

## Internal Modules

- `gui_app.py`: Tkinter interface
- `processor.py`: end-to-end processing pipeline
- `text_extractor.py`: OCR extraction with Tesseract
- `seat_renderer.py`: labeled seat map rendering
- `models/`: domain models split by responsibility
- `paths.py`: shared project paths

## Tests

Run the test suite with:

```powershell
python -m unittest discover -s tests
```

## Notes

- OCR quality depends on screenshot clarity and board layout consistency.
- If the template image is missing, the app still generates JSON, Excel, and PDF using the source screenshot.
- Unmatched OCR names are preserved in `results.json` for manual review.

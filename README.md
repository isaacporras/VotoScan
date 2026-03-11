# VotoScan

Sistema en Python para automatizar el registro de votaciones de la Asamblea Legislativa de Costa Rica a partir de un screenshot.

## Estructura del proyecto

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
|-- output/
|   |-- results.json
|   |-- results.xlsx
|   `-- asamblea_seats_labeled.png
|-- tests/
|-- main.py
|-- paths.py
|-- seat_renderer.py
`-- text_extractor.py
```

`models/` ahora separa cada entidad en su propio archivo y `paths.py` concentra las rutas compartidas del proyecto.

## Como funciona

### 1. Padron de diputados

Se carga desde [data/deputies.json](/c:/Users/imano/OneDrive/Documentos/Projects/VotoScan/data/deputies.json) con:

- nombre del diputado
- partido politico
- numero de curul (`seat_number`)

Esto se gestiona con `Assembly`, `Voter`, `PoliticalParty` y `VotingSession` dentro del paquete `models`.

### 2. OCR del screenshot

`TextExtractor` en [text_extractor.py](/c:/Users/imano/OneDrive/Documentos/Projects/VotoScan/text_extractor.py) usa `pytesseract` para:

- detectar secciones (`a favor`, `en contra`, `no votacion`)
- extraer nombres por bloque o columna
- limpiar ruido comun de OCR

### 3. Asignacion de votos

`VotingSession.process_results()`:

- compara nombres OCR contra el padron
- usa similitud de texto para empatar nombres aunque tengan errores menores
- asigna voto por diputado (`in_favor`, `against`, `abstention`, `absent`)
- devuelve nombres no reconocidos para revision manual

### 4. Salidas

`main.py` genera por defecto:

- [output/results.json](/c:/Users/imano/OneDrive/Documentos/Projects/VotoScan/output/results.json)
- [output/results.xlsx](/c:/Users/imano/OneDrive/Documentos/Projects/VotoScan/output/results.xlsx)
- [output/asamblea_seats_labeled.png](/c:/Users/imano/OneDrive/Documentos/Projects/VotoScan/output/asamblea_seats_labeled.png) si existe la plantilla

## Requisitos

```powershell
python -m pip install pytesseract pillow openpyxl
```

En Windows, `pytesseract` requiere Tesseract OCR instalado:

```powershell
winget install UB-Mannheim.TesseractOCR
```

## Uso rapido

1. Ajusta en [main.py](/c:/Users/imano/OneDrive/Documentos/Projects/VotoScan/main.py) el nombre de la sesion o cambia las constantes en [paths.py](/c:/Users/imano/OneDrive/Documentos/Projects/VotoScan/paths.py).
2. Ejecuta:

```powershell
python main.py
```

3. Revisa la carpeta `output/`.

## Render de curules

`AssemblySeatRenderer` en [seat_renderer.py](/c:/Users/imano/OneDrive/Documentos/Projects/VotoScan/seat_renderer.py):

- lee la plantilla desde `assets/templates/`
- escribe el nombre del diputado segun su `seat_number`
- puede colorear cada curul segun el voto

## Tests

```powershell
python -m unittest discover -s tests
```

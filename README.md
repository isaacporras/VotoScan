# VotoScan

Sistema en Python para automatizar el registro de votaciones de la Asamblea Legislativa de Costa Rica a partir de un screenshot.

## Problema que resuelve

El flujo manual tradicional es:

1. Ver el video de la Asamblea.
2. Pausar en la pantalla de resultados.
3. Leer nombre por nombre.
4. Transcribir votos manualmente.

`VotoScan` reduce ese trabajo leyendo la imagen con OCR, mapeando cada nombre al padrón de diputados y generando una salida estructurada que luego puede exportarse a Excel.

## Como funciona

### 1) Padrón de diputados

Se carga desde `deputies.json` con:

- nombre del diputado
- partido politico
- numero de curul (`seat_number`)

Esto se gestiona con `Assembly` y `Voter` en `models.py`.

### 2) OCR del screenshot

`TextExtractor` (en `text_extractor.py`) usa `pytesseract` para:

- detectar secciones (`a favor`, `en contra`, `no votacion`)
- extraer nombres por bloque/columna
- limpiar ruido comun de OCR

### 3) Asignacion de votos

`VotingSession.process_results()`:

- compara nombres OCR contra el padrón
- usa similitud de texto para empatar nombres aunque tengan errores menores
- asigna voto por diputado (`in_favor`, `against`, `abstention`, `absent`)
- devuelve nombres no reconocidos para revision manual

### 4) Salida estructurada

`VotingSession.to_dict()` devuelve:

- metadata de la sesion
- conteo de votos
- votos individuales por diputado
- agrupaciones opcionales:
  - `group_by_parties=True` -> `votes_by_party`
  - `group_by_vote=True` -> `votes_by_choice`

Actualmente `main.py` escribe `results.json`.
Tambien exporta `results.xlsx`.

## Estado actual y siguiente paso (Excel)

Hoy la salida principal es JSON. El siguiente paso natural es convertir `results.json` a `.xlsx` (por ejemplo con `openpyxl` o `pandas`) para que tu amigo tenga el reporte listo para usar sin transcripcion manual.

## Requisitos

### Python

```powershell
python -m pip install pytesseract pillow openpyxl
```

### Sistema (Windows)

`pytesseract` requiere Tesseract OCR instalado:

```powershell
winget install UB-Mannheim.TesseractOCR
```

Ruta comun:

- `C:\Program Files\Tesseract-OCR\tesseract.exe`

## Uso rapido

1. Ajusta en `main.py`:
- `png_path` de la votacion
- `name` de la sesion
2. Ejecuta:

```powershell
python main.py
```

3. Revisa:
- `results.json`
- `results.xlsx`
- `unmatched_ocr_names` para corregir casos que el OCR no empato
- `asamblea_seats_labeled.png` (si existe `asamblea_seats_template.png`)

## Render de curules con nombres

El modelo `Assembly` ahora expone `get_seat_assignments()` para retornar la conformacion por curul (`seat_number`).

La clase `AssemblySeatRenderer`:

- lee una plantilla de curules
- detecta los circulos de asientos
- escribe el nombre del diputado debajo del circulo segun su `seat_number`
- puede colorear cada curul segun el voto:
  - verde: `in_favor`
  - rojo: `against`
  - gris: `abstention`/`absent`

Flujo:

1. Coloca la plantilla como `asamblea_seats_template.png` en la raiz del proyecto.
2. Ejecuta `python main.py`.
3. Se genera `asamblea_seats_labeled.png`.

## Exportar a Excel desde codigo

`VotingSession` ahora incluye:

```python
voting_session.to_excel(
    "results.xlsx",
    group_by_parties=True,
    group_by_vote=True,
)
```

Opciones:

- `group_by_parties=True`: agrega hoja `by_party`
- `group_by_vote=True`: agrega hoja `by_vote`

## Configurar PATH de Tesseract (Windows)

### Opcion A: Interfaz grafica

1. Buscar `Editar las variables de entorno del sistema`.
2. Abrir `Variables de entorno`.
3. Editar `Path` en variables del sistema.
4. Agregar: `C:\Program Files\Tesseract-OCR\`
5. Reabrir terminal.
6. Validar:

```powershell
tesseract --version
```

### Opcion B: PowerShell (admin)

```powershell
setx /M PATH "$($env:Path);C:\Program Files\Tesseract-OCR\"
```

Luego reabre la terminal y valida con `tesseract --version`.

## Error comun

Si ves `pytesseract.pytesseract.TesseractNotFoundError`, Python no esta encontrando `tesseract.exe`.

Soluciones:

- agregar Tesseract al `PATH`
- o definir la ruta manualmente en codigo

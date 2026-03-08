# VotoScan

Script simple en Python para extraer texto desde una imagen `.png` usando OCR.

## Dependencias

### Python
Instalar con:

```powershell
python -m pip install pytesseract pillow
```

Dependencias actuales:
- `pytesseract`
- `pillow`

### Sistema (Windows)
`pytesseract` necesita Tesseract OCR instalado localmente:

```powershell
winget install UB-Mannheim.TesseractOCR
```

Ruta comun esperada:
- `C:\Program Files\Tesseract-OCR\tesseract.exe`

## Uso

1. En [extract_png_text.py](c:/Users/imano/OneDrive/Documentos/Projects/VotoScan/extract_png_text.py), ajusta `ruta_imagen` al archivo `.png` que quieras leer.
2. Ejecuta:

```powershell
python extract_png_text.py
```

## Notas

- El OCR corre localmente, no usa servidor.
- Si agregamos nuevas librerias, las iremos sumando en la seccion **Dependencias** de este README.

## Error comun: Tesseract no esta en PATH

Si aparece:
- `pytesseract.pytesseract.TesseractNotFoundError`

Significa que Python no encuentra `tesseract.exe` en el `PATH`.

Opciones:
- Agregar `C:\Program Files\Tesseract-OCR\` al `PATH` de Windows.
- O fijar la ruta en el script:

```python
ruta_tesseract = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if ruta_tesseract.exists():
    pytesseract.pytesseract.tesseract_cmd = str(ruta_tesseract)
```

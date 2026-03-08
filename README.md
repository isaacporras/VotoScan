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

1. En [main.py](c:/Users/imano/OneDrive/Documentos/Projects/VotoScan/main.py), ajusta `image_path` al archivo `.png` que quieras leer.
2. Ejecuta:

```powershell
python main.py
```

## Notas

- El OCR corre localmente, no usa servidor.
- Si agregamos nuevas librerias, las iremos sumando en la seccion **Dependencias** de este README.

## Configurar variables del sistema (Windows)

Para que cualquier usuario pueda ejecutar el OCR sin tocar el codigo, agrega Tesseract al `PATH`.

### Opcion A: Interfaz grafica (recomendada)

1. Abre el menu de Windows y busca: `Editar las variables de entorno del sistema`.
2. En la ventana **Propiedades del sistema**, entra a **Variables de entorno...**.
3. En **Variables del sistema**, selecciona `Path` y haz clic en **Editar...**.
4. Haz clic en **Nuevo** y agrega esta ruta:
   - `C:\Program Files\Tesseract-OCR\`
5. Guarda con **Aceptar** en todas las ventanas.
6. Cierra y vuelve a abrir la terminal para que tome el cambio.
7. Verifica:

```powershell
tesseract --version
```

### Opcion B: PowerShell (administrador)

Tambien puedes agregarlo por comando:

```powershell
setx /M PATH "$($env:Path);C:\Program Files\Tesseract-OCR\"
```

Luego cierra y abre la terminal, y valida con:

```powershell
tesseract --version
```

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

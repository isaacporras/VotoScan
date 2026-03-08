from pathlib import Path

from PIL import Image
import pytesseract
from pytesseract import Output

ruta_tesseract = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if ruta_tesseract.exists():
    pytesseract.pytesseract.tesseract_cmd = str(ruta_tesseract)

ruta_imagen = Path("votacion_1_example.PNG")
imagen = Image.open(ruta_imagen)

datos = pytesseract.image_to_data(
    imagen,
    output_type=Output.DICT,
    config="--oem 3 --psm 6",
)

tokens = []
for i, texto in enumerate(datos["text"]):
    texto = texto.strip()
    if not texto:
        continue

    conf = int(datos["conf"][i]) if datos["conf"][i] != "-1" else -1
    if conf < 0:
        continue

    tokens.append(
        {
            "text": texto,
            "left": datos["left"][i],
            "top": datos["top"][i],
            "height": datos["height"][i],
        }
    )

tokens.sort(key=lambda t: (t["top"], t["left"]))
linea_tolerancia = max(
    12,
    int(sum(t["height"] for t in tokens) / max(1, len(tokens)) * 0.6),
)
lineas = []

for token in tokens:
    if not lineas:
        lineas.append({"y": token["top"], "tokens": [token]})
        continue

    if abs(token["top"] - lineas[-1]["y"]) <= linea_tolerancia:
        lineas[-1]["tokens"].append(token)
        lineas[-1]["y"] = int((lineas[-1]["y"] + token["top"]) / 2)
    else:
        lineas.append({"y": token["top"], "tokens": [token]})

texto_en_variable = "\n".join(
    " ".join(t["text"] for t in sorted(linea["tokens"], key=lambda x: x["left"]))
    for linea in lineas
)

ruta_salida = Path("resultado_ocr.txt")
ruta_salida.write_text(texto_en_variable, encoding="utf-8")

print(f"Texto guardado en: {ruta_salida.resolve()}")

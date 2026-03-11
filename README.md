# VotoScan

Sistema en Python para **automatizar el registro de votaciones del plenario de la Asamblea Legislativa de Costa Rica** a partir de un screenshot.

Este proyecto nace como un pequeño regalo para el equipo de **Delfino.CR**, que durante años ha llevado un seguimiento riguroso y transparente de las votaciones legislativas.

---

# ¿Por qué existe este proyecto?

El registro de votaciones del plenario suele implicar un proceso bastante manual:

1. Ver el video de la sesión legislativa.
2. Esperar a que aparezca el tablero de votación.
3. Pausar el video.
4. Revisar diputado por diputado.
5. Anotar manualmente cada voto.

Cuando esto se hace para **muchas votaciones**, el proceso puede volverse lento y repetitivo.

**VotoScan** intenta simplificar ese trabajo.

> A partir de un screenshot del tablero de votación, el sistema detecta los nombres de los diputados, identifica su voto y genera automáticamente archivos estructurados con los resultados.

---

# ¿Qué hace VotoScan?

A partir de una imagen del tablero de votación, el sistema:

1. Extrae los nombres de los diputados usando **OCR**
2. Identifica el tipo de voto de cada uno
3. Cruza esa información con el padrón de diputados
4. Genera distintos formatos de salida

### Salidas generadas

El sistema produce automáticamente:

- **JSON** (ideal para integrarlo con sitios web)
- **Excel** (para análisis y revisión rápida)
- **Imagen de la Asamblea etiquetada** mostrando cada curul y su voto

---

# Ejemplo de flujo

## 1. Screenshot de la votación

Coloca un screenshot del tablero de votación dentro de:

assets/examples/

Ejemplo:

assets/examples/votacion_1_example.PNG

---

## 2. Procesamiento automático

El sistema:

- detecta bloques de votación (`a favor`, `en contra`, etc.)
- extrae nombres de diputados
- corrige errores comunes de OCR
- asigna votos al padrón de diputados

---

## 3. Resultados generados

Después de ejecutar el sistema se generan automáticamente:

output/results.json  
output/results.xlsx  
output/asamblea_seats_labeled.png  

---

# Dependencias

Instala las dependencias de Python:

    python -m pip install pytesseract pillow openpyxl

En Windows también debes instalar **Tesseract OCR**:

    winget install UB-Mannheim.TesseractOCR

---

# Cómo ejecutarlo

1. Clona el repositorio

    git clone https://github.com/tuusuario/VotoScan
    cd VotoScan

2. Coloca el screenshot de votación en:

    assets/examples/

3. Ejecuta el programa:

    python main.py

4. Revisa los resultados en:

    output/

---

# Cómo funciona internamente

## 1. Padrón de diputados

Se carga desde:

    data/deputies.json

Contiene:

- nombre del diputado
- partido político
- número de curul

---

## 2. OCR del screenshot

El módulo `TextExtractor` usa **pytesseract** para:

- detectar secciones de votación
- extraer nombres de diputados
- limpiar ruido típico del OCR

---

## 3. Asignación de votos

El sistema compara los nombres detectados contra el padrón y usa **similitud de texto** para empatar nombres aunque el OCR tenga errores menores.

Cada diputado queda clasificado como:

- in_favor
- against
- abstention
- absent

---

## 4. Render del plenario

Opcionalmente se genera una imagen de la Asamblea donde cada curul aparece etiquetada según el voto.

Esto se hace con:

    seat_renderer.py

---

# Tests

Ejecutar:

    python -m unittest discover -s tests

---

# Nota final

Este proyecto fue creado con el objetivo de **facilitar el seguimiento de votaciones legislativas** y apoyar el trabajo de transparencia que realiza el equipo de **Delfino.CR**.

Si este proyecto ayuda aunque sea un poco a reducir el trabajo manual en ese proceso, entonces ya cumplió su propósito.
import chardet
import pandas as pd

INPUT_CSV = "BD_PRUEBA_.csv"

# 1. Detección automática de Encoding
with open(INPUT_CSV, 'rb') as f:
    raw_data = f.read(100000)  # Lee los primeros 100 KB
    result = chardet.detect(raw_data)
    print(f"--- DETECCIÓN DE ENCODING ---")
    print(f"Encoding detectado: {result['encoding']} (confianza: {result['confidence'] * 100:.1f}%)\n")

# 2. Prueba de lectura con 'latin1' (soporta cualquier byte sin lanzar UnicodeDecodeError)
df_preview = pd.read_csv(INPUT_CSV, nrows=5, dtype=str, encoding='latin1')

print("--- PROPIEDADES DEL CSV ---")
print(f"Columnas detectadas ({len(df_preview.columns)}):")
print(list(df_preview.columns)[:10], "... (primeras 10)")

print("\n--- MUESTRA DE DATOS CON TEXTO Y ACENTOS ---")
# Buscar filas o columnas que tengan texto para verificar visualmente los acentos
print(df_preview.iloc[:3, :6])
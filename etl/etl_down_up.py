"""
Descripción:
  1.Este escript lee un archivo CSV de origen y a partir de este se generan 3 csv de salida, 
  un csv para cada tabla de la bd.

  2. Después de generar los CSVs y se guardan en ./DATA, realiza la carga masiva de los datos con la cláusula COPY de PostgreSQL.

  3. Finalmente genera 2 arhivos un .sql y .dump

Ejecución:
  python etl_down_up.py

Salida: 
  ./DATA/cid_state.csv
  ./DATA/cid_geography.csv
  ./DATA/fid_population_census.csv
  ./DATA/idtest_db_dump.sql
  ./DATA/idtest_db_dump.dump

Nota: El servidor de BD y el esquema deben estar creados previamente.
"""

import os
import subprocess
import pandas as pd
import psycopg2
from aux import POPULATION_CENSUS_COLS_CSV, POPULATION_CENSUS_COLS_BD, POPULATION_CENSUS_COLS_INS

# ---------------------------------------------------------
# 1. Configuración de Archivos y Conexión a la DB
# ---------------------------------------------------------
INPUT_CSV = "BD_PRUEBA_.csv"
AUDIT_DATE = "2026-09-29 02:50:00"
PATH_DEST = "./DATA/"
DUMP_FILE = os.path.join(PATH_DEST, "idtest_db_dump.sql")
DUMP_FILE2 = os.path.join(PATH_DEST, "idtest_db_dump.dump")
DOCKER_CONTAINER = "idtest_db"

# Credenciales BD
DB_CONFIG = {
  "dbname": "idtest_db",
  "user": "postgres",
  "password": "postgres_password",
  "host": "127.0.0.1",
  "port": "5432"
}

SCHEMA = "idtest"

# Nombres de los CSVs procesados a partir del original
# se genera un archivo por cada tabla que tenemos en la BD
CSV_STATE = PATH_DEST+"cid_state.csv"
CSV_GEOGRAPHY = PATH_DEST+"cid_geography.csv"
CSV_CENSUS = PATH_DEST+"fid_population_census.csv"


def get_data_from_source():
  print(" Generando archivos CSV a partir del original...")
  df = pd.read_csv(INPUT_CSV, dtype=str, encoding='latin1')  # Leemos todo como string para preservar ceros a la izquierda

  #limpieza de datos para la e con tilde
  df = df.replace({
    'ï¿½': 'é'  # Reemplazo general si la secuencia rota siempre equivale a una 'é'
  }, regex=True)

  # ---------------------------------------------------------
  # A) Generar CID_STATE
  # ---------------------------------------------------------
  # definimmos el dataframe con los nombres de las columnas en el csv
  df_state = df[['cve_ent', 'gid', 'nom_ent', 'nombre_igg']].copy()
  # definimos los nombres que tendra cada columna en la BD
  df_state.columns = ['CCK_CVE_ENT','CIN_GID','CVC_NOM_ENT','CVC_NOMBRE_IGG']
  # definimos la fecha por defecto para el audit record 
  df_state['CDT_AUDIT_RECORD'] = AUDIT_DATE
  
  # Eliminar duplicados para mantener solo estados únicos
  df_state = df_state.drop_duplicates(subset=['CCK_CVE_ENT'])
  # Generamos el CSV, como defino que si se guarde en csv utf-8 delimitado por | en vez de , ?
  df_state.to_csv(CSV_STATE, index=False, header=False, sep='|', encoding=' utf-8') # utf-8
  print(f"-> {CSV_STATE} generado ({len(df_state)} registros).")

  # ---------------------------------------------------------
  # B) Generar CID_GEOGRAPHY
  # ---------------------------------------------------------
  df_geography = df[['cve_ent', 'cve_mun', 'nomgeo', 'epsg', 'cvegeo', 'id']].copy()
  df_geography.columns = [ 'CFK_CVE_ENT', 'CBI_CVE_MUN' ,'CVC_NOMGEO' ,'CIN_EPSG', 'CCK_CVEGEO','CIN_ID']
  df_geography['CDT_AUDIT_RECORD'] = AUDIT_DATE
      
  # Eliminar duplicados para mantener geografías únicas
  df_geography = df_geography.drop_duplicates(subset=['CCK_CVEGEO']) 
  df_geography.to_csv(CSV_GEOGRAPHY, index=False, header=False, sep='|', encoding='utf-8')
  print(f"-> {CSV_GEOGRAPHY} generado ({len(df_geography)} registros).")

  # ---------------------------------------------------------
  # C) Generar FID_POPULATION_CENSUS
  # ---------------------------------------------------------
  # AL ser demasiadas columnas nos auxiliamos de otro archivo (aux.py)
  # que solo contiene las columnas del csv y de la BD que usareos
  # para esta table de censo
  df_census = df[POPULATION_CENSUS_COLS_CSV].copy()
  df_census.columns = POPULATION_CENSUS_COLS_BD
  df_census['FDT_AUDIT_RECORD'] = AUDIT_DATE
      
  # Limpieza o casting de nulos a formato CSV comprensible por Postgres
  df_census.to_csv(CSV_CENSUS, index=False, header=False, sep='|', encoding='utf-8')
  print(f"-> {CSV_CENSUS} generado ({len(df_census)} registros).")


def load_to_db():
  print("\nIniciando carga masiva con COPY en PostgreSQL...")
  conn = psycopg2.connect(**DB_CONFIG)
  cursor = conn.cursor()

  try:
    # Orden respetando llaves foráneas: STATE -> GEOGRAPHY -> CENSUS
    tablas_y_csvs = [
      (f"{SCHEMA}.cid_state", CSV_STATE, "CCK_CVE_ENT, CIN_GID, CVC_NOM_ENT, CVC_NOMBRE_IGG, CDT_AUDIT_RECORD"),
      (f"{SCHEMA}.cid_geography", CSV_GEOGRAPHY, "CFK_CVE_ENT, CBI_CVE_MUN, CVC_NOMGEO, CIN_EPSG, CCK_CVEGEO, CIN_ID, CDT_AUDIT_RECORD"),
      (f"{SCHEMA}.fid_population_census", CSV_CENSUS, POPULATION_CENSUS_COLS_INS )
    ] 

    for tabla, csv_file, columnas in tablas_y_csvs:
      print(f"Cargando {csv_file} en {tabla}...")
      with open(csv_file, 'r', encoding='utf-8') as f:
        sql_copy = f"""
          COPY {tabla} ({columnas})
          FROM STDIN
          WITH (FORMAT csv, HEADER false, DELIMITER '|', ENCODING 'UTF8', NULL '');
        """
        cursor.copy_expert(sql_copy, f)
      print(f"- Carga completa en {tabla}.")

    conn.commit()
    print("\n Proceso finalizado exitosamente con commit a la BD.")

  except Exception as e:
    conn.rollback()
    print(f"\n Error durante la carga. Se hizo Rollback. Detalle: {e}")
  finally:
    cursor.close()
    conn.close()

def generate_dump():
  print(f"\nGenerando data dump en {DUMP_FILE}...")
    
  # Comando pg_dump ejecutado dentro del contenedor enviando la salida al archivo local
  # -U postgres: usuario
  # -d idtest_db: base de datos
  # -n idtest: si solo quieres exportar el esquema 'idtest' (Opcional, quítalo si quieres toda la BD)
  # --clean --if-exists: útil para regenerar esquemas fácilmente
  cmd = [
    "docker", "exec", "-t", DOCKER_CONTAINER,
    "pg_dump",
    "-U", DB_CONFIG["user"],
    "-d", DB_CONFIG["dbname"],
    "-n", SCHEMA,  # Exporta únicamente el esquema 'idtest'
    "--clean",
    "--if-exists"
  ]

  cmd2 = [
    "docker", "exec", "-t", DOCKER_CONTAINER,
    "pg_dump",
    "-U", DB_CONFIG["user"],
    "-d", DB_CONFIG["dbname"],
    "-n", SCHEMA,
    "-F", "c",          # <--- Formato Custom (Binario comprimido)
    "-f", f"/tmp/dump.dump"
  ]

  try:
    with open(DUMP_FILE, "w", encoding="utf-8") as outfile:
      result = subprocess.run(cmd, stdout=outfile, stderr=subprocess.PIPE, text=True, check=True)

    with open(DUMP_FILE2, "w", encoding="utf-8") as outfile:
      result = subprocess.run(cmd2, stdout=outfile, stderr=subprocess.PIPE, text=True, check=True)

    print(f" Data dump generado exitosamente en: {DUMP_FILE}, {DUMP_FILE2}")

  except subprocess.CalledProcessError as e:
    print(f" Error generando el dump de la BD. Detalle: {e.stderr}")
  except Exception as e:
    print(f" Ocurrió un error inesperado al generar el dump: {e}")

if __name__ == "__main__":
  get_data_from_source()
  load_to_db()
  generate_dump()
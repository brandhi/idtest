CREATE OR REPLACE PROCEDURE IDTEST.SP_GET_FEMALE_POPULATION(
  OUT   p_status_code   INT,
  OUT   p_status_message   VARCHAR,
  INOUT p_refcursor  REFCURSOR DEFAULT 'ref_top10_female',
  IN  p_limit   INT DEFAULT 10         -- Parámetro de entrada con default 10
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_state   TEXT;
  v_msg     TEXT;
  v_detail  TEXT;
BEGIN
  -- 1. Inicialización de variables de control
  p_status_code := 0;
  p_status_message := 'Operación ejecutada con éxito.';

  -- 2. Apertura del cursor dinámico usando COALESCE para mayor seguridad si p_limit viene explícitamente como NULL
  OPEN p_refcursor FOR
    SELECT 
      g.cvc_nomgeo            AS colonia,
      g.cbi_cve_mun           AS municipio_num,
      e.cvc_nom_ent           AS estado,
      MAX(c.fbi_p_15a49_f)    AS total_poblacion_femenina_15a49 -- Asumiendo que esta columna contiene el precalculo por cada colonia.
    FROM IDTEST.FID_POPULATION_CENSUS c
    INNER JOIN IDTEST.CID_GEOGRAPHY g 
      ON  c.ffk_cvegeo = g.cck_cvegeo 
    INNER JOIN IDTEST.CID_STATE e 
      ON g.cfk_cve_ent = e.cck_cve_ent 
    WHERE LOWER(TRIM(g.cvc_nomgeo)) NOT IN ('sin nombre', 'sin nombre (en construccion)', 'ninguno', '')
      AND g.cvc_nomgeo IS NOT NULL
    GROUP BY 
      g.cvc_nomgeo,
      g.cbi_cve_mun,
      e.cvc_nom_ent
    ORDER BY 
      total_poblacion_femenina_15a49 DESC
    LIMIT COALESCE(p_limit, 10);

EXCEPTION
  WHEN OTHERS THEN
    -- Captura de diagnósticos y pila de error
    GET STACKED DIAGNOSTICS 
      v_state  = RETURNED_SQLSTATE,
      v_msg = MESSAGE_TEXT,
      v_detail = PG_EXCEPTION_DETAIL;

    -- Formato de respuesta de error
    p_status_code := -1;
    p_status_message := FORMAT('Error [%s]: %s. Detalle: %s', v_state, v_msg, COALESCE(v_detail, 'Sin detalle adicional'));

    RAISE WARNING 'Excepción capturada en SP_GET_FEMALE_POPULATION: %', p_status_message;
END;
$$;


/*
Ejecución:

BEGIN;

-- 1. Invocas el procedimiento almacenado
CALL IDTEST.SP_GET_FEMALE_POPULATION(
    p_status_code    => NULL, 
    p_status_message => NULL, 
    p_refcursor      => 'ref_top10_female',
    p_limit          => NULL -- podemos modificar este parametro con el númmero que queramos , el default es 10
);

-- 2. Lees el contenido del cursor abierto
FETCH ALL FROM "ref_top10_female";

-- 3. Cierras la transacción
COMMIT;



*/
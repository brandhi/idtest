/********************************************************************************
  INCISO C: Totales absolutos por entidad de variables demográficas clave.
  
  Nota: Se aplica MAX() asumiendo valores consolidados a nivel Entidad.
  En caso de tener la granularidad a nivel localidad/colonia, usuariamos SUM().
********************************************************************************/

CREATE OR REPLACE PROCEDURE IDTEST.SP_GET_DEMOGRAPHICS(
  OUT   p_status_code   INT,
  OUT   p_status_message   VARCHAR,
  INOUT p_refcursor  REFCURSOR DEFAULT 'ref_demographics_point_c'
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_state   TEXT;
  v_msg  TEXT;
  v_detail  TEXT;
BEGIN
  p_status_code := 0;
  p_status_message := 'Operación ejecutada con éxito.';

  OPEN p_refcursor FOR
    SELECT 
      e.cvc_nom_ent               AS nombre_igg,
      MAX(c.fbi_p_total)          AS p_total,
      MAX(c.fbi_pobmas)           AS pobmas,
      MAX(c.fbi_p_5ymas_f)        AS p_5ymas_f,
      MAX(c.fbi_p_15ymas)         AS p_15ymas
    FROM IDTEST.FID_POPULATION_CENSUS c
    INNER JOIN IDTEST.CID_GEOGRAPHY g 
      ON c.ffk_cvegeo = g.cck_cvegeo
    INNER JOIN IDTEST.CID_STATE e 
      ON g.cfk_cve_ent = e.cck_cve_ent
    GROUP BY 
      e.cck_cve_ent,
      e.cvc_nom_ent
    ORDER BY 
      p_total DESC;

EXCEPTION
  WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS 
      v_state  = RETURNED_SQLSTATE,
      v_msg = MESSAGE_TEXT,
      v_detail = PG_EXCEPTION_DETAIL;

    p_status_code := -1;
    p_status_message := FORMAT('Error [%s]: %s. Detalle: %s', v_state, v_msg, COALESCE(v_detail, 'Sin detalle adicional'));

    RAISE WARNING 'Excepción capturada en SP_GET_DEMOGRAPHICS: %', p_status_message;
END;
$$;


/*
Ejecución:

BEGIN;

-- 1. Invocas el procedimiento almacenado
CALL IDTEST.SP_GET_DEMOGRAPHICS(
  p_status_code => NULL, 
  p_status_message => NULL, 
  p_refcursor   => 'ref_demographics_point_c'
);

-- 2. Lees el contenido del cursor abierto
FETCH ALL FROM "ref_demographics_point_c";

-- 3. Cierras la transacción
COMMIT;



*/
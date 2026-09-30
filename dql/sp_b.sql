/********************************************************************************
  SUPUESTO DE DATOS:
  Se asume que la tabla IDTEST.FID_POPULATION_CENSUS cuenta con las métricas 
  demográficas (p_total, pcon_lim, pclim_*) precalculadas y consolidadas a nivel
  Entidad Federativa (Estado).
  
  Por esta razón, se utiliza la función de agregación MAX() agrupada por estado, 
  evitando la duplicidad o sobreconteo (fan-out) que ocurriría al aplicar SUM() 
  sobre las distintas geometrías/colonias asociadas a una misma entidad.
********************************************************************************/

CREATE OR REPLACE PROCEDURE IDTEST.SP_GET_DISABILITY_BY_STATE(
  OUT   p_status_code   INT,
  OUT   p_status_message   VARCHAR,
  INOUT p_refcursor  REFCURSOR DEFAULT 'ref_disability_state'
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

  -- Se asume agregación previa a nivel entidad; se usa MAX() para extraer el valor escalar único.
  OPEN p_refcursor FOR
    SELECT 
    e.cvc_nom_ent                                       AS estado,
    MAX(c.fbi_p_total )                                 AS poblacion_total,
    -- Totales absolutos por condición
    MAX(c.fbi_pcon_lim)                                 AS total_con_discapacidad,
    MAX(c.fbi_pclim_mot)                                AS dis_motriz,
    MAX(c.fbi_pclim_vis)                                AS dis_visual,
    MAX(c.fbi_pclim_aud)                                AS dis_auditiva,
    MAX(c.fbi_pclim_leng)                               AS dis_lenguaje,
    MAX(c.fbi_pclim_men)                                AS dis_mental,
    -- Porcentajes sobre la población total del estado
    ROUND((MAX(c.fbi_pcon_lim)::NUMERIC / NULLIF(MAX(c.fbi_p_total), 0)) * 100, 2)    AS pct_con_discapacidad,
    ROUND((MAX(c.fbi_pclim_mot)::NUMERIC / NULLIF(MAX(c.fbi_p_total), 0)) * 100, 2)   AS pct_motriz,
    ROUND((MAX(c.fbi_pclim_vis)::NUMERIC / NULLIF(MAX(c.fbi_p_total), 0)) * 100, 2)   AS pct_visual,
    ROUND((MAX(c.fbi_pclim_aud)::NUMERIC / NULLIF(MAX(c.fbi_p_total), 0)) * 100, 2)   AS pct_auditiva,
    ROUND((MAX(c.fbi_pclim_leng)::NUMERIC / NULLIF(MAX(c.fbi_p_total), 0)) * 100, 2)  AS pct_lenguaje,
    ROUND((MAX(c.fbi_pclim_men)::NUMERIC / NULLIF(MAX(c.fbi_p_total), 0)) * 100, 2)   AS pct_mental
    FROM IDTEST.FID_POPULATION_CENSUS c
    INNER JOIN IDTEST.CID_GEOGRAPHY g 
    ON c.ffk_cvegeo = g.cck_cvegeo
    INNER JOIN IDTEST.CID_STATE e 
    ON g.cfk_cve_ent = e.cck_cve_ent
    GROUP BY 
    e.cck_cve_ent,
    e.cvc_nom_ent
    ORDER BY 
      pct_con_discapacidad DESC;

EXCEPTION
  WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS 
      v_state  = RETURNED_SQLSTATE,
      v_msg = MESSAGE_TEXT,
      v_detail = PG_EXCEPTION_DETAIL;

    p_status_code := -1;
    p_status_message := FORMAT('Error [%s]: %s. Detalle: %s', v_state, v_msg, COALESCE(v_detail, 'Sin detalle adicional'));

    RAISE WARNING 'Excepción capturada en SP_GET_DISABILITY_BY_STATE: %', p_status_message;
END;
$$;


/*
Ejecución:

BEGIN;

-- 1. Invocas el procedimiento almacenado
CALL IDTEST.SP_GET_DISABILITY_BY_STATE(
  p_status_code => NULL, 
  p_status_message => NULL, 
  p_refcursor   => 'ref_disability_state'
);

-- 2. Lees el contenido del cursor abierto
FETCH ALL FROM "ref_disability_state";

-- 3. Cierras la transacción
COMMIT;



*/
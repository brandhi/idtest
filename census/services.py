from django.db import connection, transaction

class CensusService:

    @staticmethod
    def get_female_population(limit=10):
        """Ejecuta SP_GET_FEMALE_POPULATION (Inciso A)"""
        with transaction.atomic():
          with connection.cursor() as cursor:
              cursor.execute("""
                  CALL IDTEST.SP_GET_FEMALE_POPULATION(
                      p_status_code => NULL,
                      p_status_message => NULL,
                      p_refcursor => 'ref_top_female',
                      p_limit => %s
                  );
              """, [limit])
              
              cursor.execute('FETCH ALL FROM "ref_top_female";')
              columns = [col[0] for col in cursor.description]
              return [dict(zip(columns, row)) for row in cursor.fetchall()]

    @staticmethod
    def get_disability_by_state():
      """Ejecuta SP_GET_DISABILITY_BY_STATE (Inciso B)"""

      # OBLIGATORIO: Mantener la transacción abierta durante el CALL y el FETCH
      with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("""
                CALL IDTEST.SP_GET_DISABILITY_BY_STATE(
                    p_status_code => NULL,
                    p_status_message => NULL,
                    p_refcursor => 'ref_disability_state'
                );
            """)
            cursor.execute('FETCH ALL FROM "ref_disability_state";')
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    @staticmethod
    def get_demographics():
        """Ejecuta SP_GET_DEMOGRAPHICS (Inciso C)"""
        with transaction.atomic():
          with connection.cursor() as cursor:
              cursor.execute("""
                  CALL IDTEST.SP_GET_DEMOGRAPHICS(
                      p_status_code => NULL,
                      p_status_message => NULL,
                      p_refcursor => 'ref_demographics'
                  );
              """)
              cursor.execute('FETCH ALL FROM "ref_demographics";')
              columns = [col[0] for col in cursor.description]
              return [dict(zip(columns, row)) for row in cursor.fetchall()]
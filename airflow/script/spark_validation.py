from python_class.common import Get_env
from python_class.postgres_hook import PostgresHook

import argparse, json
from pyspark.sql import SparkSession
from concurrent.futures import ThreadPoolExecutor

# ==================================================
# Argument
# ==================================================
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tables", required=True)
    parser.add_argument("--dt", required=True)
    return parser.parse_args()

# ==================================================
# Count 체크
# ==================================================
def check_table(spark, table, dt):
    try:
        log_type = table

        staging_query = f"""
            SELECT count(*) as cnt
            FROM staging
            WHERE substr(`timestamp`, 1, 10) = '{dt[:4]}-{dt[4:6]}-{dt[6:]}'
            AND log_type = '{log_type}'
        """

        raw_query = f"""
            SELECT count(*) as cnt
            FROM raw_{table}
            WHERE dt = '{dt}'
        """

        parquet_query = f"""
            SELECT count(*) as cnt
            FROM {table}
            WHERE dt = '{dt}'
        """

        s = spark.sql(staging_query).collect()[0]["cnt"]
        r = spark.sql(raw_query).collect()[0]["cnt"]
        p = spark.sql(parquet_query).collect()[0]["cnt"]

        return (table, s, r, p)

    except Exception as e:
        print(f"[ERROR] checking table {table}: {e}") # 에러 메시지 로그 출력
        return (table, s, r, p)

# ==================================================
# PostgreSQL 저장 (UPSERT)
# ==================================================
def save_to_postgres(results, dt, postgresql):
    insert_sql = """
    INSERT INTO job.validation_row_count
    (table_name, stage_count, raw_count, analysis_count, dt)
    VALUES %s
    ON CONFLICT (table_name, dt)
    DO UPDATE SET
        stage_count = EXCLUDED.stage_count,
        raw_count = EXCLUDED.raw_count,
        analysis_count = EXCLUDED.analysis_count
    """

    data = [(table, s, r, p, dt) for table, s, r, p in results]
    postgresql.bulk_insert(insert_sql, data)
    postgresql.commit() # 커밋

# ==================================================
# Main
# ==================================================
def main():
    try:
        # ===============================
        # 환경 변수 및 설정 로드
        # ===============================
        pg_env = Get_env._postgres()
        print(pg_env)

        # ===============================
        # Postgresql 연결
        # ===============================
        postgresql = PostgresHook(
            pg_env["pg_host"],
            pg_env["pg_port"],
            pg_env["pg_db"],
            pg_env["pg_user"],
            pg_env["pg_password"]
        )
        postgresql.connect()
        print("PostgreSQL 연결 완료")

        args = get_args()
        tables = args.tables.split(",")
        dt = args.dt

        spark = (
            SparkSession.builder
            .appName("hive_validation")
            .enableHiveSupport()
            .getOrCreate()
        )

        results = [] # 멀티 스레드 결과 저장
    
        # 병렬 처리 (IO 바운드라 멀티스레드 적합)
        # → 분산엔진이 CPU 바운드 작업 처리 ( 파이썬 드리이버가 CPU 작업 안함 )
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(check_table, spark, t, dt)
                for t in tables
            ]

            for f in futures:
                results.append(f.result())

        spark.stop()
    
        print(results)
        save_to_postgres(results, dt, postgresql)

    except Exception as e:
        print(f"Error checking {e}")

    finally:
        postgresql.close()
        print(f"프로세스 종료, 모든 자원 반납 완료.")


# 파일 직접 실행할때만 아래 코드 실행
if __name__ == "__main__":
    main() 

from __future__ import annotations

from airflow.decorators import dag, task
from airflow.providers.ssh.operators.ssh import SSHOperator
from airflow.utils.task_group import TaskGroup
from airflow.models import Variable
from datetime import datetime
import json

@dag(
    dag_id = "hive_msck_repair_v2",
    start_date = datetime(2026, 4, 21),
    schedule = "0 1 * * *",
    catchup = False,
    tags = ["hive", "msck", "dynamic", "ETL"]
)

def Unified_log_pipline():
    # ==================================================
    # 0. CONFIG (Variable 로드)
    # ==================================================
    @task
    def load_config(dt: str) -> dict:
        env = Variable.get("env").strip()
        hive_tables = json.loads(Variable.get(f"{env}_hive_msck_table"))

        hive_tables.update({"env": env, "dt": dt})

        print(f"[DEBUG] ======= {hive_tables} =======")
        return hive_tables

    # ==================================================
    # 1. Hive 테이블 리스트
    # ==================================================
    @task
    def hive_table_list(config: dict) -> list[str]:
        tables_list = config["analytics_table"] + config["raw_table"]

        print(f"[DEBUG] ======= {tables_list} =======")
        return [] if not tables_list else tables_list

    # ==================================================
    # 2. MSCK GROUP
    # ==================================================
    def build_msck_command(table: str) -> str:
        return f"""
        bash -lc '
        echo "===== MSCK START: {table} ====="

        # HDFS 파티션 생성 (-3 ~ +3)
        for i in $(seq -3 3); do
            date=$(date -d "$i days" +%Y%m%d)
            hdfs dfs -mkdir -p /hive/{table}/dt=$date
        done

        # MSCK
        beeline -u jdbc:hive2://localhost:10000/default \
        -e "MSCK REPAIR TABLE {table}";

        # VERIFY
        beeline -u jdbc:hive2://localhost:10000/default \
        -e "SHOW PARTITIONS {table}";

        echo "===== MSCK END: {table} ====="
        '
        """

    # ==================================================
    # 3. INSERT GROUP
    # ==================================================
    @task
    def build_insert_cmds(tables: list[str], config: dict) -> list[str]:
        dt = config["dt"]
        cmds = []

        for table in tables:
            if table.startswith("raw_"):
                continue

            cols = config[f"{table}_schema"]

            query = f"""
            ADD JAR /application/apache-hive-3.1.3-bin/lib/hive-hcatalog-core-3.1.3.jar;
            SET hive.exec.dynamic.partition=true;
            SET hive.exec.dynamic.partition.mode=nonstrict;

            INSERT OVERWRITE TABLE {table} PARTITION (dt={dt})
            SELECT {cols}
            FROM raw_{table}
            WHERE dt={dt};
            """

            q = query.replace("\n", " ").strip()
            escaped_query = q.replace("`", "\\`")

            cmd = f"bash -lc 'beeline -u jdbc:hive2://localhost:10000/default -e \"{escaped_query}\"'"

            cmds.append(cmd)

        print(f"[INSERT CMDS] {cmds}")
        return cmds

    # ==================================================
    # 4. VALIDATION GROUP
    # ==================================================
    @task
    def build_validation_cmd(tables: list[str], config: dict) -> str:
        dt = config["dt"]
        target_tables = [t for t in tables if not t.startswith("raw_")]

        cmd = f"""
        bash -lc '
        PYTHONPATH=/work/jsy/Unified_Log_Analytics_Platform \
        spark-submit \
            --master {config["spark_option"]["master"]} \
            --deploy-mode {config["spark_option"]["deploy_mode"]} \
            --num-executors 2 \
            --executor-memory 2G \
            --executor-cores 1 \
            {config["spark_option"]["files"]["log_validation"]} \
            --tables "{",".join(target_tables)}" \
            --dt "{dt}"
        '
        """

        return cmd

    @task
    def check_validation(dt: str):
        from airflow.providers.postgres.hooks.postgres import PostgresHook

        pg = PostgresHook(postgres_conn_id="postgresql_default")
        rows = pg.get_records("""
            SELECT table_name, stage_count, raw_count, analysis_count
            FROM job.validation_row_count
            WHERE dt = %s
        """, parameters=(dt,))

        if not rows:
            raise Exception(f"[FAIL] validation 없음 → dt={dt}")

        failed = []
        for t, s, r, a in rows:
            if not (s == r == a):
                print(f"[MISMATCH] {t}: {s}, {r}, {a}")
                failed.append(t)

        if failed:
            raise Exception(f"[FAIL] {failed}")

        print(f"[SUCCESS] {dt} validation OK")


    # ==================================================
    # DAG FLOW
    # ==================================================
    config = load_config("{{ ds_nodash }}")
    tables = hive_table_list(config)

    # ---------------- MSCK ----------------
    with TaskGroup(group_id="msck_group") as msck_group:

        msck_tasks = SSHOperator.partial(
            task_id = "msck",
            ssh_conn_id = "ap_ssh",
            pool = "hive_msck_pool",
            retries = 0,
            cmd_timeout = None
        ).expand(command = tables.map(build_msck_command))

    # ---------------- INSERT ----------------
    with TaskGroup(group_id="insert_group") as insert_group:
        
        insert_cmds = build_insert_cmds(tables, config)
        insert_tasks = SSHOperator.partial(
            task_id = "insert",
            ssh_conn_id = "ap_ssh",
            pool = "hive_insert_pool",
            retries = 0,
            cmd_timeout = None,
        ).expand(command = insert_cmds)

    # ---------------- VALIDATION ----------------
    with TaskGroup(group_id="validation_group") as validation_group:

        validation_cmd = build_validation_cmd(tables, config)
        validation_exec = SSHOperator(
            task_id = "run_validation",
            ssh_conn_id = "ap_ssh",
            command = validation_cmd,
            retries = 0,
            cmd_timeout = None
        )

        validation_exec >> check_validation(config["dt"])

    # ---------------- DEPENDENCY ----------------
    msck_group >> insert_group >> validation_group

dag = Unified_log_pipline()

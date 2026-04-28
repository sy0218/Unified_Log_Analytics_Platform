from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="test_dag",
    start_date=datetime(2024, 1, 1),
    schedule=None,  # 수동 실행용
    catchup=False,
) as dag:

    task1 = BashOperator(
        task_id="print_hello",
        bash_command="echo 'Hello Airflow DAG!'"
    )

    task1

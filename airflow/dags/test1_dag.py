from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id="complex_taskflow_dag",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
)
def complex_dag():

    @task
    def extract():
        data = ["apple", "banana", "cherry"]
        print("extract:", data)
        return data

    @task
    def transform(data):
        transformed = [x.upper() for x in data]
        print("transform:", transformed)
        return transformed

    @task
    def validate(data):
        valid = [x for x in data if len(x) > 5]
        print("validate:", valid)
        return valid

    @task
    def load(data):
        print("load to warehouse:", data)
        return len(data)

    @task
    def notify(count):
        print(f"pipeline finished. loaded rows: {count}")

    raw = extract()
    transformed = transform(raw)
    validated = validate(transformed)
    count = load(validated)
    notify(count)

complex_dag()

# 📝 **Project Overview**
- **프로젝트 이름** : **통합 로그 분석 플랫폼**
- **설명**: 여러 운영 서버에 **분산되어 있는 로그 데이터를 실시간으로 수집하고 통합**하여,
로그 검색, 모니터링, 대용량 로그 분석 기능을 제공함으로써 시스템 운영 및 장애 대응을 효율적으로 지원하는 플랫폼입니다.

- **목표**
  1. 여러 운영 서버에서 발생하는 **로그 데이터를 안정적이고 빠르게 수집**
  2. **Filebeat, Kafka, Nifi 기반의** 실시간 로그 수집 및 스트리밍 파이프라인 구축
  3. **Elasticsearch를 활용한** 실시간 로그 검색 및 모니터링 환경 구성
  4. **Hadoop, Hive, Spark 기반의** 대용량 로그 데이터 저장 및 분석 환경 구축
---
<br><br>

# 🏗️ **플랫폼 아키텍처**
<p align="center">
  <img src="https://github.com/user-attachments/assets/9a66f927-486e-4503-831d-e165f5d61a2f" width="200%"/>
</p>

---
<br><br>

# 🛠️ **Trouble Shooting**
- ✅ **Ansible 자동화 도입! 다중 서버 환경 구성 & 환경 구축 시간 폭발적 단축!** → **[`📘 정리 문서`](./docs/trouble/ansible.md)**
---
<br><br>

# 🧰 **Project Operations Manual**
- 여기서는 **서비스 운영 및 관리를 위해 필요한 환경 구축과 설정 매뉴얼**을 제공합니다.
> 🚀 **Ansible로 자동화된 환경 설정 예시**는 🔗 [`Ansible 레포지토리`](https://github.com/sy0218/Ansible-Multi-Server-Setup)에서 확인하세요!

| **서비스** | **설명** | **매뉴얼** |
|------------|----------|------------|
| 🖲️ **KVM 기반 Ubuntu 서버 설치** | KVM 가상화 서버 설치 및 초기 설정 | **[`📘 매뉴얼`](./docs/manual/kvm_setup.md)** |
| ⏰ **클러스터 시간 & 클럭 동기화** | 클러스터 서버 시간과 클럭 초기 설정 | **[`📘 매뉴얼`](./docs/manual/sync_time_clock.md)** |
| 📷 **다중 서버 모니터링** | Prometheus · Grafana 기반 통합 모니터링 구성 | **[`📘 매뉴얼`](./docs/manual/prometheus_grafana_setup.md)** |
| 🐳 **Docker 환경 구축** | 컨테이너 개발/운영 환경 설정 | **[`📘 매뉴얼`](./docs/manual/docker_setup.md)** |
| 💾 **PostgreSQL DB** | 설치 및 초기 데이터베이스 설정 | **[`📘 매뉴얼`](./docs/manual/postgresql_setup.md)** |
| 🦓 **ZooKeeper** | 분산 환경 설정 관리 및 동기화 | **[`📘 매뉴얼`](./docs/manual/zookeeper_setup.md)** |
| 📡 **Kafka** | 데이터 스트리밍 플랫폼 구축/활용 | **[`📘 매뉴얼`](./docs/manual/kafka_setup.md)** |
| └─ 📦 **Schema Registry** | 카프카 직렬화 & 스키마 관리 | **[`📘 매뉴얼`](./docs/manual/kafka_schema_registry_setup.md)** |
| 🌀 **NiFi** | 데이터 플로우 관리 및 ETL | **[`📘 매뉴얼`](./docs/manual/hadoop_setup.md)** |
| 🐘 **Hadoop** | 분산 시스템 클러스터 설치/설정 | **[`📘 매뉴얼`](./docs/manual/hadoop_setup.md)** |
| ⚡ **Spark** | 분산 엔진 설치/설정 | **[`📘 매뉴얼`](./docs/manual/zookeeper_setup.md)** |
| 🐝 **Hive** | 데이터 웨어하우스 설치/운영 | **[`📘 매뉴얼`](./docs/manual/hive_manual.md)** |
| 🔍 **Elasticsearch** | 검색엔진 클러스터 설치/설정 | **[`📘 매뉴얼`](./docs/manual/elasticsearch_setup.md)** |




---
<br><br>

# 🏎️ **Real-time Data Pipeline**
여기서는 **Filebeat, Kafka, NiFi, Hadoop, Spark, Elasticsearch** 등을 활용해 구축한 **준실시간 데이터 파이프라인**의 **수집·처리·적재·검색** 전체 흐름을 단계별로 문서화했습니다.

| **카테고리** | **서비스** | **설명** |
|--------------|------------|----------|
| **수집** | 📡 `filebeat.service` | **시스템 로그 수집** → **[`📘 filebeat`](./docs/pipline/filebeat.md)** |

---
<br><br>

# 🛠️ Tech Stack

| Category | Stack |
|:--------:|:-----|
| 💻 **프로그래밍 언어** | ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=Python&logoColor=white) ![Shell Script](https://img.shields.io/badge/Shell%20Script-4EAA25?style=for-the-badge&logo=GNU%20Bash&logoColor=white)  |
| ☁️ **인프라 & 가상화** | ![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=Linux&logoColor=black) ![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=Docker&logoColor=white) ![KVM](https://img.shields.io/badge/KVM-FF6600?style=for-the-badge&logo=Linux&logoColor=white) |
| 🗄 **빅데이터 & 저장소** | ![Hadoop](https://img.shields.io/badge/Apache%20Hadoop-66CCFF?style=for-the-badge&logo=Apache%20Hadoop&logoColor=black) ![Elasticsearch](https://img.shields.io/badge/Elasticsearch-005571?style=for-the-badge&logo=Elasticsearch&logoColor=white) |
| 💾 **데이터 웨어하우스 & 마트** |  ![Hive](https://img.shields.io/badge/Hive-FDEE21?style=for-the-badge&logo=Apache%20Hive&logoColor=black) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=PostgreSQL&logoColor=white) |
| 🖧 **분산 엔진** | ![Spark](https://img.shields.io/badge/Apache%20Spark-E25A1C?style=for-the-badge&logo=Apache%20Spark&logoColor=white) |
| ⚡ **메시징** | ![Kafka](https://img.shields.io/badge/Apache%20Kafka-231F20?style=for-the-badge&logo=Apache%20Kafka&logoColor=white) |
| 🔄 **워크플로우** | ![NiFi](https://img.shields.io/badge/Apache%20NiFi-FF6600?style=for-the-badge&logo=Apache%20NiFi&logoColor=white) ![Airflow](https://img.shields.io/badge/Apache%20Airflow-017CEE?style=for-the-badge&logo=Apache%20Airflow&logoColor=white) |
| 📊 **모니터링 & 시각화** | ![Prometheus](https://img.shields.io/badge/Prometheus-263238?style=for-the-badge&logo=Prometheus&logoColor=white) ![Grafana](https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=Grafana&logoColor=white) ![Kibana](https://img.shields.io/badge/Kibana-005571?style=for-the-badge&logo=Kibana&logoColor=white) |

---

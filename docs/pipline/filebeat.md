# 📡 로그 수집 아키텍처 **(Filebeat 기반)**

## 🧾 수집 로그 종류

| 로그 | 설명 |
|------|------|
| **syslog** | 통합 시스템 로그 (커널, 서비스, 네트워크 등 전체 활동 기록) |
| **auth.log** | 인증 로그 (로그인, sudo, SSH 접속, 계정 관련 보안 이벤트) |
| **kern.log** | 커널 로그 (하드웨어 에러, 드라이버 문제, OOM 등) |
| **dmesg** | 부팅 로그 (하드웨어 초기화 및 드라이버 로딩 과정) |
| **dpkg.log** | 패키지 관리 로그 (설치/삭제/업데이트 이력 → 변경 추적) |

---
<br>

## 🔄 로그 수집 파이프라인
![Pipline](https://github.com/user-attachments/assets/04997001-1414-4e2c-8d59-f4ea4f23336f)

---
<br>

## 🧵 Kafka 토픽 구성
```bash
__consumer_offsets
system_auth_log
system_dmesg_log
system_dpkg_log
system_kern_log
system_syslog_log
```
---
### ⚙️ 토픽 설정
- 파티션: 3 → 병렬 처리
- 레플리카: 3 → 가용성 확보 (브로커 3대 구성)
- 리텐션: 3 → 재처리 목적 데이터 보존
→ **추후 디스크 사용량 기반 조정 예정**

---
<br>

## 🚀 Filebeat (경량 로그 수집기)
### ✅ 장점
- **서버 부담 최소화 (Logstash 대비 매우 가벼움)**
- 다양한 Output 지원 (Kafka, Logstash, Elasticsearch)
- ACK 기반 재전송 → 안정성 확보
---
### ❌ 단점
- 로그 가공 기능 제한적 (전처리 기능 부족)
---
### 🎯 선택 이유
- 로그 수집 자유도 확보
- 전처리는 Kafka Consumer에서 수행 (분석 목적에 맞게 표준화)
- **경량 수집기 + 유연한 구조 선택**
---
### 🏗️ Filebeat 설정 구조
```bash
filebeat.yml (main)
 └── inputs/*.yml (각 로그별 설정)
```
- 로그별 설정 파일 분리 → 관리 용이
- 동적 reload 지원 → 유연한 확장
---
### ⚙️ filebeat.yml (메인 설정)
```yaml
filebeat.config.inputs:
  enabled: true
  path: '/etc/filebeat/inputs/*.yml'
  reload.enabled: true

output.kafka:
  hosts: ["192.168.122.60:9092", "192.168.122.61:9092", "192.168.122.62:9092"]
  topic: '%{[kafka_topic]}'
  required_acks: 1
  codec.format:
     string: '%{[@timestamp]} %{[host.name]} %{[message]}'

logging.level: info
logging.to_files: true
logging.files:
  path: /var/log/filebeat
  name: filebeat.log
  keepfiles: 3
  permissions: 0644
logging.to_syslog: false
logging.to_journal: false
```
#### 📌 출력 포맷
- timestamp + host.name + message
- 분산 환경 고려 ( 호스트 식별 )
#### 📌 로그 관리 전략
- syslog 미사용 → **자기 로그 파일 직접 관리**
---
### 📥 로그별 Input 설정
```yaml
## syslog ##
- type: filestream
  id: syslog_input
  enabled: true
  paths:
    - /var/log/syslog
  fields:
    kafka_topic: "system_syslog_log"
  fields_under_root: true
  processors:
    - add_host_metadata: ~
    - include_fields:
        fields: ["host.name", "message", "kafka_topic"]

-----------------------------------------------------------------
## auth.log ##
- type: filestream
  id: auth_input
  enabled: true
  paths:
    - /var/log/auth.log
  fields:
    kafka_topic: "system_auth_log"
  fields_under_root: true
  processors:
    - add_host_metadata: ~
    - include_fields:
        fields: ["host.name", "message", "kafka_topic"]

-----------------------------------------------------------------
## dmesg ##
- type: filestream
  id: dmesg_input
  enabled: true
  paths:
    - /var/log/dmesg
  fields:
    kafka_topic: "system_dmesg_log"
  fields_under_root: true
  processors:
    - add_host_metadata: ~
    - include_fields:
        fields: ["host.name", "message", "kafka_topic"]

-----------------------------------------------------------------
## dpkg.log ##
- type: filestream
  id: dpkg_input
  enabled: true
  paths:
    - /var/log/dpkg.log
  fields:
    kafka_topic: "system_dpkg_log"
  fields_under_root: true
  processors:
    - add_host_metadata: ~
    - include_fields:
        fields: ["host.name", "message", "kafka_topic"]

-----------------------------------------------------------------
## kern.log ##
- type: filestream
  id: kern_input
  enabled: true
  paths:
    - /var/log/kern.log
  fields:
    kafka_topic: "system_kern_log"
  fields_under_root: true
  processors:
    - add_host_metadata: ~
    - include_fields:
        fields: ["host.name", "message", "kafka_topic"]
```
- **`id` → offset 관리 (중요)**
- `kafka_topic` → 동적 토픽 분기
- 필드 수집 필터링 (`host.name`, `message`)

---
<br>

## 🧪 실행 및 검증
### ✔️ 설정 검증 ( 문법 오류 확인 )
```bash
filebeat test config
```
---
### ▶️ 실행
```bash
systemctl start filebeat.service
```

---
<br>

## 📊 Kafka Consumer 로그 확인 (예시)
### 🔐 auth 로그
```bash
2026-03-26T02:57:25.202Z ap ... session opened for user root
2026-03-26T02:57:25.202Z ap ... session closed for user root
```
---
### 💾 dmesg 로그
```bash
kernel: Command line: BOOT_IMAGE=...
kernel: KERNEL supported cpus:
```
---
### 📦 dpkg 로그
```bash
status installed base-passwd:amd64
status unpacked base-files:amd64
```
---
### 🧠 kern 로그
```bash
kernel: device entered promiscuous mode
kernel: port entered disabled state
```
---
### 🖥️ syslog 로그
```bash
CRON CMD (/script/service_status.sh)
systemd: Started Filebeat
```

---
<br>

## 📈 운영 고도화 계획
### 🔥 Grafana 연동
- Filebeat 에러 로그 모니터링
- **사일런트 페일러 방지 핵심**
---
### 📦 Loki 도입
- 목적: 빠른 에러 확인
- 장점
    - 그라파나 연동 용이
     - 단순 로그 확인시 → 인덱스 크기가 매우 작아 메모와 저장 공간 아낄 수 있음
> #### 모든 텍스트를 검색할 필요없고, 특정 서비스의 로그 상태를( ERROR, WARN.. ) 가볍고 빠르게 시작화 가능
---
<br>

## 🧪 통합 테스트 계획 (추후)
1) Kafka Down 시 → 로그 디스크 저장 정상 여부 확인
2) Kafka 복구 시 → 재전송/재처리 정상 동작 확인
---

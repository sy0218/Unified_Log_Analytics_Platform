# NiFi 로그 수집 파이프라인 정리

> Kafka(filebeat)에서 수집한 로그를 Grok으로 파싱한 뒤 NDJSON 형태로 변환하고 MergeContent로 묶어서 HDFS `/staging/logs` 경로에 저장합니다.

---

## 1. 전체 구성 요약

### 1.1 플로우 개요

```text
Kafka Topics
  ├─ system_kern_log
  ├─ system_auth_log
  ├─ system_dpkg_log
  └─ system_syslog_log

        ↓
ConsumeKafkaRecord_2_6
        ↓ success / parse.failure
MergeContent
        ↓ merged / failure
UpdateAttribute
        ↓ success
PutHDFS
        ↓
HDFS: /staging/logs
```

Grok Parsing 형태에 따른`ConsumeKafkaRecord_2_6` 프로세서가 2개 존재하며, 두 입력이 `MergeContent`로 합쳐진 뒤 `UpdateAttribute`를 거쳐 `PutHDFS`로 전달됩니다.

### 1.2 주요 Processor

| 순서 | Processor | 버전 | 역할 |
|---:|---|---|---|
| 1 | `ConsumeKafkaRecord_2_6` | `1.23.0` | Kafka Topic에서 로그 데이터 Consume |
| 2 | `MergeContent` | `1.23.0` | 여러 로그 file을 하나로 병합 |
| 3 | `UpdateAttribute` | `1.23.0` | 날짜시간 attribute 추가하여 HDFS 저장 파일명 생성 |
| 4 | `PutHDFS` | `1.23.0` | 병합된 NDJSON 파일을 HDFS에 저장 |

---

## 2. Kafka 수집 설정

### 2.1 Kafka Brokers

```text
192.168.122.60:9092,192.168.122.61:9092,192.168.122.62:9092
```

### 2.2 Topic 목록

```text
system_kern_log
system_auth_log
system_dpkg_log
system_syslog_log
```

---

## 3. ConsumeKafkaRecord_2_6

### 3.1 역할

`ConsumeKafkaRecord_2_6`는 Kafka에서 메시지를 가져온 뒤 Record Reader를 통해 로그를 구조화하고 ndjson 형태 output

1. 일반 syslog 계열 로그용
2. DPKG 로그용

---

### 3.2.1 INPUT: GrokReader

| 항목 | 값 |
|---|---|
| Controller Service | `GrokReader 1.23.0` |
| Schema Access Strategy | `Use String Fields From Grok Expression` |
| Grok Patterns | %{TIMESTAMP_ISO8601:outer_ts}\s+%{HOSTNAME:hostname}\s+%{DATA:log_type}\s+<%{POSINT:priority}>%{NONNEGINT:version}\s+%{TIMESTAMP_ISO8601:timestamp}\s+%{HOSTNAME:hostname1}\s+%{DATA:program}\s+%{DATA:pid}\s+%{DATA:msgid}\s+(%{DATA:structured_data})\s+%{GREEDYDATA:message} |
| No Match Behavior | `Append to Previous Message` |


### 3.2.2 파싱 필드

| 필드 | 타입 | 설명 |
|---|---|---|
| `outer_ts` | string | timestamp |
| `hostname` | string | 서버 hostname |
| `log_type` | string | 로그 타입 |
| `priority` | int | priority |
| `pid` | string | process id |
| `msgid` | string | message id |
| `structured_data` | string | structured data |
| `message` | string | 실제 로그 메시지 본문 |

### 3.2.3 OUTPUT: JsonRecordSetWriter

| 항목 | 값 |
|---|---|
| Controller Service | `JsonRecordSetWriter 1.23.0` |
| Schema Write Strategy | `Do Not Write Schema` |
| Schema Access Strategy | `Use 'Schema Text' Property` |
| Pretty Print JSON | `false` |
| Suppress Null Values | `Never Suppress` |
| Output Grouping | `One Line Per Object` |
| Compression Format | `none` |

### 3.2.4 Syslog Schema Text

```json
{
  "type": "record",
  "name": "sysloglogRecord",
  "fields": [
    { "name": "log_type", "type": "string" },
    { "name": "priority", "type": "int" },
    { "name": "version", "type": "int" },
    { "name": "timestamp", "type": "string" },
    { "name": "hostname", "type": "string" },
    { "name": "program", "type": "string" },
    { "name": "pid", "type": "string" },
    { "name": "msgid", "type": "string" },
    { "name": "structured_data", "type": "string" },
    { "name": "message", "type": "string" }
  ]
}
```

### 3.3.1 DPKG_GrokReader

| 항목 | 값 |
|---|---|
| Controller Service | `DPKG_GrokReader` |
| Schema Access Strategy | `Use String Fields From Grok Expression` |
| Grok Patterns | %{TIMESTAMP_ISO8601:outer_ts}\s+%{HOSTNAME:hostname}\s+%{WORD:log_type}\s+%{TIMESTAMP_ISO8601:timestamp}\s+%{WORD:action}\s+%{DATA:category}\s+%{GREEDYDATA:message} |
| No Match Behavior | `Append to Previous Message` |

### 3.3.2 파싱 필드

| 필드 | 타입 | 설명 |
|---|---|---|
| `outer_ts` | string | 외부 로그 prefix timestamp로 추정 |
| `hostname` | string | hostname |
| `log_type` | string | 로그 타입 |
| `timestamp` | string | DPKG 로그 timestamp |
| `category` | string | 패키지/카테고리 구분값 |
| `message` | string | 상세 로그 메시지 |

### 3.3.3 DPKG_JsonRecordSetWriter

| 항목 | 값 |
|---|---|
| Controller Service | `DPKG_JsonRecordSetWriter` |
| Schema Write Strategy | `Do Not Write Schema` |
| Schema Access Strategy | `Use 'Schema Text' Property` |
| Pretty Print JSON | `false` |
| Suppress Null Values | `Never Suppress` |
| Output Grouping | `One Line Per Object` |
| Compression Format | `none` |

### 3.3.4 DPKG Schema Text

```json
{
  "type": "record",
  "name": "dpkglogRecord",
  "fields": [
    { "name": "log_type", "type": "string" },
    { "name": "timestamp", "type": "string" },
    { "name": "hostname", "type": "string" },
    { "name": "action", "type": "string" },
    { "name": "category", "type": "string" },
    { "name": "message", "type": "string" }
  ]
}
```

---

## 4. MergeContent 설정

### 4.1 역할

`MergeContent`는 Kafka에서 들어온 여러 FlowFile을 하나의 파일로 통합하여 이후 `UpdateAttribute`에서 파일명을 부여하고 `PutHDFS`로 전달합니다.

### 4.2 주요 Properties

| Property | Value |
|---|---|
| Merge Strategy | `Bin-Packing Algorithm` |
| Merge Format | `Binary Concatenation` |
| Attribute Strategy | `Keep All Unique Attributes` |
| Correlation Attribute Name | 설정 없음 |
| Minimum Number of Entries | `1000` |
| Maximum Number of Entries | `1000` |
| Minimum Group Size | `0 B` |
| Maximum Group Size | 설정 없음 |
| Max Bin Age | `300 sec` |
| Maximum number of Bins | `1` |
| Delimiter Strategy | `Do Not Use Delimiters` |

### 4.3 Relationships

| Relationship | 처리 방식 | 설명 |
|---|---|---|
| `merged` | 다음 단계로 전달 | 병합된 FlowFile |
| `failure` | 다음 단계로 전달된 것으로 보임 | 병합 실패 건 |
| `original` | `terminate` | 병합에 사용된 원본 FlowFile 제거 |

### 4.4 동작 해석

현재 설정은 아래 둘 중 먼저 만족되는 조건으로 병합 파일을 생성합니다.

- FlowFile이 `1000`개 쌓임
- `Max Bin Age = 300 sec`
---

## 5. UpdateAttribute 설정

### 5.1 역할

`UpdateAttribute`는 Attribute를 추가하여 HDFS에 저장될 파일명을 동적으로 생성합니다.

### 5.2 filename 속성

```text
filename = ${now():format("yyyyMMddHHmmssSSSSS")}.ndjson
```

### 5.3 파일명 예시

```text
2026052415304512345.ndjson
```

---

## 6. PutHDFS 설정

### 6.1 역할

`PutHDFS`는 최종 FlowFile을 HDFS 경로에 저장합니다.

### 6.2 Hadoop Configuration Resources

```text
/application/hadoop/etc/hadoop/core-site.xml,
/application/hadoop/etc/hadoop/hdfs-site.xml
```

### 6.3 Directory

```text
/staging/logs
```

---

## 7. 최종 산출물 형태

### 7.1 저장 위치

```text
HDFS Path: /staging/logs
```

### 7.2 파일 확장자

```text
.ndjson
```

### 7.3 예상 레코드 포맷

Syslog 예시:

```json
{"log_type":"system_syslog_log","priority":13,"version":1,"timestamp":"2026-05-24T15:30:45Z","hostname":"host01","program":"sshd","pid":"1234","msgid":"-","structured_data":"-","message":"Accepted password for user"}
```

DPKG 예시:

```json
{"log_type":"dpkg","timestamp":"2026-05-24T15:30:45Z","hostname":"host01","action":"install","category":"package-name","message":"installed package-name"}
```

# NiFi 로그 수집 파이프라인 정리

> Notion Export 원문을 기준으로 Apache NiFi 플로우 구성을 Markdown 형태로 정리한 문서입니다.  
> 목적: Kafka에서 수집한 Linux/System 로그를 Grok으로 파싱한 뒤 JSON/NDJSON 형태로 변환하고, MergeContent로 묶어서 HDFS `/staging/logs` 경로에 저장합니다.

---

## 1. 전체 구성 요약

### 1.1 플로우 개요

```text
Kafka Topics
  ├─ system_kern_log
  ├─ system_auth_log
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

원본 플로우 이미지 기준으로 `ConsumeKafkaRecord_2_6` 프로세서가 2개 존재하며, 두 입력이 `MergeContent`로 합쳐진 뒤 `UpdateAttribute`를 거쳐 `PutHDFS`로 전달됩니다.

### 1.2 주요 Processor

| 순서 | Processor | 버전 | 역할 |
|---:|---|---|---|
| 1 | `ConsumeKafkaRecord_2_6` | `1.23.0` | Kafka Topic에서 로그 데이터 Consume |
| 2 | `MergeContent` | `1.23.0` | 여러 FlowFile을 하나로 병합 |
| 3 | `UpdateAttribute` | `1.23.0` | HDFS 저장 파일명 생성 |
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
system_syslog_log
```

---

## 3. ConsumeKafkaRecord_2_6

### 3.1 역할

`ConsumeKafkaRecord_2_6`는 Kafka에서 메시지를 가져온 뒤 Record Reader를 통해 로그를 구조화합니다. 원문에는 다음 두 종류의 Record Reader/Writer 설정이 정리되어 있습니다.

1. 일반 syslog 계열 로그용
2. DPKG 로그용

---

## 4. Syslog 파싱 설정

### 4.1 GrokReader

| 항목 | 값 |
|---|---|
| Controller Service | `GrokReader 1.23.0` |
| Schema Access Strategy | `Use String Fields From Grok Expression` |
| Grok Patterns | 설정 없음 |
| No Match Behavior | `Append to Previous Message` |

### 4.2 Grok Expression

```grok
%{TIMESTAMP_ISO8601:outer_ts}\s+%{HOSTNAME:hostname}\s+%{DATA:log_type}\s+<%{POSINT:priority}>%{NONNEGINT:version}\s+%{TIMESTAMP_ISO8601:timestamp}\s+%{HOSTNAME:hostname1}\s+%{DATA:program}\s+%{DATA:pid}\s+%{DATA:msgid}\s+(%{DATA:structured_data})\s+%{GREEDYDATA:message}
```

### 4.3 파싱 필드

| 필드 | 타입 | 설명 |
|---|---|---|
| `outer_ts` | string | Kafka 또는 외부 로그 prefix timestamp로 추정 |
| `hostname` | string | 외부 prefix의 hostname |
| `log_type` | string | 로그 타입 |
| `priority` | int | syslog priority |
| `version` | int | syslog version |
| `timestamp` | string | syslog 내부 timestamp |
| `hostname1` | string | syslog 내부 hostname |
| `program` | string | 로그 발생 프로그램 |
| `pid` | string | process id |
| `msgid` | string | message id |
| `structured_data` | string | syslog structured data |
| `message` | string | 실제 로그 메시지 본문 |

> 주의: Grok에서는 `hostname1`을 추출하지만, Writer Schema에는 `hostname`만 있습니다. 실제 출력 JSON에 어떤 hostname을 사용할지 확인이 필요합니다.

### 4.4 JsonRecordSetWriter

| 항목 | 값 |
|---|---|
| Controller Service | `JsonRecordSetWriter 1.23.0` |
| Schema Write Strategy | `Do Not Write Schema` |
| Schema Access Strategy | `Use 'Schema Text' Property` |
| Pretty Print JSON | `false` |
| Suppress Null Values | `Never Suppress` |
| Output Grouping | `One Line Per Object` |
| Compression Format | `none` |

### 4.5 Syslog Schema Text

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

---

## 5. DPKG 로그 파싱 설정

### 5.1 DPKG_GrokReader

| 항목 | 값 |
|---|---|
| Controller Service | `DPKG_GrokReader` |
| Schema Access Strategy | `Use String Fields From Grok Expression` |
| Grok Patterns | 설정 없음 |
| No Match Behavior | `Append to Previous Message` |

### 5.2 Grok Expression

```grok
%{TIMESTAMP_ISO8601:outer_ts}\s+%{HOSTNAME:hostname}\s+%{WORD:log_type}\s+%{TIMESTAMP_ISO8601:timestamp}\s+%{WORD:action}\s+%{DATA:category}\s+%{GREEDYDATA:message}
```

### 5.3 파싱 필드

| 필드 | 타입 | 설명 |
|---|---|---|
| `outer_ts` | string | 외부 로그 prefix timestamp로 추정 |
| `hostname` | string | hostname |
| `log_type` | string | 로그 타입 |
| `timestamp` | string | DPKG 로그 timestamp |
| `action` | string | install, upgrade, remove 등 DPKG 액션 |
| `category` | string | 패키지/카테고리 구분값 |
| `message` | string | 상세 로그 메시지 |

### 5.4 DPKG_JsonRecordSetWriter

| 항목 | 값 |
|---|---|
| Controller Service | `DPKG_JsonRecordSetWriter` |
| Schema Write Strategy | `Do Not Write Schema` |
| Schema Access Strategy | `Use 'Schema Text' Property` |
| Pretty Print JSON | `false` |
| Suppress Null Values | `Never Suppress` |
| Output Grouping | `One Line Per Object` |
| Compression Format | `none` |

### 5.5 DPKG Schema Text

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

## 6. MergeContent 설정

### 6.1 역할

`MergeContent`는 Kafka에서 들어온 여러 FlowFile을 하나의 파일로 묶습니다. 이후 `UpdateAttribute`에서 파일명을 부여하고 `PutHDFS`로 전달합니다.

### 6.2 주요 Properties

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

### 6.3 Relationships

| Relationship | 처리 방식 | 설명 |
|---|---|---|
| `merged` | 다음 단계로 전달 | 병합된 FlowFile |
| `failure` | 다음 단계로 전달된 것으로 보임 | 병합 실패 건 |
| `original` | `terminate` | 병합에 사용된 원본 FlowFile 제거 |

### 6.4 동작 해석

현재 설정은 아래 둘 중 먼저 만족되는 조건으로 병합 파일을 생성합니다.

- FlowFile이 `1000`개 쌓임
- `Max Bin Age = 300 sec` 도달

`Merge Format`이 `Binary Concatenation`이고 `Delimiter Strategy`가 `Do Not Use Delimiters`이므로, 개별 FlowFile 끝에 개행 문자가 없으면 NDJSON 형식이 깨질 수 있습니다. `JsonRecordSetWriter`가 `One Line Per Object`로 설정되어 있어도 실제 각 FlowFile 끝에 newline이 포함되는지는 샘플 파일로 확인하는 것이 안전합니다.

---

## 7. UpdateAttribute 설정

### 7.1 역할

`UpdateAttribute`는 HDFS에 저장될 파일명을 동적으로 생성합니다.

### 7.2 filename 속성

```text
filename = ${now():format("yyyyMMddHHmmssSSSSS")}.ndjson
```

### 7.3 파일명 예시

```text
2026052415304512345.ndjson
```

### 7.4 검토 사항

동일 시각에 여러 FlowFile이 동시에 처리될 경우 파일명 충돌 가능성을 검토해야 합니다. 충돌 방지를 더 강화하려면 UUID를 추가하는 방식도 사용할 수 있습니다.

```text
filename = ${now():format("yyyyMMddHHmmssSSSSS")}_${UUID()}.ndjson
```

---

## 8. PutHDFS 설정

### 8.1 역할

`PutHDFS`는 최종 FlowFile을 HDFS 경로에 저장합니다.

### 8.2 Hadoop Configuration Resources

```text
/application/hadoop/etc/hadoop/core-site.xml,
/application/hadoop/etc/hadoop/hdfs-site.xml
```

### 8.3 Directory

```text
/staging/logs
```

---

## 9. 최종 산출물 형태

### 9.1 저장 위치

```text
HDFS Path: /staging/logs
```

### 9.2 파일 확장자

```text
.ndjson
```

### 9.3 예상 레코드 포맷

Syslog 예시:

```json
{"log_type":"system_syslog_log","priority":13,"version":1,"timestamp":"2026-05-24T15:30:45Z","hostname":"host01","program":"sshd","pid":"1234","msgid":"-","structured_data":"-","message":"Accepted password for user"}
```

DPKG 예시:

```json
{"log_type":"dpkg","timestamp":"2026-05-24T15:30:45Z","hostname":"host01","action":"install","category":"package-name","message":"installed package-name"}
```

---

## 10. 운영 체크포인트

### 10.1 Kafka

- Broker 3대 모두 연결 가능한지 확인
- Topic 이름 오타 확인
- Consumer Group 설정 확인
- Offset reset 정책 확인
- Kafka 메시지 원문 포맷이 Grok Expression과 일치하는지 확인

### 10.2 GrokReader

- `parse.failure` 건수가 증가하는지 모니터링
- `No Match Behavior = Append to Previous Message`가 의도한 설정인지 검토
- multiline 로그를 처리해야 하는 경우 현재 설정이 적합한지 확인
- Syslog Grok 필드 `hostname1`과 Writer Schema `hostname` 매핑 차이 확인

### 10.3 JsonRecordSetWriter

- Output Grouping이 `One Line Per Object`인지 확인
- Schema Text와 Grok 추출 필드가 정확히 일치하는지 확인
- int 필드인 `priority`, `version`에 문자열/빈값이 들어오는 경우 실패 가능성 확인

### 10.4 MergeContent

- `Minimum Number of Entries = 1000`
- `Maximum Number of Entries = 1000`
- `Max Bin Age = 300 sec`
- 처리량이 낮을 경우 최대 5분 지연 발생 가능
- delimiter 미사용으로 NDJSON 경계가 깨지지 않는지 확인

### 10.5 HDFS

- NiFi 실행 계정의 HDFS write 권한 확인
- `/staging/logs` 디렉터리 존재 여부 확인
- NameNode HA 또는 Kerberos 사용 여부 확인
- `core-site.xml`, `hdfs-site.xml` 경로와 권한 확인

---

## 11. 장애 대응 기준

| 증상 | 가능 원인 | 확인 위치 |
|---|---|---|
| Kafka에서 데이터가 안 들어옴 | Broker/Topic/Consumer Group 문제 | `ConsumeKafkaRecord_2_6` bulletin, Kafka topic offset |
| `parse.failure` 증가 | Grok Expression과 로그 포맷 불일치 | GrokReader, 실패 FlowFile content |
| JSON 변환 실패 | Schema 필드/타입 불일치 | JsonRecordSetWriter bulletin |
| MergeContent에 Queue 적체 | 1000개 미만 유입 또는 HDFS 지연 | MergeContent queue, Max Bin Age |
| HDFS 저장 실패 | 권한, 경로, Hadoop conf 문제 | PutHDFS bulletin, NiFi app log |
| NDJSON 파일 깨짐 | MergeContent delimiter 미사용 | HDFS 저장 파일 샘플 확인 |

---

## 12. 개선 권장사항

### 12.1 실패 라우팅 분리

현재 플로우 이미지에서는 `parse.failure`도 `MergeContent`로 연결된 것으로 보입니다. 실패 데이터를 정상 데이터와 같이 병합하면 품질 관리가 어려울 수 있습니다.

권장 라우팅:

```text
success       → MergeContent → HDFS normal path
parse.failure → PutFile/PutHDFS failure path 또는 Dead Letter Queue
```

예시 실패 경로:

```text
/staging/logs/_failed
```

### 12.2 파일명 충돌 방지

현재:

```text
${now():format("yyyyMMddHHmmssSSSSS")}.ndjson
```

권장:

```text
${now():format("yyyyMMddHHmmssSSSSS")}_${UUID()}.ndjson
```

### 12.3 HDFS 디렉터리 파티셔닝

운영/분석 편의를 위해 날짜 기준 파티셔닝을 권장합니다.

```text
/staging/logs/yyyy=${now():format("yyyy")}/MM=${now():format("MM")}/dd=${now():format("dd")}
```

또는 로그 타입 기준 분리:

```text
/staging/logs/log_type=${log_type}/yyyy=${now():format("yyyy")}/MM=${now():format("MM")}/dd=${now():format("dd")}
```

### 12.4 MergeContent 구분자 검토

NDJSON 파일은 레코드 단위 개행이 중요합니다. 실제 산출물이 아래처럼 한 줄에 하나의 JSON 객체로 저장되는지 확인해야 합니다.

```jsonl
{"log_type":"system_syslog_log","message":"..."}
{"log_type":"system_auth_log","message":"..."}
{"log_type":"dpkg","message":"..."}
```

개행이 누락되면 다음처럼 깨질 수 있습니다.

```jsonl
{"log_type":"a"}{"log_type":"b"}
```

---

## 13. 최종 정리

이 NiFi 플로우는 Kafka 기반 로그 수집 데이터를 다음 흐름으로 처리합니다.

1. Kafka Topic에서 시스템 로그 수집
2. GrokReader로 로그 라인 파싱
3. JsonRecordSetWriter로 JSON/NDJSON 변환
4. MergeContent로 1000건 단위 또는 300초 단위 병합
5. UpdateAttribute로 timestamp 기반 파일명 생성
6. PutHDFS로 `/staging/logs`에 저장

운영 시 가장 먼저 확인해야 할 부분은 `parse.failure` 라우팅, Grok 필드와 Schema 필드의 불일치, MergeContent delimiter, HDFS write 권한입니다.

---

## 부록 A. 원본 스크린샷 파일

이미지 포함 번들에는 아래 원본 캡처를 정리된 이름으로 포함했습니다.

| 파일 | 내용 |
|---|---|
| `assets/flow_overview.png` | 전체 NiFi 플로우 구성 |
| `assets/grokreader_syslog_properties.png` | Syslog GrokReader 설정 |
| `assets/json_writer_syslog_properties.png` | Syslog JsonRecordSetWriter 설정 |
| `assets/grokreader_dpkg_properties.png` | DPKG GrokReader 설정 |
| `assets/json_writer_dpkg_properties.png` | DPKG JsonRecordSetWriter 설정 |
| `assets/mergecontent_properties.png` | MergeContent Properties |
| `assets/mergecontent_relationships.png` | MergeContent Relationships |

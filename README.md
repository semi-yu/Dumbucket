## 개요

### 덤버킷이란 무엇인가?

Dumbucket(이하 ‘덤버킷’)은 **Gopher 프로토콜을 활용한 SSRF(Server-Side Request Forgery) 취약점을 학습·재현하기 위해 의도적으로 설계된 파일 저장·프록시 서버**입니다.

해당 소프트웨어는 경기대학교 2025학년도 2학기 ‘웹 보안’ 과목의 학기 프로젝트를 수행하기 위해 제작되었습니다. 백엔드는 Python의 Flask 프레임워크를 사용하였으며, 그 외 의존성은 `pyproject.toml`을 참고하십시오.

### 주의사항

- 이 프로젝트는 **교육·연구 목적**으로만 사용해야 합니다.
- 덤버킷은 의도적으로 취약한 구성이 포함되어 있으므로, **인터넷에 직접 노출하거나 실서비스 환경에서 사용해서는 안 됩니다.**

---

## 상세

### 아키텍처 및 위협 모델 개요

- **덤버킷**
    - Flask 애플리케이션 + pycurl
    - 내부에서 시스템에 설치된 cURL 바이너리를 호출하여 외부/내부 자원에 요청을 보냅니다.
- **배치 가정**
    - 덤버킷 컨테이너는 내부 인프라(MySQL, Redis, 내부 HTTP 서비스 등)와 동일한 Docker 네트워크 상에 존재합니다.
    - 외부 사용자는 덤버킷의 HTTP 포트(기본 5000)에만 접근 가능합니다.
- **위협 모델(요약)**
    1. 공격자는 `/fetch` 엔드포인트에 임의의 URL을 전달합니다.
    2. 덤버킷은 해당 URL에 대해 **호스트·프로토콜·포트에 대한 필터링 없이** 서버 측에서 cURL 요청을 수행합니다.
    3. 공격자는 gopher:// 스킴 등을 사용하여 내부망에만 노출된 서비스(예: 내부 DB)에 임의의 프로토콜 데이터를 전송하고, 그 결과로 쿼리 실행이나 민감 정보 접근을 유도할 수 있습니다.

---

### 어떻게 구현되었는가?

1. **기반 이미지 및 cURL 버전**
    - `Dockerfile` 에서 확인할 수 있듯이, 덤버킷은 Debian 9.13 기반 컨테이너에서 구동됩니다. 이 버전에는 **cURL 7.52.1**이 포함되어 있습니다.
    - cURL 7.71.1 이후 버전에서는 URL 내에 포함된 NUL 바이트(`\x00`)를 거부하도록 변경되었습니다. 이 프로젝트에서 사용하는 gopher 기반 SSRF payload는 URL 중간에 `%00`(NUL 바이트 인코딩)을 포함하므로, 이를 재현하기 위해 NUL 바이트가 허용되는 **구버전 cURL(7.52.1)** 환경을 사용합니다. [도보시오-01]
2. **요청 처리 흐름**
    1. Flask 애플리케이션은 pycurl을 사용하여 cURL 라이브러리를 직접 호출합니다.
        - 이는 cURL의 다양한 옵션과 여러 프로토콜 지원을 사용하기 위한 설계 선택입니다.
    2. 덤버킷은 `/fetch` 요청 시 전달받은 URL에 대해 **허용 목록 검증(allow-list), 내부망 차단, 스킴/포트 필터링 등의 보안 검증을 수행하지 않습니다.**
        - 이로 인해 외부 사용자가 지정한 임의의 URI에 대해 서버 측에서 요청을 보내는 **SSRF 취약점**이 발생합니다.
    3. 공격자는 gopher:// 스킴을 사용해 MySQL 등 내부 서비스의 포트로 **임의의 프로토콜 바이트열**을 전송할 수 있으며, 그 결과로 쿼리 실행이나 데이터 유출 등 내부 자원에 대한 비인가 접근을 유도할 수 있습니다. [도보시오-02]
3. **Gopher 기반 SSRF 예시(개념적인 설명)**
    - 예를 들어, 내부망에만 노출된 `mysql:3306` 서비스가 존재한다고 가정합니다.
    - 공격자는 `/fetch` 엔드포인트에 `gopher://mysql:3306/_<raw-mysql-payload>`
    형태의 URL을 전달할 수 있습니다.
    - 덤버킷은 이 URL을 그대로 cURL에 넘기고, cURL은 내부 MySQL 서비스로 raw payload를 보내 쿼리를 실행하게 됩니다.
    - 이 README에서는 실제 payload 전체를 나열하지는 않지만, 위와 같은 구조를 통해 **외부에서 내부 데이터베이스 쿼리를 우회 실행하는 SSRF 시나리오**를 재현할 수 있습니다.

---

### API 엔드포인트

| 경로 | 메서드 | 파라미터 | 설명 |
| --- | --- | --- | --- |
| `/ping` | `GET` |  | 문자열 `pong` 을 반환합니다. 단순 헬스 체크 용도입니다. |
| `/store` | `POST` |  | 업로드할 파일을 요청 본문에 첨부합니다. 서버 로컬 디스크(예: `/data` 디렉터리)에 파일을 저장합니다. 구현에 따라 `multipart/form-data` 기반 업로드를 기대합니다. |
| `/fetch` | `GET` | `filename=https://www.example.com` | `filename` 파라미터에는 덤버킷이 cURL 요청을 보낼 **대상 URL(URI)** 을 전달합니다. 이름은 `filename` 이지만, SSRF 실습을 위해 설계된 이 엔드포인트에서는 “저장된 파일 이름”이 아니라 **임의의 타겟 URI** 를 의미합니다. |

### 간단한 요청 예시

```bash
# 헬스 체크
curl "http://localhost:5000/ping"
# → pong

# 파일 업로드 예시 (구현이 multipart/form-data 를 사용할 경우)
curl -F "file=@test.txt" "http://localhost:5000/store"

# 단순 HTTP fetch 예시
curl "http://localhost:5000/fetch?filename=http://example.com/"

# gopher 기반 SSRF(형태 예시, payload 생략)
curl "http://localhost:5000/fetch?filename=gopher://internal-db:3306/_<raw-payload>"
```

---

## 실행 방법

이 방법은 MySQL이 내부 네트워크에 구성되었다는 가정 아래 `docker-compose.yml` 을 작성합니다.

### 1. 내부 네트워크 구성

```python
version: "3.9"

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ssrf-bucket
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=development
    depends_on:
      - mysql
    networks:
      - ssrf-net

  mysql:
    image: mysql:8.0
    container_name: ssrf-mysql
    restart: unless-stopped
    environment:
      MYSQL_ALLOW_EMPTY_PASSWORD: "yes"
      MYSQL_ROOT_PASSWORD: ""
      MYSQL_DATABASE: testdb
      MYSQL_USER: testuser
      MYSQL_PASSWORD: testpass
    ports:
      - "3306:3306"
    volumes:
      - mysql-data:/var/lib/mysql
    command: ["--default-authentication-plugin=mysql_native_password"]
    networks:
      - ssrf-net

networks:
  ssrf-net:
    driver: bridge

volumes:
  mysql-data:
```

- 덤버킷의 내부 포트는 기본적으로 `5000` 으로 설정되어 있습니다.
- 다른 포트를 사용하려면:
    - 컨테이너 외부 포트는 `p <host_port>:5000` 으로 매핑을 변경하고,
    - 애플리케이션 내부 포트 번호는 현재 버전에서는 `main.py` 내 Flask 실행 부분에서 직접 수정해야 합니다.

### 2. 테스트용 Docker compose 네트워크 실행

```bash
docker compose up --build
```

이제 외부 사용자는 직접 `internal-mysql:3306` 에 접근할 수 없지만, 덤버킷 `/fetch` 엔드포인트에 하기와 같은 URL을 전달해 내부 서비스로 요청을 우회 전송하는 SSRF 시나리오를 실습할 수 있습니다.

```
gopher://internal-mysql:3306/_<raw-payload>
```

---

## 참고 자료

### 도보시오

| 번호 | 링크 | 설명 |
| --- | --- | --- |
| 01 | https://curl.se/ch/7.71.1.html | cURL 7.71.1 에서 URL 내 NUL 바이트(`\\x00`) 처리 방식이 변경된 릴리스 노트입니다. |
| 02 | https://me2nuk.com/SSRF-Gopher-Protocol-MySQL-Raw-Data-Exploit/ | gopher 프로토콜을 활용하여 MySQL 등 내부 서비스에 raw 데이터(쿼리)를 주입하는 SSRF 기법을 설명하는 자료입니다. |


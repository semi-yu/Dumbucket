## Overview

### What is Dumbucket?

Dumbucket is a **file storage / proxy server intentionally designed to learn and reproduce SSRF (Server-Side Request Forgery) vulnerabilities using the Gopher protocol**.

This software was developed as a term project for the “Web Security” course in the 2nd semester of 2025 at Kyonggi University. The backend is built with the Python Flask framework, and other dependencies are listed in `pyproject.toml`.

### Precautions

- This project is for **educational and research purposes only**.
- Dumbucket is intentionally configured with vulnerabilities, so it **must not be exposed directly to the Internet or used in any production environment.**

---

## Details

### Architecture and Threat Model Overview

- **Dumbucket**
    - Flask application + pycurl
    - Uses the cURL binary installed in the system to make requests to external / internal resources.
- **Deployment assumptions**
    - The Dumbucket container runs on the same Docker network as internal infrastructure (MySQL, Redis, internal HTTP services, etc.).
    - External users can only access Dumbucket’s HTTP port (port 5000 by default).
- **Threat model (summary)**
    1. An attacker sends an arbitrary URL to the `/fetch` endpoint.
    2. Dumbucket performs a server-side cURL request to that URL **without any filtering on host, protocol, or port**.
    3. By using the `gopher://` scheme, an attacker can send arbitrary protocol data to services that are only exposed on the internal network (e.g., an internal database) and thereby induce query execution or unauthorized access to sensitive data.

---

### How is it implemented?

1. **Base image and cURL version**
    - As can be seen in the `Dockerfile`, Dumbucket runs inside a Debian 9.13–based container. This image includes **cURL 7.52.1**.
    - Starting from cURL 7.71.1, URLs that contain a NUL byte (`\x00`) are rejected. The gopher-based SSRF payload used in this project includes `%00` (NUL-byte encoding) in the middle of the URL, so we use an environment with the **older cURL (7.52.1)** where NUL bytes are still allowed to reproduce the behavior. [See 01]

2. **Request handling flow**
    1. The Flask application directly calls the cURL library using pycurl.
        - This is a design choice to leverage cURL’s various options and its support for multiple protocols.
    2. For `/fetch` requests, Dumbucket **does not perform any security checks** such as allow-list validation, internal network blocking, or scheme/port filtering on the given URL.
        - As a result, an **SSRF vulnerability** exists where the server can send requests to arbitrary URIs specified by external users.
    3. By using the `gopher://` scheme, an attacker can send **arbitrary protocol byte streams** to ports of internal services such as MySQL, and thereby induce query execution, data exfiltration, or other unauthorized access to internal resources. [See 02]

3. **Gopher-based SSRF example (conceptual)**  
    - Suppose there is a service `mysql:3306` that is only exposed inside the internal network.
    - An attacker can send a URL of the form  
      `gopher://mysql:3306/_<raw-mysql-payload>`  
      to the `/fetch` endpoint.
    - Dumbucket passes this URL directly to cURL, which then sends the raw payload to the internal MySQL service and executes queries.
    - This README does not list the full payload, but using this structure you can reproduce **SSRF scenarios where internal database queries are executed indirectly from the outside**.

---

### API Endpoints

| Path    | Method | Parameter       | Description |
|--------|--------|-----------------|-------------|
| `/ping`  | `GET`  |                 | Returns the string `pong`. Used as a simple health check. |
| `/store` | `POST` |                 | Attach the file to upload in the request body. The file is stored on the server’s local disk (e.g., `/data` directory). Depending on the implementation, `multipart/form-data`–based uploads are expected. |
| `/fetch` | `GET`  | `filename=<>`   | The `filename` parameter provides the **target URL (URI)** that Dumbucket will request via cURL. Although the parameter name is `filename`, in this SSRF-oriented endpoint it represents an **arbitrary target URI**, not a “stored file name.” |

### Simple request examples

```bash
# Health check
curl "http://localhost:5000/ping"
# → pong

# File upload example (if implemented with multipart/form-data)
curl -F "file=@test.txt" "http://localhost:5000/store"

# Simple HTTP fetch example
curl "http://localhost:5000/fetch?filename=http://example.com/"

# Gopher-based SSRF (shape example, payload omitted)
curl "http://localhost:5000/fetch?filename=gopher://internal-db:3306/_<raw-payload>"
```

---

## How to Run

The following assumes that MySQL is configured on the internal network and shows an example docker-compose.yml.

### 1. Internal network configuration

```version: "3.9"

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

- Dumbucket’s internal port is 5000 by default.
- To use a different port:
  - For the external container port, change the mapping to something like - "8080:5000" in the ports section, or when using docker run, use -p <host_port>:5000.
  - In the current version, if you want to change the application’s internal port, you need to manually modify the Flask run configuration inside main.py.

### 2. Run the Docker Compose network

```bash
docker compose up --build
```

Now, even though external users cannot directly access internal-mysql:3306, they can send a URL like the following to Dumbucket’s /fetch endpoint to practice an SSRF scenario where requests to the internal service are relayed:

```
gopher://internal-mysql:3306/_<raw-payload>
```

---

## References

### See also

| No.	| Link | Description |
|-----|------|-------------|
| 01 | https://curl.se/ch/7.71.1.html | Release notes for cURL 7.71.1 describing changes to the handling of NUL bytes (\x00) in URLs. |
| 02 | https://me2nuk.com/SSRF-Gopher-Protocol-MySQL-Raw-Data-Exploit/ | A resource explaining how to use the Gopher protocol to inject raw data (queries) into internal services such as MySQL in SSRF attacks. (korean) |

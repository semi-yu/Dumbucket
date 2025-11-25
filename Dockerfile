# Debian with old curl
FROM debian:stretch

RUN printf 'deb http://archive.debian.org/debian stretch main\n\
deb http://archive.debian.org/debian-security stretch/updates main\n' > /etc/apt/sources.list \
    && apt-get -o Acquire::Check-Valid-Until=false update

RUN apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        build-essential \
        libcurl4-openssl-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.cargo/bin:/root/.local/bin:${PATH}" \
    PYCURL_SSL_LIBRARY=openssl \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY . /app

RUN uv venv \
    && uv pip install pycurl flask

EXPOSE 5000

CMD ["uv", "run", "main.py"]

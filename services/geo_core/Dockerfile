FROM rust:1.75 as builder
WORKDIR /usr/src/geo_core
COPY Cargo.toml .
COPY src ./src
# We need to compile the python extension. Better to do it in python image with maturin.
# Let's switch approach:

FROM python:3.11-slim

# Install Rust toolchain
RUN apt-get update && apt-get install -y curl build-essential \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

RUN useradd -m -u 1000 hydroviz
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Cargo.toml .
COPY src ./src
RUN maturin develop --release

COPY main.py .

RUN chown -R 1000:1000 /app
USER 1000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]

FROM python:3.11-slim

# Install Rust toolchain and build dependencies (must be root for install)
RUN apt-get update && apt-get install -y curl build-essential pkg-config \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app

# Install Python deps first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Rust source and build the PyO3 extension as root
COPY Cargo.toml .
COPY src ./src
RUN maturin build --release && pip install --no-cache-dir target/wheels/*.whl && rm -rf target

# Copy Python entrypoint
COPY main.py .

# Create non-root user and hand over ownership
RUN useradd -m -u 1000 hydroviz && chown -R 1000:1000 /app
USER 1000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]

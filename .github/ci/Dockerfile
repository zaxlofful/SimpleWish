# ---------- Stage 1: builder ----------
FROM python:3.11-slim AS builder

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Build-time system deps for Python packages
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
       build-essential \
       libffi-dev \
       libssl-dev \
       pkg-config \
       libc6-dev \
  && python -m pip install --upgrade pip setuptools wheel \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy Python scripts and requirements
COPY scripts/ ./scripts/

# Install Python deps (wheels get built here if needed)
RUN pip install --no-cache-dir -r scripts/requirements.txt

# At this point /usr/local has Python + your deps; /app has your code.


# ---------- Stage 2: runtime ----------
FROM python:3.11-slim AS runtime

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy Python runtime + installed deps
COPY --from=builder /usr/local /usr/local
# Copy app
COPY --from=builder /app /app

# Create non-root user
RUN groupadd -r ci -g 1000 \
  && useradd -r -g ci -u 1000 -m -d /home/ci -s /bin/bash ci

USER ci
WORKDIR /app

ENV PATH="/home/ci/.local/bin:${PATH}"

# Default command for running QR generation scripts
# Example: python scripts/generate_qr_svg.py --root-domain "https://example.com" --pattern "*.html" --out-dir /tmp/qr
CMD ["python", "-c", "print('SimpleWish CI image ready. Use with: python scripts/generate_qr_svg.py or python scripts/inject_qr_svg.py')"]
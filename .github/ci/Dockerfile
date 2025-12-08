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

# Install Python deps (wheels get built here if needed)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY . .

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

# Default command — change to your real entrypoint if you want
CMD ["python", "your_entrypoint.py"]
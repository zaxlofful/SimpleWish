FROM python:3.11-slim

# Install build-time dependencies required for many Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    pkg-config \
    libc6-dev \
  && python -m pip install --upgrade pip setuptools wheel \
  # Remove build-time packages to keep image small. Keep runtime libraries.
  && apt-get purge -y --auto-remove build-essential pkg-config libc6-dev \
  && apt-get purge -y libssl-dev libffi-dev || true \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create a non-root user
RUN groupadd -r ci && useradd -r -g ci -m -d /home/ci -s /bin/bash ci
USER ci

WORKDIR /home/ci

ENV PATH="/home/ci/.local/bin:${PATH}"

CMD ["/bin/bash"]

FROM python:3.11-alpine

# Install build-time dependencies required for many Python packages
RUN apk add --no-cache --virtual .build-deps \
    build-base \
    libffi-dev \
    openssl-dev \
    linux-headers \
  && python -m pip install --upgrade pip setuptools wheel \
  && apk del .build-deps

# Create a non-root user
RUN addgroup -S ci && adduser -S -G ci ci
USER ci

WORKDIR /home/ci

ENV PATH="/home/ci/.local/bin:${PATH}"

CMD ["/bin/sh"]

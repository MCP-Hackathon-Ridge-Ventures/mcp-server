# Use Alpine Linux as the base image
FROM alpine:3.18

# Set environment variables
ENV NODE_VERSION=22
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apk add --no-cache \
    nodejs \
    npm \
    python3 \
    python3-dev \
    py3-pip \
    gcc \
    musl-dev \
    linux-headers \
    curl \
    bash

# Create symlink for python command
RUN ln -sf python3 /usr/bin/python

# Create app directory
WORKDIR /app

# Copy all files to app directory first
COPY . /app/

# Install Node.js dependencies
WORKDIR /app/template-app
RUN npm install
WORKDIR /app

# Install Python dependencies using pyproject.toml
RUN pip install --no-cache-dir -e .

# Expose ports
# Port 8000 for FastAPI
# Port 3000 for Node.js (common default)
EXPOSE 3000 8000

# Set working directory
WORKDIR /app

# Default command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


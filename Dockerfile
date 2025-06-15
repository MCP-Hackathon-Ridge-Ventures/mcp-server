# Use Python slim image as base
FROM python:3.12-slim

# Set environment variables
ENV NODE_VERSION=18
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install Node.js
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy all files to app directory first
COPY . /app
COPY ./template-web-app/ /app/template-web-app

# Install Node.js dependencies
WORKDIR /app/template-web-app
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
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]


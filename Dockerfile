# Use Python slim image as base
FROM python:3.12-slim

# Set environment variables
ENV NODE_VERSION=20
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install Node.js and build essentials
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify Node.js and npm installation
RUN node --version && npm --version

# Create app directory
WORKDIR /app

# Copy Python project files first
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install Python dependencies using pyproject.toml
RUN pip install --no-cache-dir -e .

# Copy Node.js project files
COPY template-web-app/package*.json ./template-web-app/

# Install Node.js dependencies first (better caching)
WORKDIR /app/template-web-app
RUN npm ci

# Copy the rest of the Node.js application files
COPY template-web-app/ ./

# Build the Node.js application
RUN npm run build

# Switch back to main app directory
WORKDIR /app

# Copy any remaining files (node_modules excluded via .dockerignore)
COPY . .

# Expose ports
# Port 8000 for FastAPI
# Port 3000 for Node.js (common default)
EXPOSE 3000 8000

# Default command
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]


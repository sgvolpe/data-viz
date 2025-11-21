# ===========================
# DataViz Dockerfile
# ===========================

# Base image: Python 3.13 slim
FROM python:3.13-slim

# ---------------------------
# Environment variables
# ---------------------------
ENV PIPENV_VENV_IN_PROJECT=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ---------------------------
# Set working directory
# ---------------------------
WORKDIR /app

# ---------------------------
# Install system dependencies for Playwright
# ---------------------------
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libglib2.0-0 \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------
# Install pipenv
# ---------------------------
RUN pip install --upgrade pip
RUN pip install pipenv

# ---------------------------
# Copy Pipfile and Pipfile.lock
# ---------------------------
COPY Pipfile Pipfile.lock /app/

# ---------------------------
# Install Python dependencies
# ---------------------------
RUN pipenv install --deploy --ignore-pipfile

# ---------------------------
# Copy Python code
# ---------------------------
COPY data_viz /app/data_viz

# ---------------------------
# Copy CSS files and HTML templates
# ---------------------------
COPY data_viz/schemas/*.css /app/data_viz/schemas/
COPY data_viz/schemas/templates/ /app/data_viz/schemas/templates/

# ---------------------------
# Install Playwright browsers
# ---------------------------
RUN pipenv run python -m playwright install

# ---------------------------
# Expose the port your app uses
# ---------------------------
EXPOSE 8050

# ---------------------------
# Run the app using pipenv
# ---------------------------
CMD ["pipenv", "run", "python", "main.py"]

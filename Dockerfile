# AI Collections Web Scraper - Docker Container
# 
# Build: docker build -t ai-scraper .
# Run:   docker run -v $(pwd)/data:/output ai-scraper \
#          --start-url https://books.toscrape.com \
#          --max-pages 50 \
#          --output /output/books.jsonl

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scraper.py .
COPY cli.py .

# Create output directory
RUN mkdir -p /output

# Make CLI executable
RUN chmod +x cli.py

# Set entrypoint to CLI
ENTRYPOINT ["python", "cli.py"]

# Default arguments (can be overridden)
CMD ["--help"]


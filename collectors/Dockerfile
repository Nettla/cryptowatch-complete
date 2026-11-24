
FROM python:3.14-slim
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools
RUN pip install --no-cache-dir -r requirements.txt
RUN pip uninstall -y setuptools

# Copy collector application
COPY app.py .

# Run as a non-root user
USER 65534:65534

CMD ["python", "app.py"]

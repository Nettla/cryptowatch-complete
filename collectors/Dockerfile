
FROM python:3.14-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy collector application
COPY app.py .

# Run as a non-root user
USER 65534:65534

CMD ["python", "app.py"]

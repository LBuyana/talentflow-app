FROM python:3.10-slim

WORKDIR /code

# Install system dependencies needed for PyTorch and sentence-transformers
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /code/requirements.txt

# Install Python packages with pip upgrade
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /code/requirements.txt

COPY . /code/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
# Use the official Python base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /code

# Copy the requirements file and install dependencies
COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt

# Copy the rest of the application code
COPY . /code/

# This is the critical change:
# Run uvicorn on port 8080, which is the default port Cloud Run expects
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
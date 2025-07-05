# Use official Python 3.12 image as base
FROM python:3.12

# Install system dependencies for GDAL and GEOS
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    python3-gdal

# Set environment variables for GDAL & GEOS
ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so.32
ENV GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install GDAL Python bindings inside virtualenv
RUN pip install --no-cache-dir gdal==3.6.2

# Copy project files
COPY . .

# Expose Django port
EXPOSE 8000

# Run the application

CMD ["gunicorn", "fitarena.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers=4"]


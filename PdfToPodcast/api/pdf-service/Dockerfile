FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for OCR (tesseract), PDF-to-image (poppler), and file type detection (libmagic1)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# python-magic-bin is for Windows; python-magic is for Linux. This ensures the correct library is used.
RUN sed -i 's/python-magic-bin/python-magic/' requirements.txt

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application files into the container
COPY . .

# Expose the port the service runs on
EXPOSE 8001

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

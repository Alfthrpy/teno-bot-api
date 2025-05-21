# Base image
FROM python:3.11-slim

# Set work directory
WORKDIR /app


# Install PyTorch dari source resmi
RUN pip install --no-cache-dir torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu

# Lalu install sisanya
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Salin seluruh isi project ke dalam container
COPY . .

# Jalankan aplikasi FastAPI menggunakan uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
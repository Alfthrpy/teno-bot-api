# Menggunakan base image Python versi 3.9 seperti yang direkomendasikan Hugging Face
# Baca dokumentasi lengkapnya di: https://huggingface.co/docs/hub/spaces-sdks-docker
FROM python:3.9

# Dua baris berikut diperlukan agar Dev Mode berfungsi dengan baik.
# Pelajari lebih lanjut tentang Dev Mode di: https://huggingface.co/dev-mode-explorers
RUN useradd -m -u 1000 user
WORKDIR /app

# Salin file requirements.txt terlebih dahulu dan berikan kepemilikan ke 'user'
COPY --chown=user ./requirements.txt requirements.txt
# Install dependensi dari requirements.txt. Sebaiknya upgrade pip terlebih dahulu.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --upgrade -r requirements.txt

# Install PyTorch secara spesifik (seperti di Dockerfile Anda sebelumnya)
# Catatan PENTING: Cara terbaik adalah memasukkan baris instalasi PyTorch
# (torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu)
# ke dalam file requirements.txt Anda. Jika sudah ada di sana, baris RUN di bawah ini TIDAK diperlukan.
RUN pip install --no-cache-dir torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu

# Salin seluruh kode aplikasi Anda ke dalam direktori /app dan berikan kepemilikan ke 'user'
COPY --chown=user . /app

# Ganti ke user non-root yang telah dibuat
USER user

# Set variabel lingkungan untuk user
ENV HOME=/home/user \
	PATH=/home/user/.local/bin:$PATH

# Jalankan aplikasi FastAPI menggunakan uvicorn
# Menggunakan 'app.main:app' sesuai dengan struktur aplikasi Anda
# Menggunakan port 7860 seperti yang direkomendasikan Hugging Face
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
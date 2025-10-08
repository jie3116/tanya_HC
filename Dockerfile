# Dockerfile

# Tahap 1: Gunakan base image Python yang ringan
FROM python:3.11-slim

# Tetapkan direktori kerja di dalam container
WORKDIR /app

# Salin file requirements terlebih dahulu untuk caching yang lebih baik
COPY requirements.txt .

# Install semua dependensi Python
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh sisa kode aplikasi Anda ke dalam container
COPY . .

# Tetapkan environment variable untuk memberitahu Flask/Gunicorn di mana aplikasi berada
ENV FLASK_APP=app:app

# Ekspos port 5001 agar bisa diakses dari luar container
EXPOSE 5001

# Perintah untuk menjalankan aplikasi saat container dimulai
# Menggunakan Gunicorn sebagai server WSGI level produksi
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "app:app"]
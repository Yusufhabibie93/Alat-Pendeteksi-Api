# Gunakan image dasar Python
FROM python:3.9-slim

# Setel direktori kerja di dalam container
WORKDIR /app

# Salin requirements.txt ke dalam container
COPY requirements.txt .

# Instal dependensi
RUN pip install --no-cache-dir -r requirements.txt

# Salin semua file proyek ke dalam container
COPY . .

# Jalankan aplikasi
CMD ["python", "app.py"]

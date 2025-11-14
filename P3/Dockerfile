FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

# instalar dependencias del sistema (añade las que necesites)
RUN apt-get update && apt-get install -y --no-install-recommends     build-essential     git     curl   && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER app

EXPOSE 8080

CMD ["gunicorn", "-b", "0.0.0.0:8080", "space.app:app", "--workers", "2", "--timeout", "120"]

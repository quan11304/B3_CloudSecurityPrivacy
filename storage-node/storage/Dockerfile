FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

COPY init_music/*.mp3 ../storage/

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8083

CMD ["python", "app.py"]
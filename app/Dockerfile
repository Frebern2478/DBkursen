FROM python:3.10-slim
LABEL authors="rasmu"

WORKDIR /dbkursen
COPY requirements.txt ./

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
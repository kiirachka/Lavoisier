FROM python:3.13-slim

WORKDIR /opt/render/project/src

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "run.py"]

FROM python:3.11-slim
LABEL authors="jnaed"

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

CMD ["python", "./jamf_inventory/jamf_inventory.py"]
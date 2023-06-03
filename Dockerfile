FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

WORKDIR ./jamf_inventory

CMD ["python", "jamf_inventory.py"]
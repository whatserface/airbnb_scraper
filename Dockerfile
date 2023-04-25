# syntax=docker/dockerfile:1
FROM python:3.10.6

WORKDIR /python

ENV PYTHONUNBUFFERED=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
WORKDIR /python/airbnb
ENTRYPOINT ["scrapy", "crawl", "airbnb_crawl", "-o", "output/output.json"]
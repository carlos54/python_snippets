FROM python:3.7.7-buster

# extra dependencies (over what buildpack-deps already includes)
RUN apt-get update && apt-get install -y --no-install-recommends apt-utils \
    redis-server \
    ghostscript

RUN set -ex \
    && wget  https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz \
    && tar xvf wkhtmltox-0.12.4_linux-generic-amd64.tar.xz \
    && mv wkhtmltox/bin/wkhtmlto* /usr/local/bin

WORKDIR /root/www/

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

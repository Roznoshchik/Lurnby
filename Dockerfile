FROM python:3.9.9

RUN apt-get update && \
    apt-get install -y postgresql-server-dev-all \
    gcc \
    python3-dev \
    musl-dev \
    nodejs \
    npm \
    mupdf-tools pdftk

RUN curl -fsSL https://deb.nodesource.com/setup_current.x | bash - && \
 apt-get install -y nodejs

RUN useradd lurnby

WORKDIR /home/lurnby

COPY requirements.txt requirements.txt
RUN python3 -m venv venv
RUN venv/bin/pip install --upgrade pip
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn

COPY app app
COPY migrations migrations
COPY learnbetter.py config.py boot.sh data.py package.json package-lock.json ./
RUN chmod +x boot.sh

ENV FLASK_APP learnbetter.py

RUN chown -R lurnby:lurnby ./
USER lurnby

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
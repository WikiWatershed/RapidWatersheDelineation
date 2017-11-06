FROM quay.io/wikiwatershed/taudem:5.3.8

MAINTAINER Azavea <systems@azavea.com>

COPY requirements.txt /tmp/
COPY src/api/requirements.txt /tmp/src/api/
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    pip install --no-cache-dir -r /tmp/src/api/requirements.txt && \
    rm /tmp/requirements.txt && \
    rm /tmp/src/api/requirements.txt

ENV PYTHONPATH /usr/src:$PYTHONPATH

COPY ./rwd_drb /usr/src/rwd_drb
COPY ./rwd_nhd /usr/src/rwd_nhd
COPY ./src/api /usr/src/api

WORKDIR /usr/src/api

ENTRYPOINT ["/usr/local/bin/gunicorn"]

CMD ["--workers", "4", \
     "--timeout", "60", \
     "--log-syslog", \
     "--bind", "0.0.0.0:5000", \
     "main:app"]

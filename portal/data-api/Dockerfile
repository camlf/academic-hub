FROM python:3.6-alpine as base
FROM base as builder
RUN mkdir /install
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN apk add --no-cache --virtual .build-deps \
    ca-certificates gcc make postgresql-dev linux-headers musl-dev \
    libffi-dev jpeg-dev zlib-dev \
    && pip install --install-option="--prefix=/install" -r /requirements.txt --no-cache-dir \
    && find /usr/local \
        \( -type d -a -name test -o -name tests \) \
        -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
        -exec rm -rf '{}' + \
    && runDeps="$( \
        scanelf --needed --nobanner --recursive /usr/local \
                | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
                | sort -u \
                | xargs -r apk info --installed \
                | sort -u \
    )" \
    && apk add --virtual .rundeps $runDeps \
    && apk del .build-deps
# RUN pip install --install-option="--prefix=/install" -r /requirements.txt --no-cache-dir
FROM base
COPY --from=builder /install /usr/local
RUN mkdir /app
COPY app.py /app
WORKDIR /app
RUN pip install python-dateutil marshmallow
EXPOSE 80 
CMD ["python", "app.py", "--workers", "4"]

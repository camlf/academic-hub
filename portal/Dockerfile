FROM python:3.9-slim-buster as base
FROM base as builder
RUN mkdir /install
WORKDIR /install
COPY auth_app/requirements.txt /requirements.txt
RUN pip install --upgrade pip
RUN pip install --prefix=/install -r /requirements.txt --no-cache-dir 

FROM base
COPY --from=builder /install /usr/local
COPY auth_app /app
WORKDIR /app
EXPOSE 3000 
CMD ["python", "auth0_resp.py"]

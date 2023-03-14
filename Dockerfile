FROM python:3.8

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY hvsrweb.py /app
COPY /assets /app/assets
COPY /data /app/data
COPY /img /app/img

CMD python hvsrweb.py

# docker build . -t hvsrweb:dev
# docker run -p 8050:8050 hvsrweb:dev
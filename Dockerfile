FROM python:3.7-slim

ADD . /usr/local/spades

RUN useradd -ms /bin/bash spades \
    && pip install -r /usr/local/spades/requirements.txt \
    && chown -R spades /usr/local/spades

WORKDIR /usr/local/spades
USER spades

EXPOSE 8080
CMD ["python", "/usr/local/spades/main.py"]

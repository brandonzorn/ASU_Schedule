FROM python:3.12.8-slim

RUN apt update

COPY ./requirements /requirements
RUN pip install --no-cache-dir -r requirements/prod.txt
RUN rm -rf requirements

COPY ./asuschedule /asuschedule/
WORKDIR /asuschedule

CMD python import_document.py && python main.py
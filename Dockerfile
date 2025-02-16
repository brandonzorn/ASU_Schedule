FROM python:3.13.2-slim

COPY ./requirements /requirements
RUN pip install --no-cache-dir -r requirements/prod.txt
RUN rm -rf requirements

COPY ./asuschedule /asuschedule/
WORKDIR /asuschedule

CMD ["python", "main.py"]
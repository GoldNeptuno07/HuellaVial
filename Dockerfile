FROM python:3.13-slim

# Set env variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=HuellaVial.settings

WORKDIR /code

# Dependencies
COPY requirements.txt /code/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY HuellaVial/ /code/HuellaVial/
COPY dashboard/ /code/dashboard/
COPY manage.py /code/
COPY .env /code/

# Django static files
RUN python manage.py collectstatic --noinput
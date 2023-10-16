FROM python:3.10
WORKDIR /foodgram_app
RUN pip install gunicorn==20.1.0
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY . .
COPY ./data/ingridients.csv ./data/
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"]
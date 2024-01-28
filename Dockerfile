FROM python:3.9
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
EXPOSE 5000
#ENV FLASK_APP=my_flask.py
CMD ["flask", "--app", "main","run","--host=0.0.0.0", "--port=5000"]

FROM python:3.8

RUN mkdir -p /smsbot
WORKDIR /smsbot

RUN python -m pip install --upgrade pip

COPY requirements.txt .
RUN python -m pip install -r requirements.txt

COPY . /smsbot

CMD ["python", "main.py"]
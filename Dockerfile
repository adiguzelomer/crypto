FROM python:3.8.5

# Create app directory
WORKDIR /app

# Install app dependencies
COPY ./requirements.txt ./

RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install -r requirements.txt

# Bundle app source
COPY . /app

CMD [ "python3", "main_bot.py" ]
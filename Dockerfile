
FROM python:3.10

MAINTAINER Gilbert Yoder <yodergilbert1@gmail.com>

RUN apt-get update && apt-get install -y supervisor

RUN echo "python /deploy/wiki_app/main.py" >> /home/start_wiki
RUN chmod +x /home/start_wiki

RUN mkdir /deploy 
COPY wiki_app /deploy/wiki_app

# RUN ls

WORKDIR /deploy/wiki_app/
RUN pip install -r requirements.txt

# Setup supervisord
RUN mkdir -p /var/log/supervisor
COPY misc/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY misc/hypercorn.conf /etc/supervisor/conf.d/hypercorn.conf

# Start processes
CMD ["/usr/bin/supervisord"]
FROM docker.elastic.co/logstash/logstash:7.17.9

COPY logstash.conf /usr/share/logstash/pipeline/logstash.conf

ENV ELASTICSEARCH_HOST=elasticsearch
ENV ELASTICSEARCH_PORT=9200



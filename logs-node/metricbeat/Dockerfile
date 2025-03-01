FROM docker.elastic.co/beats/metricbeat:7.17.9

USER root

COPY --chown=root:root metricbeat.yml /usr/share/metricbeat/metricbeat.yml

RUN chmod 644 /usr/share/metricbeat/metricbeat.yml

USER metricbeat

ENV ELASTICSEARCH_HOST=elasticsearch
ENV ELASTICSEARCH_PORT=9200

ENV KIBANA_HOST=kibana
ENV KIBANA_PORT=5601



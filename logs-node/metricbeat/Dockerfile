FROM docker.elastic.co/beats/metricbeat:7.17.9

USER root

COPY --chown=root:root metricbeat.yml /usr/share/metricbeat/metricbeat.yml

RUN chmod 644 /usr/share/metricbeat/metricbeat.yml

USER metricbeat

ENV ELASTICSEARCH_HOST=10.43.154.125
ENV ELASTICSEARCH_PORT=9200

ENV KIBANA_HOST=10.43.53.64
ENV KIBANA_PORT=5601



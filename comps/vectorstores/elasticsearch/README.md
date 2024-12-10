# Start Elasticsearch server

## 1. Download Elasticsearch image

```bash
docker pull docker.elastic.co/elasticsearch/elasticsearch:8.16.0
```

## 2. Run Elasticsearch service

```bash
docker run -p 9200:9200 -p 9300:9300 -e ES_JAVA_OPTS="-Xms1g -Xmx1g" -e "discovery.type=single-node" -e "xpack.security.enabled=false" \ docker.elastic.co/elasticsearch/elasticsearch:8.16.0
```

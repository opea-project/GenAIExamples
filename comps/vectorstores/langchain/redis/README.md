# Start Redis server

## 1. Download Redis image

```bash
docker pull redis/redis-stack:7.2.0-v9
```

## 2. Run Redis service

```bash
docker run -p 6379:6379 -p 8001:8001 redis/redis-stack:7.2.0-v9
```

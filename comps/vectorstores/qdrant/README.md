# Start Qdrant server

## 1. Download Qdrant image

```bash
docker pull qdrant/qdrant
```

## 2. Run Qdrant service

```bash
docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage:z qdrant/qdrant
```

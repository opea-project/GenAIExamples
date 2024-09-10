# Start PGVector server

## 1. Download Pgvector image

```bash
docker pull pgvector/pgvector:0.7.0-pg16
```

## 2. Configure the username, password and dbname

```bash
export POSTGRES_USER=testuser
export POSTGRES_PASSWORD=testpwd
export POSTGRES_DB=vectordb
```

## 3. Run Pgvector service

```bash
docker run --name vectorstore-postgres -e POSTGRES_USER=${POSTGRES_USER} -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_DB=${POSTGRES_DB} -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} -d -v ./init.sql:/docker-entrypoint-initdb.d/init.sql -p 5432:5432 pgvector/pgvector:0.7.0-pg16
```

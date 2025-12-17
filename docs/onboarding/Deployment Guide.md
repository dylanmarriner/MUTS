# Deployment Guide

## Local Deployment
```bash
docker compose up -d
```

## Production Deployment
1. Build Docker images:
```bash
docker build -t muts-frontend -f frontend.Dockerfile .
docker build -t muts-backend -f backend.Dockerfile .
```

2. Kubernetes deployment:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: muts-backend
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: backend
        image: muts-backend:latest
        envFrom:
        - secretRef:
            name: muts-secrets
```

## DigitalOcean
1. Create Droplet
2. Install Docker
3. Run:
```bash
docker swarm init
docker stack deploy -c docker-compose.prod.yml muts
```

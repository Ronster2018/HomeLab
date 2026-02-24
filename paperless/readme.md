# Paperless-NGX – Home Kubernetes Setup

This deployment includes:

- Standalone PostgreSQL StatefulSet
- Separate PVCs for Paperless data and database
- Backup CronJob for Postgres
- Resource requests and limits
- Traefik HTTPS ingress (TLS will be configured later)
- Redis caching backend
- DNS via Pi-hole (`paperless.home.arpa`)

---

## Architecture

| Component | Notes |
|----------|-------|
| Paperless | Deployment, connects to Redis & Postgres |
| PostgreSQL | StatefulSet, PVC for DB, TLS enabled |
| Redis | Existing Pod in cluster |
| Storage | Separate PVCs for documents & DB |
| Backup | CronJob saves database snapshots |
| Ingress | Traefik over HTTPS |
| DNS | Pi-hole resolves *.home.arpa |

---

## Storage

| PVC | MountPath | Purpose |
|-----|-----------|---------|
| paperless-data-pvc | /usr/src/paperless/data | Document storage |
| paperless-db-pvc   | /var/lib/postgresql/data | PostgreSQL database |
| paperless-backup-pvc | /backups | CronJob backup storage |

---

## Configuration

- **ConfigMap**: connection details for DB & Redis, timezone, URL
- **Secret**: DB credentials, Paperless SECRET_KEY
- Paperless connects to DB via **TLS**

---

## Deployment Notes

- Paperless Deployment uses `envFrom` (all config + secrets)
- Postgres StatefulSet uses explicit `env` mappings
- Resource limits set for both pods
- Backup CronJob scheduled daily at 2am

---

## Access

- Browser: `https://paperless.home.arpa`
- Database:

```bash
kubectl exec -it sts/postgres -n paperless -- psql -U paperless paperless
```
---

## 🌍 DNS

Add to Pi-hole:


---

## 🧪 Testing

### Check Pods

```bash
kubectl get pods -n paperless
```

### Check Service
```bash
kubectl get svc -n paperless
```

### Check DB Connectivity
```bash
kubectl exec -it deploy/paperless -n paperless \
  -- psql -h localhost -U paperless paperless
```

### Check Redis Connectivity
```bash
kubectl exec -it deploy/paperless -n paperless \
  -- nc -z redis-service.redis.svc.cluster.local 6379
```
## Next Steps

1. **Enable TLS for PostgreSQL**
   - Generate self-signed or CA-signed certificates
   - Mount certs into Postgres StatefulSet
   - Configure Paperless DB connection to use TLS

2. **Add Traefik TLS for HTTPS**
   - Use cert-manager or self-signed certs
   - Update IngressRoute with `tls.certResolver`

3. **Backup & Restore Improvements**
   - Integrate Velero for PVC snapshots
   - Configure automated backup retention policies

4. **Monitoring & Metrics**
   - Traefik dashboard for ingress metrics
   - Pod and StatefulSet resource monitoring
   - Optional: Prometheus + Grafana for cluster monitoring

5. **Scaling**
   - Consider Horizontal Pod Autoscaler for Paperless
   - Scale Postgres StatefulSet with read replicas (if needed)

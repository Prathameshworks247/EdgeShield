# Rate-Limiter

A FastAPI project that demonstrates multiple rate-limiting algorithms and exposes Prometheus metrics for observability with Grafana.

LIVE ENDPOINTS TO TEST - https://rate-limiter-tjnd.onrender.com/docs

## Features
- FastAPI API with limited and unlimited endpoints
- Pluggable rate-limiting algorithms:
  - `FixedCounterWindow`
  - `TokenBucket`
  - `SlidingWindow`
  - `SlidingWindowCounter` (Redis-backed state)
- Prometheus metrics endpoint at `/metrics`
- Dockerized app
- Docker Compose stack with Prometheus + Grafana

## Project Structure
- `api.py` - main FastAPI app used by Docker (`uvicorn api:app`)
- `services/rate_limiter.py` - algorithm factory
- `algortihms/limiting_algorithms.py` - limiter implementations
- `services/cache.py` - Redis helper for sliding-window-counter state
- `Dockerfile` - app container image build
- `docker-compose.yml` - app + Prometheus + Grafana stack
- `monitoring/prometheus.yml` - Prometheus scrape config
- `monitoring/grafana/provisioning/datasources/datasource.yml` - Grafana datasource provisioning
- `main.py` - experimental middleware sample (not used by Docker entrypoint)

## API Endpoints
### `GET /limited`
- Returns: `"This is a limited use API"`
- Uses `FixedCounterWindow` per client IP in current implementation.
- Limit defaults to **60 requests per minute**.

### `GET /unlimited`
- Returns: `"Free to use API limitless"`

### `GET /metrics`
- Prometheus metrics scrape endpoint.

## Current Rate-Limit Behavior
For `/limited`:
- A limiter instance is created per client IP and stored in memory.
- `FixedCounterWindow` resets on **minute boundary** (`HH:MM:00`), not exactly 60 seconds after first request.
- Example: if limit is reached at `10:12:05`, reset happens at `10:13:00`.

## Redis Usage
Redis is implemented for `SlidingWindowCounter` in `services/cache.py` and used in `algortihms/limiting_algorithms.py`.

Important: `/limited` currently uses `FixedCounterWindow`, so Redis is not used by that route unless you switch algorithm selection.

## Metrics Exposed
- `http_requests_total{method,path,status}`
- `http_request_duration_seconds{method,path}` (histogram)
- `rate_limited_requests_total{path}`

## Run Locally (without Docker)
## 1. Create and activate virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

## 2. Install dependencies
```bash
pip install -r requirements.txt
```

## 3. Run app
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

## 4. Test quickly
```bash
curl http://localhost:8000/unlimited
curl http://localhost:8000/limited
curl http://localhost:8000/metrics
```

## Run with Docker (app only)
```bash
docker build -t rate-limiter:latest .
docker run --rm -p 8000:8000 rate-limiter:latest
```

## Run Full Observability Stack (App + Prometheus + Grafana)
```bash
docker compose up -d --build
```

Services:
- App: `http://localhost:8000`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

Grafana default login:
- Username: `admin`
- Password: `admin`

Note:
- Use `localhost` URLs in browser.
- `http://prometheus:9090` works only inside Docker network (for inter-container communication), not from host browser.

## Prometheus Checks
Open: `http://localhost:9090/targets`
- Ensure `rate-limiter-app` target is `UP`.

Useful PromQL:
```promql
sum(rate(http_requests_total[1m])) by (path, status)
```

```promql
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, path))
```

```promql
sum(rate(rate_limited_requests_total[1m])) by (path)
```

## Generate Load for Demo
```bash
for i in {1..120}; do curl -s http://localhost:8000/limited > /dev/null; done
for i in {1..50}; do curl -s http://localhost:8000/unlimited > /dev/null; done
```

## Troubleshooting
### Docker build error: `docker buildx build requires 1 argument`
Include build context:
```bash
docker build -t rate-limiter:latest .
```

### Browser error `prometheus` DNS not found
Use:
- `http://localhost:9090` (host browser)

### Prometheus/Grafana containers exit immediately
If you hit low-level Docker runtime errors (for example `exec format error` or exit `139`), reset Docker state:
```bash
docker compose down -v
docker system prune -af --volumes
```
Then restart Docker Desktop and run:
```bash
docker compose up -d --build
```

## Future Improvements
- Move limiter state fully to Redis for multi-instance consistency.
- Add configurable limits via environment variables.
- Add tests for each algorithm and boundary behavior.
- Fix lock semantics in Redis-based limiter implementation.

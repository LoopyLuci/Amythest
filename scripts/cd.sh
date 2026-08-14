#!/usr/bin/env bash
set -euo pipefail
IMAGE="${IMAGE:-amythest}"
TAG="${TAG:-latest}"
CONTAINER_NAME="amythest-cd-smoke-$$"
echo "==> docker build"
docker build -t "${IMAGE}:${TAG}" .
echo "==> docker run smoke test"
container_id=$(docker run -d --name "${CONTAINER_NAME}" -p 127.0.0.1:8125:8125 "${IMAGE}:${TAG}")
cleanup() {
  set +e
  docker rm -f "${container_id}" >/dev/null 2>&1 || true
}
trap cleanup EXIT
for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8125/status >/dev/null 2>&1; then
    echo "==> /status OK"
    break
  fi
  sleep 1
done
if ! curl -fsS http://127.0.0.1:8125/status >/dev/null 2>&1; then
  echo "Server did not become ready" >&2
  docker logs "${container_id}" || true
  exit 1
fi
python amythest/examples/verify_server.py
echo "==> done"

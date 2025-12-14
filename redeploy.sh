set -euo

echo "==> Pulling latest repository changes..."
git pull

echo "==> Bringing down existing services..."
docker compose -f ./src/server/compose.yml down

echo "==> Building and deploying new services..."
docker compose -f ./src/server/compose.yml up --build -d

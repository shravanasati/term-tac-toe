set -euo
git pull
docker compose -f ./src/server/compose.yml down
docker compose -f ./src/server/compose.yml up --build -d

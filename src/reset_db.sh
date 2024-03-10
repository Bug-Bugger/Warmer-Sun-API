sudo docker kill $(sudo docker ps | sed -n '2p' | awk '{print $1}')
rm Warmer-Sun.db
touch Warmer-Sun.db
sudo docker pull hoopoed/big_red_hack:latest
sudo docker compose up -d
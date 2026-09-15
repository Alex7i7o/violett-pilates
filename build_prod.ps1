Write-Host "Creating ViolettPilates-Deploy.zip..."
Compress-Archive -Path engine, proxy, config_pilates, config_estetica, landings, docker-compose.yml, .env.example, deploy.sh -DestinationPath ViolettPilates-Deploy.zip -Force
Write-Host "Done! You can upload ViolettPilates-Deploy.zip to your VPS."
# Guide de déploiement local de la plateforme EasyAIoT pour Windows

> Version du document : 1.0
> Date de mise à jour : 6 décembre 2025
> Systèmes pris en charge : Windows 10/11


## Table des matières

1. [Vue d'ensemble du système](#1-vue-densemble-du-système)
2. [Préparation de l'environnement](#2-préparation-de-lenvironnement)
3. [Déploiement des middleware](#3-déploiement-des-middleware)
4. [Démarrage des services](#4-démarrage-des-services)
5. [Configuration du streaming vidéo](#5-configuration-du-streaming-vidéo)
6. [Enregistrement des problèmes et solutions](#6-enregistrement-des-problèmes-et-solutions)
7. [Résumé des commandes courantes](#7-résumé-des-commandes-courantes)
8. [Annexe](#8-annexe)


## 1. Vue d'ensemble du système

### 1.1 Description du projet

EasyAIoT est une plateforme d'analyse vidéo IoT + IA qui prend en charge la connexion de caméras, la redirection de flux vidéo et l'analyse d'algorithmes IA.

### 1.2 Architecture du système

```
┌─────────────────────────────────────────────────────────────────┐
│                         WEB 前端 (Vue3)                          │
│                         端口: 3100                               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DEVICE 网关 (Spring Cloud)                    │
│                         端口: 48080                              │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  VIDEO 服务   │       │   AI 服务     │       │ DEVICE 微服务 │
│  端口: 6000   │       │  端口: 8100   │       │  多个微服务   │
│  (Python)     │       │  (Python)     │       │  (Java)       │
└───────────────┘       └───────────────┘       └───────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                          中间件层                                │
│  PostgreSQL | Redis | Nacos | MinIO | Kafka | TDengine | SRS   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Description des composants de service

| Service | Pile technologique | Port | Description |
|---------|-------------------|------|-------------|
| WEB | Vue3 + Vite | 3100 | Interface frontend |
| Gateway | Spring Cloud | 48080 | Passerelle API |
| VIDEO | Python Flask | 6000 | Service vidéo |
| AI | Python FastAPI | 8100 | Service d'inférence IA |
| DEVICE | Spring Boot | Plusieurs | Microservices de gestion d'appareils |


## 2. Préparation de l'environnement

### 2.1 Exigences matérielles

- CPU : 4 cœurs ou plus
- Mémoire : 16 Go ou plus (32 Go recommandés)
- Disque dur : 100 Go ou plus d'espace disponible
- Réseau : Réseau local avec accès aux caméras

### 2.2 Dépendances logicielles

#### 2.2.1 JDK 21

Adresse de téléchargement : https://adoptium.net/

Après l'installation, configurez les variables d'environnement :
```
JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-21.0.x
Path 添加: %JAVA_HOME%\bin
```

Vérification de l'installation :
```powershell
java -version
```

#### 2.2.2 Node.js 18+

Adresse de téléchargement : https://nodejs.org/

Vérification de l'installation :
```powershell
node -v
npm -v
```

#### 2.2.3 Python 3.10+ (Anaconda)

Adresse de téléchargement : https://www.anaconda.com/

Création d'un environnement virtuel :
```powershell
conda create -n easyaiot python=3.10
conda activate easyaiot
```

#### 2.2.4 FFmpeg

Adresse de téléchargement : https://www.gyan.dev/ffmpeg/builds/

Téléchargez `ffmpeg-release-essentials.zip`, décompressez-le dans un répertoire spécifié, par exemple :
```
G:\ffmpeg-7.0.2-essentials_build\
```

Vérification de l'installation :
```powershell
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" -version
```

#### 2.2.5 Docker Desktop

Adresse de téléchargement : https://www.docker.com/products/docker-desktop/

Utilisé pour exécuter le serveur de streaming SRS. Docker est uniquement utilisé pour exécuter le serveur de streaming SRS, tous les autres services sont déployés localement sans utiliser Docker.

### 2.3 Planification des chemins du projet

Ce document suppose que le chemin du projet est :
```
F:\EASYLOT\easyaiot-V4.0.0\
```

Chemins d'installation des middleware :
```
F:\EASYLOT\PostgreSQL16\
F:\EASYLOT\Redis\
F:\EASYLOT\nacos\     ####要开启鉴权   自行百度
F:\EASYLOT\minio\  #####项目里边有数据库或者说minio的密码  所有密码都要和项目的配套一至  如minion  账号：minionminion 密码iot******
F:\EASYLOT\kafka\   ###自行下载
F:\EASYLOT\TDengine\  ####自行下载
```


## 3. Déploiement des middleware

### 3.1 PostgreSQL

#### Informations d'installation
- Version : 16.x
- Port : 5432
- Nom d'utilisateur : postgres
- Mot de passe : `iot45722414822`

#### Commandes de démarrage
```powershell
# Démarrer le service PostgreSQL
pg_ctl -D "F:\EASYLOT\PostgreSQL16\data" start

# Ou utiliser le service Windows
net start postgresql-x64-16
```

#### Création de la base de données
```powershell
$env:PGPASSWORD='iot45722414822'
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "CREATE DATABASE \"iot-system\";"
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "CREATE DATABASE \"iot-video20\";"
```

#### Vérification de la connexion
```powershell
$env:PGPASSWORD='iot45722414822'
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "\l"
```


### 3.2 Redis

#### Informations d'installation
- Version : 7.x
- Port : 6379
- Mot de passe : `basiclab@iot975248395`

#### Commande de démarrage
```powershell
cd F:\EASYLOT\Redis
.\redis-server.exe redis.windows.conf
```

#### Vérification de la connexion
```powershell
cd F:\EASYLOT\Redis
.\redis-cli.exe -a "basiclab@iot975248395" ping
# Devrait retourner PONG
```


### 3.3 Nacos

#### Informations d'installation
- Version : 2.x
- Port : 8848
- Nom d'utilisateur : nacos
- Mot de passe : `basiclab@iot78475418754`
- Espace de noms : local

#### Commande de démarrage
```powershell
cd F:\EASYLOT\nacos\bin
.\startup.cmd -m standalone
```

#### Adresse d'accès
```
http://localhost:8848/nacos
```

#### Configuration de l'espace de noms
1. Connectez-vous à la console Nacos
2. Accédez à « Espaces de noms »
3. Créez un espace de noms, définissez l'ID sur `local`


### 3.4 MinIO

#### Informations d'installation
- Version : Dernière version
- Port API : 9000
- Port console : 9001
- Nom d'utilisateur : minioadmin
- Mot de passe : `basiclab@iot975248395`

#### Commande de démarrage
```powershell
cd F:\EASYLOT\minio
.\minio.exe server data --console-address ":9001"
```

#### Adresses d'accès
```
Console : http://localhost:9001
API : http://localhost:9000
```


### 3.5 Kafka

#### Informations d'installation
- Version : 3.x
- Port : 9092
- Port Zookeeper : 2181

#### Commandes de démarrage (nécessite de démarrer Zookeeper en premier)
```powershell
# Terminal 1 : Démarrer Zookeeper
cd F:\EASYLOT\kafka
.\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties

# Terminal 2 : Démarrer Kafka
cd F:\EASYLOT\kafka
.\bin\windows\kafka-server-start.bat .\config\server.properties
```


### 3.6 TDengine

#### Informations d'installation
- Version : 3.x
- Port : 6030 (connexion native), 6041 (REST API)
- Nom d'utilisateur : root
- Mot de passe : taosdata

#### Commande de démarrage
```powershell
# Démarrer le service TDengine
net start taosd

# Ou démarrage manuel
cd F:\EASYLOT\TDengine
.\taosd.exe
```

#### Vérification de la connexion
```powershell
cd F:\EASYLOT\TDengine
.\taos.exe -u root -p taosdata
```


### 3.7 Serveur de streaming SRS (Docker)

#### Informations d'installation
- Version : ossrs/srs:5
- Port RTMP : 1935
- Port HTTP-FLV : 8080
- Port HTTP API : 1985
- Port WebRTC : 8000/udp

#### Création du fichier de configuration

Créez le fichier de configuration `.scripts/srs/conf/simple.conf` dans le répertoire du projet :
```conf
# Configuration simplifiée SRS
listen              1935;
max_connections     1000;
daemon              off;

http_server {
    enabled         on;
    listen          8080;
    dir             ./objs/nginx/html;
}

http_api {
    enabled         on;
    listen          1985;
}

vhost __defaultVhost__ {
    http_remux {
        enabled     on;
        mount       [vhost]/[app]/[stream].flv;
    }
}
```

#### Commande de démarrage
```powershell
docker run -d --name srs-server `
  -p 1935:1935 `
  -p 8080:8080 `
  -p 1985:1985 `
  -p 8000:8000/udp `
  -v "F:\EASYLOT\easyaiot-V4.0.0\.scripts\srs\conf\simple.conf:/usr/local/srs/conf/docker.conf" `
  ossrs/srs:5 ./objs/srs -c conf/docker.conf
```

#### Vérification de l'état d'exécution de SRS
```powershell
# Vérifier l'état du conteneur
docker ps | findstr srs

# Vérifier l'API SRS
Invoke-RestMethod -Uri "http://127.0.0.1:1985/api/v1/versions"
```

#### Commandes Docker courantes
```powershell
# Arrêter SRS
docker stop srs-server

# Démarrer SRS
docker start srs-server

# Voir les journaux
docker logs srs-server

# Supprimer le conteneur (lors de la recréation)
docker rm srs-server
```


## 4. Démarrage des services

### 4.1 Ordre de démarrage

**Doit être démarré dans l'ordre suivant :**

1. Middleware (PostgreSQL → Redis → Nacos → MinIO → Kafka → TDengine → SRS)
2. Microservices DEVICE (Java)
3. Service VIDEO (Python)
4. Service AI (Python)
5. Frontend WEB (Vue)


### 4.2 Démarrage des microservices DEVICE

Il y a plusieurs microservices Spring Boot dans le répertoire DEVICE qui doivent être démarrés séparément.

#### 4.2.1 Démarrer le service de passerelle
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\DEVICE\iot-gateway
mvn spring-boot:run
# Ou utiliser l'IDE pour démarrer
```

#### 4.2.2 Démarrer le service système
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\DEVICE\iot-system\iot-system-biz
mvn spring-boot:run
```

#### 4.2.3 Démarrer le service d'infrastructure
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\DEVICE\iot-infra\iot-infra-biz
mvn spring-boot:run
```

#### Emplacement des fichiers de configuration
- Passerelle : `DEVICE/iot-gateway/src/main/resources/bootstrap-dev.yaml`
- Système : `DEVICE/iot-system/iot-system-biz/src/main/resources/bootstrap-dev.yaml`
- Infrastructure : `DEVICE/iot-infra/iot-infra-biz/src/main/resources/bootstrap-dev.yaml`


### 4.3 Démarrage du service VIDEO

#### 4.3.1 Installation des dépendances
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\VIDEO
conda activate easyaiot
pip install -r requirements.txt
```

#### 4.3.2 Configuration des variables d'environnement

Modifiez le fichier `VIDEO/.env`, assurez-vous que les configurations suivantes sont correctes :
```properties
# Base de données
DATABASE_URL=postgresql://postgres:iot45722414822@localhost:5432/iot-video20

# Nacos
NACOS_SERVER=localhost:8848
NACOS_NAMESPACE=local
NACOS_USERNAME=nacos
NACOS_PASSWORD=basiclab@iot78475418754

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=basiclab@iot975248395

# Chemin FFmpeg (Windows doit configurer le chemin complet)
FFMPEG_PATH=G:/ffmpeg-7.0.2-essentials_build/bin/ffmpeg.exe

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

#### 4.3.3 Démarrer le service
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\VIDEO
conda activate easyaiot
python run.py
```

Le service écoute sur le port : 6000 après le démarrage


### 4.4 Démarrage du service AI

#### 4.4.1 Installation des dépendances
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\AI
conda activate easyaiot
pip install -r requirements.txt
```

#### 4.4.2 Démarrer le service
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\AI
conda activate easyaiot
python run.py
```

Le service écoute sur le port : 8100 après le démarrage


### 4.5 Démarrage du frontend WEB

#### 4.5.1 Installation des dépendances
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\WEB
npm install
# Ou utiliser pnpm
pnpm install
```

#### 4.5.2 Démarrer le serveur de développement
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\WEB
npm run dev
```

Adresse d'accès après le démarrage du service : http://localhost:3100

#### 4.5.3 Informations de connexion
- Nom d'utilisateur : admin
- Mot de passe : admin123


## 5. Configuration du streaming vidéo

### 5.1 Processus de lecture vidéo

```
Caméra(RTSP) → FFmpeg → SRS(RTMP) → HTTP-FLV → Lecteur frontend(flv.js)
```

### 5.2 Ajouter une caméra

1. Connectez-vous au système frontend
2. Accédez à « Streaming » → « Liste des appareils »
3. Cliquez sur « Ajouter un appareil source vidéo »
4. Sélectionnez le type de caméra (Hikvision/Dahua/Uniview/Personnalisé)
5. Remplissez les informations de la caméra :
   - Adresse IP
   - Port (par défaut 554)
   - Nom d'utilisateur
   - Mot de passe
6. Cliquez sur OK, le système générera automatiquement l'adresse RTSP

### 5.3 Démarrer le streaming

1. Trouvez la caméra ajoutée dans la liste des appareils
2. Cliquez sur le bouton « Activer la redirection RTSP »
3. Le système démarrera automatiquement le streaming FFmpeg vers SRS
4. Cliquez sur le bouton « Lecture » pour voir la vidéo

### 5.4 Test manuel du streaming

Si le streaming automatique échoue, vous pouvez tester manuellement :

```powershell
# Commande de test de streaming
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" `
  -re `
  -rtsp_transport tcp `
  -i "rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101" `
  -c:v copy `
  -an `
  -f flv `
  "rtmp://127.0.0.1:1935/live/camera1"
```

### 5.5 Test de lecture

Après un streaming réussi, vous pouvez tester la lecture de la manière suivante :

1. **Lecteur intégré SRS**
   ```
   http://127.0.0.1:8080/players/srs_player.html?autostart=true&stream=live/camera1.flv
   ```

2. **Adresse HTTP-FLV**
   ```
   http://127.0.0.1:8080/live/camera1.flv
   ```

3. **Lecteur VLC**
   - Ouvrez VLC
   - Média → Ouvrir un flux réseau
   - Entrez : `rtmp://127.0.0.1:1935/live/camera1`


## 6. Enregistrement des problèmes et solutions

### 6.1 Limitation de la longueur du nom de flux SRS

#### Description du problème
Lors de l'utilisation de l'ID d'appareil (par exemple `1765004744998329500`) comme nom de flux, FFmpeg signale une erreur :
```
Error opening output rtmp://127.0.0.1:1935/live/1765004744998329500: I/O error
```

Mais l'utilisation d'un nom court (par exemple `camera1`) permet un streaming normal.

#### Solution
Modifiez la logique de génération du nom de flux, utilisez `cam_` + les 8 premiers caractères de l'ID d'appareil :
```python
# VIDEO/app/services/camera_service.py
short_stream_name = f"cam_{device_id[:8]}"
rtmp_stream = f"rtmp://127.0.0.1:1935/live/{short_stream_name}"
http_stream = f"http://127.0.0.1:8080/live/{short_stream_name}.flv"
```

#### Correction manuelle des données existantes
```powershell
$env:PGPASSWORD='iot45722414822'
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20" -c "UPDATE device SET rtmp_stream = 'rtmp://127.0.0.1:1935/live/cam_' || SUBSTRING(id, 1, 8), http_stream = 'http://127.0.0.1:8080/live/cam_' || SUBSTRING(id, 1, 8) || '.flv';"
```


### 6.2 Problème de chemin FFmpeg (Windows)

#### Description du problème
Lors du démarrage du streaming par le service VIDEO, une erreur se produit, la commande `ffmpeg` est introuvable.

#### Analyse de la cause
Dans le système Windows, si FFmpeg n'est pas ajouté au PATH système, il est nécessaire d'utiliser le chemin complet.

#### Solution
1. Configurez le chemin complet de FFmpeg dans `VIDEO/.env` :
   ```properties
   FFMPEG_PATH=G:/ffmpeg-7.0.2-essentials_build/bin/ffmpeg.exe
   ```

2. Modifiez la classe FFmpegDaemon dans `VIDEO/app/blueprints/camera.py` :
   ```python
   ffmpeg_path = os.getenv('FFMPEG_PATH', 'ffmpeg')
   ffmpeg_cmd = [
       ffmpeg_path,
       '-re',
       '-rtsp_transport', 'tcp',
       '-i', self.source,
       '-c:v', 'copy',
       '-an',
       '-f', 'flv',
       self.rtmp_stream
   ]
   ```


### 6.3 Problème de configuration daemon SRS Docker

#### Description du problème
Le conteneur SRS Docker démarre puis se ferme immédiatement.

#### Analyse de la cause
Dans le fichier de configuration SRS, `daemon on;` fait passer SRS en arrière-plan, mais le conteneur Docker nécessite un processus au premier plan.

#### Solution
Dans le fichier de configuration SRS, définissez :
```conf
daemon off;
```


### 6.4 Port 8080 occupé

#### Description du problème
Le port HTTP-FLV SRS 8080 entre en conflit avec d'autres services.

#### Solution
1. Vérifiez le processus qui occupe le port :
   ```powershell
   netstat -ano | findstr :8080
   ```

2. Si le port est occupé par un autre service, vous pouvez modifier la configuration SRS pour utiliser un autre port, ou arrêter le service qui occupe le port.

3. Assurez-vous que la passerelle Java utilise le port 48080, pas 8080.


### 6.5 Problème audio du lecteur flv.js

#### Description du problème
Lors de la lecture vidéo dans le frontend, une erreur se produit ou la vidéo ne peut pas être lue.

#### Analyse de la cause
La caméra peut ne pas avoir de flux audio, mais FFmpeg tente d'encoder l'audio, ce qui provoque une erreur.

#### Solution
1. Désactivez l'audio lors du streaming FFmpeg :
   ```
   -an
   ```

2. Configurez flv.js pour désactiver l'audio :
   ```javascript
   flvPlayer = flvjs.createPlayer({
       type: 'flv',
       url: url,
       isLive: true,
       hasAudio: false,  // Désactiver l'audio
       hasVideo: true,
   });
   ```


### 6.6 Échec de connexion à la base de données

#### Description du problème
Lors du démarrage du service VIDEO, une erreur de connexion à la base de données se produit.

#### Étapes de diagnostic
1. Vérifiez que le service PostgreSQL est démarré :
   ```powershell
   $env:PGPASSWORD='iot45722414822'
   & "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "\l"
   ```

2. Vérifiez que la base de données `iot-video20` existe

3. Vérifiez la configuration DATABASE_URL dans `VIDEO/.env`


### 6.7 Échec d'enregistrement Nacos

#### Description du problème
Le service ne peut pas s'enregistrer dans Nacos au démarrage.

#### Étapes de diagnostic
1. Vérifiez que le service Nacos est démarré :
   ```
   http://localhost:8848/nacos
   ```

2. Vérifiez que l'espace de noms `local` est créé

3. Vérifiez l'adresse et le mot de passe Nacos dans le fichier de configuration


### 6.8 Le code de vérification du frontend ne s'affiche pas

#### Description du problème
L'image du code de vérification sur la page de connexion du frontend ne peut pas être chargée.

#### Analyse de la cause
Cela se produit généralement parce que le service de passerelle n'est pas démarré ou que le port est mal configuré.

#### Solution
1. Vérifiez que le service de passerelle DEVICE est démarré (port 48080)
2. Vérifiez que l'adresse API du frontend est correctement configurée
3. Vérifiez les erreurs de requête réseau dans la console du navigateur


## 7. Résumé des commandes courantes

### 7.1 Opérations sur la base de données

```powershell
# Définir la variable d'environnement du mot de passe
$env:PGPASSWORD='iot45722414822'

# Se connecter à la base de données
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20"

# Voir toutes les bases de données
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "\l"

# Voir la table des appareils
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20" -c "SELECT id, name, source, rtmp_stream, http_stream FROM device;"

# Mettre à jour l'adresse de flux de l'appareil
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20" -c "UPDATE device SET http_stream = 'http://127.0.0.1:8080/live/cam_12345678.flv' WHERE id = '1234567890';"
```

### 7.2 Opérations SRS

```powershell
# Vérifier l'état du conteneur SRS
docker ps | findstr srs

# Voir les journaux SRS
docker logs srs-server

# Redémarrer SRS
docker restart srs-server

# Voir la liste actuelle des streams
Invoke-RestMethod -Uri "http://127.0.0.1:1985/api/v1/streams/" | ConvertTo-Json

# Voir la version SRS
Invoke-RestMethod -Uri "http://127.0.0.1:1985/api/v1/versions"
```

### 7.3 Test de streaming FFmpeg

```powershell
# Test de streaming caméra Hikvision
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" `
  -re `
  -rtsp_transport tcp `
  -i "rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101" `
  -c:v copy `
  -an `
  -f flv `
  "rtmp://127.0.0.1:1935/live/test"

# Test de streaming caméra Dahua
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" `
  -re `
  -rtsp_transport tcp `
  -i "rtsp://admin:password@192.168.1.64:554/cam/realmonitor?channel=1&subtype=0" `
  -c:v copy `
  -an `
  -f flv `
  "rtmp://127.0.0.1:1935/live/test"
```

### 7.4 Démarrage et arrêt des services

```powershell
# Service VIDEO
cd F:\EASYLOT\easyaiot-V4.0.0\VIDEO
conda activate easyaiot
python run.py

# Service AI
cd F:\EASYLOT\easyaiot-V4.0.0\AI
conda activate easyaiot
python run.py

# Frontend WEB
cd F:\EASYLOT\easyaiot-V4.0.0\WEB
npm run dev
```


## 8. Annexe

### 8.1 Tableau récapitulatif des ports

| Service | Port | Protocole | Description |
|---------|------|-----------|-------------|
| PostgreSQL | 5432 | TCP | Base de données |
| Redis | 6379 | TCP | Cache |
| Nacos | 8848 | HTTP | Centre d'enregistrement des services |
| MinIO API | 9000 | HTTP | API de stockage d'objets |
| MinIO Console | 9001 | HTTP | Console de stockage d'objets |
| Kafka | 9092 | TCP | File d'attente de messages |
| Zookeeper | 2181 | TCP | Dépendance Kafka |
| TDengine | 6030 | TCP | Connexion native à la base de données de séries temporelles |
| TDengine REST | 6041 | HTTP | REST API de la base de données de séries temporelles |
| SRS RTMP | 1935 | TCP | Streaming RTMP (push/pull) |
| SRS HTTP-FLV | 8080 | HTTP | Lecture HTTP-FLV |
| SRS API | 1985 | HTTP | API de gestion SRS |
| SRS WebRTC | 8000 | UDP | WebRTC |
| DEVICE Gateway | 48080 | HTTP | Passerelle Java |
| VIDEO | 6000 | HTTP | Service vidéo |
| AI | 8100 | HTTP | Service IA |
| WEB | 3100 | HTTP | Serveur de développement frontend |

### 8.2 Tableau récapitulatif des mots de passe

| Service | Nom d'utilisateur | Mot de passe |
|---------|-------------------|--------------|
| PostgreSQL | postgres | iot45722414822 |
| Redis | - | basiclab@iot975248395 |
| Nacos | nacos | basiclab@iot78475418754 |
| MinIO | minioadmin | basiclab@iot975248395 |
| TDengine | root | taosdata |
| Frontend WEB | admin | admin123 |
| Caméra de test | admin | sr336699 |

### 8.3 Format d'adresse RTSP de la caméra

#### Hikvision
```
rtsp://用户名:密码@IP:554/Streaming/Channels/101  # 主码流
rtsp://用户名:密码@IP:554/Streaming/Channels/102  # 子码流
```

#### Dahua
```
rtsp://用户名:密码@IP:554/cam/realmonitor?channel=1&subtype=0  # 主码流
rtsp://用户名:密码@IP:554/cam/realmonitor?channel=1&subtype=1  # 子码流
```

#### Uniview
```
rtsp://用户名:密码@IP:554/unicast/c1/s0/live  # 主码流
rtsp://用户名:密码@IP:554/unicast/c1/s1/live  # 子码流
```

### 8.4 FAQ - Questions fréquemment posées

**Q : La page frontend ne s'ouvre pas ?**
R : Vérifiez si le service WEB est démarré et si le port 3100 est occupé.

**Q : Une erreur réseau apparaît lors de la connexion ?**
R : Vérifiez si le service de passerelle DEVICE est démarré et si le port 48080 fonctionne normalement.

**Q : La vidéo s'affiche en écran noir ?**
R : 
1. Vérifiez si SRS fonctionne : `docker ps | findstr srs`
2. Vérifiez s'il y a un stream : accédez à `http://127.0.0.1:1985/api/v1/streams/`
3. Vérifiez si la commande de test de streaming manuel fonctionne normalement

**Q : Le streaming échoue ?**
R : 
1. Vérifiez si le chemin FFmpeg est correct
2. Vérifiez si l'adresse RTSP de la caméra est accessible
3. Vérifiez si SRS fonctionne
4. Vérifiez si le nom du stream est trop long

**Q : Échec d'enregistrement du service dans Nacos ?**
R : 
1. Vérifiez si Nacos est démarré
2. Vérifiez si l'espace de noms `local` existe
3. Vérifiez si le mot de passe est correct


> Fin du document
> En cas de problème, contactez l'IA


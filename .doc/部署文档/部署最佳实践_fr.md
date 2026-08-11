# Bonnes pratiques de déploiement EasyAIoT

> Ce document reste synchronisé avec les scripts du projet et couvre le déploiement et l'exploitation en production.  
> Pour un démarrage rapide, consultez le [Guide de déploiement de la plateforme](./平台部署文档_fr.md).

---

## Table des matières

- [Deux modes d'utilisation (détaillé)](#deux-modes-dutilisation-détaillé)
- [Flux de déploiement en 5 minutes](#flux-de-déploiement-en-5-minutes)
- [Sélection du profil de déploiement](#sélection-du-profil-de-déploiement)
- [Exigences d'environnement et vérifications pré-déploiement](#exigences-denvironnement-et-vérifications-pré-déploiement)
- [Déploiement en un clic et étape par étape](#déploiement-en-un-clic-et-étape-par-étape)
- [Mode atomique RUNTIME (nœuds de calcul légers)](#mode-atomique-runtime-nœuds-de-calcul-légers)
- [Opérations courantes](#opérations-courantes)
- [Images préconstruites](#images-préconstruites)
- [Configuration GPU](#configuration-gpu)
- [Environnements spéciaux](#environnements-spéciaux)
- [Notes sur les bases de données](#notes-sur-les-bases-de-données)
- [Identifiants par défaut](#identifiants-par-défaut)
- [Dépannage](#dépannage)
- [Emplacements des journaux](#emplacements-des-journaux)
- [Mise à jour et désinstallation](#mise-à-jour-et-désinstallation)
- [Référence d'architecture](#référence-darchitecture)

---

## Deux modes d'utilisation (détaillé)

Les scripts d'entrée unifiés (`install_linux.sh` / `install_linux_centos.sh` / `install_linux_centos_arm.sh` / `install_linux_openeuler.sh` / `install_linux_arm.sh` / `install_linux_kylin.sh`) prennent en charge **deux modes d'utilisation équivalents** :

| Mode | Entrée | Public cible | Caractéristiques |
|------|--------|--------------|------------------|
| **Interactif** | Sans argument / `menu` / `interactive` | Ops sur site, opérations manuelles | Piloté par menu, étape par étape, retour au menu courant après exécution |
| **Commande directe** | `<command> [args]` | Dev, SRE, CI/CD | Scriptable, reproductible, se termine à la fin de l'exécution |

```bash
# Interactif
sudo .scripts/docker/install_linux.sh

# Commande directe
sudo .scripts/docker/install_linux.sh install
.scripts/docker/install_linux.sh status
```

**Guide de choix :** Privilégiez le mode interactif pour les opérations manuelles ; utilisez les commandes directes pour les scénarios scriptés (Cron / Ansible / CI). **Ne pas** invoquer sans argument dans l'automatisation.

### Interactif : structure des menus

**Menu principal**

```
  1) Deploy — install, start/stop, update, status, logs
  2) Analyze — logs, disk, status diagnostics
  0) Exit
```

**Sous-menu [Deploy]**

| # | Action | Commande équivalente |
|:-:|--------|---------------------|
| 1 | Première installation et démarrage | `install` |
| 2 | Démarrer tous les services | `start` |
| 3 | Arrêter tous les services | `stop` |
| 4 | Redémarrer tous les services | `restart` |
| 5 | Afficher l'état | `status` |
| 6 | Afficher les journaux | `logs` |
| 7 | Vérification de santé | `verify` |
| 8 | Mettre à jour les images et redémarrer | `update` |
| 9 | Vérifier l'environnement Docker | `check` |
| 10 | Afficher le profil de déploiement | `profile` |
| 11 | Aide CLI complète | `help` |

**Sous-menu [Analyze]** — sortie adaptée aux équipes de support

| # | Action | Commande équivalente |
|:-:|--------|---------------------|
| 1 | Fusion multi-modules des journaux | `analyze-logs` |
| 2 | Analyse de l'utilisation disque | `analyze-disk` |
| 3 | État + vérification de santé | `status` + `verify` |
| 4 | Vérification de l'environnement Docker | `check` |

**Menu interne de fusion des journaux** (depuis Analyze → 1) : sélectionnez les sources par numéro (ex. `24,23,27`), `0` = tout pour le profil courant, `b` = retour à [Analyze].

### Commande directe : référence complète

```bash
cd .scripts/docker   # ou utilisez .scripts/docker/install_linux.sh depuis la racine du projet

# Cycle de vie
./install_linux.sh install | start | stop | restart | update | clean

# Observabilité
./install_linux.sh status | logs | logs WEB | verify | check | profile

# Build et images
./install_linux.sh build | pull | build-runtime [module]

# Diagnostics
./install_linux.sh diagnose          # Entrer dans le sous-menu [Analyze] (toujours interactif)
./install_linux.sh analyze-logs      # Fusion des journaux
./install_linux.sh analyze-disk      # Rapport disque

# Aide
./install_linux.sh help | menu
```

### Outils d'analyse : utilisation avancée

Les scripts d'analyse dans `.scripts/docker/` peuvent s'exécuter de manière autonome :

**Fusion multi-modules des journaux `analyze_merge_logs.sh`**

```bash
cd .scripts/docker

# Non interactif (recommandé pour les runbooks)
./analyze_merge_logs.sh --non-interactive \
  --modules dev-iot-sink,dev-iot-message,biz-video --lines 500 --save

# Alias de modules
./analyze_merge_logs.sh --non-interactive --modules DEVICE
./analyze_merge_logs.sh --non-interactive --modules .scripts/docker
./analyze_merge_logs.sh --non-interactive --modules all --save

# ID d'unités courants : mw-nacos / mw-postgres / dev-iot-gateway / dev-iot-sink / biz-ai / biz-video / biz-web
./analyze_merge_logs.sh --help
```

Stratégie de collecte : `docker logs` (N dernières lignes) → fichiers journaux hôte si le conteneur est indisponible → dernière ligne du fichier rotatif le plus récent.

**Utilisation disque `analyze_disk_usage.sh`**

```bash
./analyze_disk_usage.sh                  # Rapport terminal
./analyze_disk_usage.sh --save           # Enregistrer dans logs/disk_usage_*.log
./analyze_disk_usage.sh --top 20
```

Répertoires clés : MinIO `record-space` / `alert-images`, `playbacks` local, zone de transit des images d'alerte.

### Notes d'automatisation

- Cron / Ansible / CI **ne doivent pas** invoquer sans argument (bloque sur le menu)
- Les opérations déclenchées par menu définissent `EASYAIOT_FROM_MENU=1` pour éviter le retour au menu principal après l'installation
- Profil non interactif : `export EASYAIOT_DEPLOY_PROFILE=full`

### Relation avec les scripts par module

Les répertoires de modules (`DEVICE/`, `AI/`, `VIDEO/` …) disposent de leur propre `install_linux.sh` pour ce module uniquement — **sans** menu unifié [Analyze].  
Orchestration complète de la plateforme + guide interactif + analyse inter-modules des journaux/disque → utilisez uniquement `.scripts/docker/install_linux.sh`.

---

## Flux de déploiement en 5 minutes

```bash
git clone https://gitee.com/volara/easyaiot.git && cd easyaiot

docker --version && docker compose version

# Option A : Commande directe
sudo .scripts/docker/install_linux.sh pull    # Optionnel : images préconstruites
sudo .scripts/docker/install_linux.sh install
.scripts/docker/install_linux.sh verify

# Option B : Interactif
sudo .scripts/docker/install_linux.sh         # 1 Deploy → 1 Install → 7 Verify

# Accès : http://<server-ip>:8888
```

### Durée d'installation

| Scénario | Durée |
|----------|-------|
| Images préconstruites téléchargées | 10–30 minutes |
| Build local complet | 30 minutes à plusieurs heures |

---

## Sélection du profil de déploiement

Sélectionné de manière interactive lors du premier `install`, ou via `export EASYAIOT_DEPLOY_PROFILE=mini|standard|full`.  
Enregistré dans `.scripts/docker/.deploy_profile`, réutilisé par `start` / `stop` / `update`.

| Profil | Alias | RAM recommandée | Cas d'usage |
|--------|-------|-----------------|-------------|
| **mini** | `1` / `4g` | ≥ 8 Go | Nœuds edge, PoC |
| **standard** | `2` / `16g` | ≥ 16 Go | Production standard |
| **full** | `3` (par défaut) | ≥ 20 Go | Fonctionnalités complètes + APP H5 |

```bash
.scripts/docker/install_linux.sh profile
```

### Services par profil

**mini**

- Métier : `iot-system`, `iot-gateway`, `iot-sink`, `iot-infra`, VIDEO, AI, WEB
- Middleware : Nacos, PostgreSQL, Redis, Kafka, MinIO, SRS, EMQX
- Non démarrés : `iot-device`, `iot-dataset`, `iot-node`, `iot-visualize`, `iot-file`, `iot-message`, `iot-gb28181`, `iot-tdengine`, Milvus, ZLMediaKit, Node-RED, FUXA, TDengine, APP / VISUALIZE / TRANSFORM, etc.
- Plan événements : identique à standard/full — MQTT → Gateway → iot-sink
- Média : pile NFS préparée à l'installation (`EASYAIOT_MEDIA_ROOT`)
- Routage API : entrée unifiée via Gateway (48080)

**standard**

- Non démarrés : TDengine, Node-RED, `iot-device`, `iot-tdengine`
- Tous les autres démarrés

**full**

- Tous les modules métier et middleware, y compris **APP mobile H5** (9010)

Analyse mémoire :

```bash
.scripts/docker/analyze_deploy_memory.sh
.scripts/docker/analyze_deploy_memory.sh --all-profiles
```

---

## Exigences d'environnement et vérifications pré-déploiement

### Matériel

| Ressource | Minimum | Recommandé |
|-----------|---------|------------|
| CPU | 4 cœurs | 8+ cœurs |
| RAM | Voir les profils (full ≥ 20 Go) | 32 Go+ |
| Disque | **300 Go** libres | 500 Go+ SSD |
| GPU | Aucun (CPU fonctionne) | GPU NVIDIA (CUDA 12.8) |

### Logiciel

| Logiciel | Exigence |
|----------|----------|
| OS | Ubuntu 24.04+ (26.04 recommandé) ; CentOS/RHEL, **Kylin (麒麟) / openEuler (欧拉)**, ARM64 également pris en charge |
| Docker | Installé et démon accessible |
| Docker Compose | **v2.35.0+** (plugin `docker compose`) |
| NVIDIA Driver / Container Toolkit | Scénarios GPU uniquement |

### Permissions Docker

```bash
sudo usermod -aG docker $USER && newgrp docker
docker ps   # doit réussir sans permission denied
```

Utilisez `sudo` lors de la première installation pour la configuration du miroir et des ports RTP.

### Vérifications pré-déploiement

```bash
.scripts/docker/detect_system_info.sh
.scripts/docker/install_linux.sh check
df -h / && docker system df
```

### Exigences de ports

| Port | Service | Notes |
|------|---------|-------|
| 1880 | Node-RED | full/standard |
| 1883 | EMQX | full/standard |
| 1935 | SRS | RTMP |
| 5432 | PostgreSQL | Base de données principale |
| 6000 | VIDEO | Traitement vidéo |
| 6030 | TDengine | full |
| 6080 | ZLMediaKit | Serveur média |
| 6379 | Redis | Cache |
| 8848 | Nacos | Registre/configuration |
| 8888 | WEB | Interface de gestion |
| 9000/9001 | MinIO | Stockage objet |
| 9010 | APP | full uniquement |
| 9092 | Kafka | File de messages |
| 19530 | Milvus | Base vectorielle |
| 48080 | Gateway | Passerelle API |
| 5000 | AI | Service IA |
| 30000-30500 | ZLM RTP | Le script tente la réservation |

```bash
ss -tlnp | grep -E '8848|5432|6379|9092|5000|6000|8888|48080'
```

---

## Déploiement en un clic et étape par étape

### En un clic

```bash
sudo .scripts/docker/install_linux.sh install
.scripts/docker/install_linux.sh verify
```

**Flux automatique `install` :**

1. Sélection du profil → enregistrement dans `.deploy_profile`
2. Détection des images préconstruites (ignore le build local si téléchargées)
3. Vérifications Docker / Compose / création des conteneurs
4. Détection de l'IP hôte (définir `HOST_IP=<ip>` pour forcer)
5. Réservation des ports RTP 30000-30500 (nécessite root)
6. Configuration du miroir Docker (nécessite root)
7. Création de `easyaiot-network`
8. Déploiement dans l'ordre : middleware → DEVICE → AI → VIDEO → WEB → APP (full)
9. Attente de PostgreSQL / Nacos / Redis
10. Mise en place de l'Agent edge si nécessaire

### Étape par étape

Définir d'abord le profil :

```bash
export EASYAIOT_DEPLOY_PROFILE=full
```

**Étape 1 : Middleware**

```bash
cd .scripts/docker && ./install_middleware_linux.sh install
```

| Middleware | Port | Rôle |
|------------|------|------|
| Nacos | 8848 | Registre/configuration |
| PostgreSQL | 5432 | BD principale (6 bases) |
| Redis | 6379 | Cache |
| Kafka | 9092 | File de messages |
| MinIO | 9000/9001 | Stockage objet |
| Milvus | 19530/9091 | Base vectorielle |
| SRS | 1935 | Streaming |
| EMQX | 1883 | MQTT (full/standard) |
| ZLMediaKit | 6080 | Serveur média |
| TDengine | 6030 | BD séries temporelles (full) |
| Node-RED | 1880 | Moteur de règles |

**Étapes 2+ : Modules métier**

```bash
cd DEVICE && ./install_linux.sh install
cd AI    && ./install_linux.sh install
cd VIDEO && ./install_linux.sh install
cd WEB   && ./install_linux.sh install
cd APP   && ./install_linux.sh install   # full uniquement
```

**Modules métier uniquement**

```bash
cd .scripts/docker
./install_business_linux.sh install
./install_business_linux.sh update DEVICE WEB
./install_business_linux.sh verify
```

---

## Mode atomique RUNTIME (nœuds de calcul légers)

Séparez la pile centrale et les nœuds de calcul légers :

| Rôle | Contenu | Entrée |
|------|---------|--------|
| **Centre / tout-en-un** | Middleware + DEVICE/AI/VIDEO/WEB… ; VIDEO monte RUNTIME | `install_linux.sh install` |
| **Nœud de calcul** | **RUNTIME seul** | `VIDEO_BASE_URL=… install_linux.sh runtime` |
| **Lots de nœuds** | Idem via SSH | WEB « distribution runtime » → RUNTIME(C++) |

```bash
VIDEO_BASE_URL=http://<VIDEO-central>:6000 \
  sudo -E bash .scripts/docker/install_linux.sh runtime

./RUNTIME/install_linux.sh status
source /opt/easyaiot/RUNTIME/env.sh
```

`VIDEO_BASE_URL` obligatoire. Atomique ≠ jamais de push. Indépendant des profils mini/standard/full — ne relancez pas `install` complet sur les boîtiers de calcul. Détails : [`RUNTIME/README.md`](../../RUNTIME/README.md).

---

## Opérations courantes

### Script unifié

```bash
./install_linux.sh install | start | stop | restart | status
./install_linux.sh logs | logs WEB | verify | check | profile
./install_linux.sh build | pull | update | clean
./install_linux.sh diagnose | analyze-logs | analyze-disk | help
```

### Scripts par module

Chaque module (`DEVICE` / `AI` / `VIDEO` / `WEB` / `APP`) :

```bash
./install_linux.sh install | start | stop | restart | status | logs | build | clean | update
```

Middleware :

```bash
cd .scripts/docker
./install_middleware_linux.sh install | start | stop | restart | status | logs | build | clean | update
```

### Variables d'environnement

| Variable | Description |
|----------|-------------|
| `EASYAIOT_DEPLOY_PROFILE` | `mini` / `standard` / `full` |
| `HOST_IP` | Forcer l'IP hôte |
| `PARALLEL_MODULES=true` | Démarrage/mise à jour parallèle des modules métier |
| `PARALLEL_BUILD=true` | Build parallèle (séquentiel par défaut pour éviter OOM) |
| `FORCE_NETWORK_RECREATE=true` | Recréer le réseau après changement d'IP |
| `EASYAIOT_RUNTIME_REGISTRY` | Registre d'images préconstruites |

---

## Images préconstruites

Configuration : `.scripts/docker/runtime_registry.conf`

```bash
.scripts/docker/install_linux.sh pull                    # Téléchargement interactif
.scripts/docker/install_linux.sh build-runtime           # Build et push (CI/release)
.scripts/docker/install_linux.sh build-runtime DEVICE    # Module unique
```

Après le téléchargement, `install` / `update` détecte `.runtime_images_pulled` et démarre les conteneurs directement.

---

## Configuration GPU

```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu24.04 nvidia-smi
```

Détection automatique : GPU présent → `runtime: nvidia` ; pas de GPU → mode CPU.

Multi-GPU : `export CUDA_VISIBLE_DEVICES=0,1`

---

## Environnements spéciaux

```bash
# CentOS / RHEL / Rocky / Alma x86 (mise à niveau Docker CE, ports firewalld)
sudo .scripts/docker/install_linux_centos.sh install
# Docker seulement : sudo .scripts/docker/install_linux_centos.sh --upgrade-docker-only

# CentOS / RHEL ARM (puis délégation à install_linux_arm.sh)
sudo .scripts/docker/install_linux_centos_arm.sh install
# Docker seulement : sudo .scripts/docker/install_linux_centos_arm.sh --upgrade-docker-only

# openEuler
sudo .scripts/docker/install_linux_openeuler.sh install
# Docker seulement : sudo .scripts/docker/install_linux_openeuler.sh --upgrade-docker-only

# Kylin OS
sudo .scripts/docker/install_linux_kylin.sh install

# ARM64 (générique)
sudo .scripts/docker/install_linux_arm.sh install

# macOS / Windows
bash .scripts/docker/install_mac.sh install
bash .scripts/docker/install_windows.sh install
```

---

## Notes sur les bases de données

### PostgreSQL (6 bases, scripts dans `.scripts/postgresql/`)

| Base de données | Rôle |
|-----------------|------|
| ruoyi-vue-pro20 | Gestion système |
| iot-ai20 | Service IA |
| iot-device10 | Gestion des appareils |
| iot-gb2818110 | Vidéosurveillance |
| iot-message10 | Messagerie |
| iot-video10 | Traitement vidéo |

### TDengine

SQL dans `.scripts/tdengine/tdengine_super_tables.sql` ; initialisation automatique sous le profil full.

### Sauvegarde

```bash
.scripts/postgresql/backup_databases.sh
```

---

## Identifiants par défaut

| Middleware | Nom d'utilisateur | Mot de passe | Console |
|------------|-------------------|--------------|---------|
| Nacos | nacos | nacos | :8848/nacos |
| PostgreSQL | postgres | iot45722414822 | — |
| Redis | — | basiclab@iot975248395 | — |
| MinIO | minioadmin | basiclab@iot975248395 | :9001 |
| EMQX | admin | basiclab@iot6874125784 | :18083 |
| Milvus | — | — | :9091 |

> **Modifiez tous les mots de passe par défaut en production.**

---

## Dépannage

### Flux recommandé

**Interactif :**

```
No args → 2 Analyze → 4 Docker check → 3 Status+health → 1 Logs → 2 Disk
```

**Commande directe :**

```bash
.scripts/docker/install_linux.sh check
.scripts/docker/install_linux.sh status
.scripts/docker/install_linux.sh verify

cd .scripts/docker
./analyze_disk_usage.sh --save
./analyze_merge_logs.sh --non-interactive --modules dev-iot-sink,biz-video,mw-nacos --lines 500 --save
```

### Problèmes courants

**Échecs de démarrage des services**

```bash
docker ps -a
docker logs -f postgres-server
.scripts/docker/install_linux.sh logs
```

**Réseau (IP hôte modifiée)**

```bash
export FORCE_NETWORK_RECREATE=true
.scripts/docker/install_linux.sh restart
```

**PostgreSQL / Redis**

```bash
.scripts/docker/fix_postgresql.sh
.scripts/docker/fix_redis.sh
```

**Système Docker**

```bash
sudo .scripts/docker/diagnose_docker_systemd.sh diagnose
.scripts/docker/cleanup_docker_space.sh
```

**Groupe de consommateurs Kafka**

```bash
cd VIDEO && ./fix_kafka_consumer_group.sh
```

**WEB après changement de profil**

```bash
cd WEB && ./install_linux.sh build
```

---

## Emplacements des journaux

| Emplacement | Description |
|-------------|-------------|
| `.scripts/docker/logs/` | Journaux du script d'installation ; rapports `merged_logs_*`, `disk_usage_*` |
| `.scripts/docker/standalone-logs/` | Journaux sur disque de Nacos et autres middleware |
| `.build-cache/device/logs/` | Journaux Spring des microservices DEVICE |
| `${EASYAIOT_MEDIA_ROOT:-/mnt/easyaiot-media}/srs.log` | Streaming SRS (racine média résolue par `deploy_profile`) |
| `WEB/logs/runtime.log` | Journal d'exécution WEB |
| `docker logs <container>` | stdout du conteneur (courant pour AI/VIDEO) |

| Besoin | Interactif | Commande directe |
|--------|------------|------------------|
| 500 dernières lignes, multi-services | Analyze → 1 | `analyze-logs` ou `analyze_merge_logs.sh --modules ...` |
| Module unique, suivi en direct | Deploy → 6 | `logs VIDEO` ou `docker compose logs -f` |
| Échec d'installation | — | `tail .scripts/docker/logs/install_linux_*.log` |

---

## Mise à jour et désinstallation

```bash
git pull origin main
sudo .scripts/docker/install_linux.sh update
.scripts/docker/install_linux.sh verify
```

Module unique : `cd AI && ./install_linux.sh update`

Désinstallation :

```bash
sudo .scripts/docker/install_linux.sh clean   # ⚠️ Supprime conteneurs, images, volumes
```

---

## Référence d'architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEB Frontend (:8888)                          │
├─────────────────────────────────────────────────────────────────┤
│                 API Gateway (:48080)                              │
├───────────┬───────────┬───────────┬───────────┬─────────────────┤
│ iot-system│ iot-infra │ iot-device│ iot-dataset│  iot-message   │
│ iot-file  │ iot-sink  │ iot-gb28181                        │
├───────────┴───────────┴───────────┴───────────┴─────────────────┤
│  AI (:5000)              │  VIDEO (:6000)    │  APP H5 (:9010) │
├──────────────────────────┴───────────────────┴─────────────────┤
│  Nacos │ PostgreSQL │ Redis │ Kafka │ MinIO │ TDengine          │
│  Milvus │ SRS │ EMQX │ ZLMediaKit │ Node-RED                     │
└─────────────────────────────────────────────────────────────────┘
```

---

*Version du document : 3.1 | 2026-07-08 | Point d'entrée du script : `.scripts/docker/install_linux.sh` (sans argument=interactif ; `<command>`=direct)*

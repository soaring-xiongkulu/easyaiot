# Guide de déploiement de la plateforme EasyAIoT

> Pour un premier déploiement, consultez [Démarrage rapide](#démarrage-rapide). Pour les opérations avancées, le GPU, les bases de données et le dépannage, voir [Bonnes pratiques de déploiement](./部署最佳实践_fr.md).

---

## Table des matières

- [Aperçu](#aperçu)
- [Deux modes d'utilisation](#deux-modes-dutilisation)
- [Démarrage rapide](#démarrage-rapide)
- [Profils de déploiement](#profils-de-déploiement)
- [Référence des commandes du script](#référence-des-commandes-du-script)
- [Accès aux services et ports](#accès-aux-services-et-ports)
- [FAQ](#faq)
- [Exigences d'environnement](#exigences-denvironnement)

---

## Aperçu

EasyAIoT est déployé via **des conteneurs Docker et un script d'installation unifié**. La plateforme comprend le middleware de base et les modules métier : DEVICE, AI, VIDEO, WEB et APP.

| Module | Répertoire | Description |
|--------|-----------|-------------|
| Services de base | `.scripts/docker` | Nacos, PostgreSQL, Redis, Kafka, MinIO, etc. |
| DEVICE | `DEVICE/` | Gestion des appareils et passerelle API (Java / Spring Cloud) |
| AI | `AI/` | Entraînement et inférence de modèles (Python) |
| VIDEO | `VIDEO/` | Streaming vidéo, alertes, enregistrement (Python) |
| WEB | `WEB/` | Console de gestion (Vue 3) |
| APP | `APP/` | H5 mobile (**profil full** uniquement) |

**Scripts d'entrée unifiés** (exemples Linux x86 ci-dessous) :

| OS | Script |
|----|--------|
| Linux x86 | `.scripts/docker/install_linux.sh` |
| CentOS / RHEL (x86) | `.scripts/docker/install_linux_centos.sh` |
| **CentOS / RHEL · ARM** | `.scripts/docker/install_linux_centos_arm.sh` |
| **Kylin (麒麟)** | `.scripts/docker/install_linux_kylin.sh` |
| **openEuler (欧拉)** | `.scripts/docker/install_linux_openeuler.sh` |
| Linux ARM (générique) | `.scripts/docker/install_linux_arm.sh` |
| macOS | `.scripts/docker/install_mac.sh` |
| Windows | `.scripts/docker/install_windows.ps1` / `install_windows.sh` |

---

## Deux modes d'utilisation

Le script d'entrée unifié prend en charge les modes **guidage interactif** et **commande directe**, avec des capacités sous-jacentes identiques :

| | Interactif | Commande directe |
|---|---|---|
| **Entrée** | Sans argument / `menu` / `interactive` | `<commande> [arguments]` |
| **Cas d'usage** | Premier déploiement, ops sur site, dépannage | Dev, ops scriptées, CI/CD |
| **Opération** | Menu, sélection numérique | Exécution directe de la sous-commande |
| **Après exécution** | Retour au niveau de menu actuel | Sortie à la fin |

```bash
# Interactif
sudo .scripts/docker/install_linux.sh

# Commande directe
sudo .scripts/docker/install_linux.sh install
.scripts/docker/install_linux.sh status
```

**Guide de sélection :**

- Ops manuelles quotidiennes, arguments de commande peu familiers → Interactif
- Opération connue, scripts ou tâches cron → Commande directe (**ne pas** invoquer sans arguments dans Cron/CI — le script bloquera en attente d'entrée)

### Interactif : structure des menus

**Menu racine**

```
  1) Deploy — install, start/stop, update, status, logs
  2) Analyze — log merge, disk usage, health checks
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

**Sous-menu [Analyze]**

| # | Action | Commande équivalente |
|:-:|--------|---------------------|
| 1 | Fusion multi-modules des journaux (~500 lignes par source) | `analyze-logs` |
| 2 | Analyse de l'utilisation disque | `analyze-disk` |
| 3 | État + vérification de santé | `status` + `verify` |
| 4 | Vérification de l'environnement Docker | `check` |

**Parcours typiques :**

| Scénario | Parcours interactif |
|----------|---------------------|
| Premier déploiement | 1 → 1 → 7 |
| Démarrage après redémarrage | 1 → 2 → 7 |
| Collecte de diagnostics | 2 → 3 → 1 → 2 |

---

## Démarrage rapide

### Prérequis

- OS : **Ubuntu 24.04+** (26.04 recommandé) ; également **CentOS/RHEL**, ARM, **Kylin (麒麟) / openEuler (欧拉)**
- Docker + Docker Compose **v2.35+** (sous CentOS / **openEuler (欧拉)** : le script d'entrée OS peut installer/mettre à niveau Docker CE)
- **≥ 300 Go** d'espace disque libre

```bash
docker --version && docker compose version && docker ps
```

### Option 1 : Interactif

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

sudo .scripts/docker/install_linux.sh
# CentOS / RHEL x86 : sudo .scripts/docker/install_linux_centos.sh
# CentOS / RHEL ARM : sudo .scripts/docker/install_linux_centos_arm.sh
# openEuler : sudo .scripts/docker/install_linux_openeuler.sh
# 1 Deploy → 1 First install → 7 Health verify
```

Le profil est sélectionné de manière interactive lors de la première installation. Ouvrez `http://<server-ip>:8888` une fois terminé.

### Option 2 : Commande directe

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

# Optionnel : télécharger les images préconstruites pour raccourcir l'installation
sudo .scripts/docker/install_linux.sh pull
# CentOS x86 : sudo .scripts/docker/install_linux_centos.sh pull
# CentOS ARM : sudo .scripts/docker/install_linux_centos_arm.sh pull
# openEuler : sudo .scripts/docker/install_linux_openeuler.sh pull

sudo .scripts/docker/install_linux.sh install
# CentOS x86 : sudo .scripts/docker/install_linux_centos.sh install
# CentOS ARM : sudo .scripts/docker/install_linux_centos_arm.sh install
# openEuler : sudo .scripts/docker/install_linux_openeuler.sh install

.scripts/docker/install_linux.sh verify
```

### Notes CentOS / RHEL

Utilisez `.scripts/docker/install_linux_centos.sh` (CentOS 7/8/Stream, Rocky, Alma, RHEL · x86). Détails (ZH) : [平台部署文档_zh.md](./平台部署文档_zh.md#centos--rhel-系说明).

### Notes CentOS / RHEL · ARM

Utilisez `.scripts/docker/install_linux_centos_arm.sh` (CentOS/RHEL aarch64/arm64). Même préparation Docker CE / miroir / firewalld, puis délégation à `install_linux_arm.sh`. Détails (ZH) : [平台部署文档_zh.md](./平台部署文档_zh.md#centos--rhel-系--arm-说明).

### Notes **openEuler (欧拉)**

Utilisez `.scripts/docker/install_linux_openeuler.sh` (openEuler 24.03 LTS / 24.x). Remplace le `docker-engine` système, corrige `$releasever` du dépôt Docker CE, configure le miroir et firewalld, puis délègue à `install_linux.sh`. Détails (ZH) : [平台部署文档_zh.md](./平台部署文档_zh.md#openeuler-24x-说明).

### Durée d'installation

| Scénario | Durée estimée |
|----------|---------------|
| Images préconstruites téléchargées | 10–30 minutes |
| Construction locale complète | 30 minutes à plusieurs heures |

Flux `install` : sélection du profil → vérification de l'environnement → création du réseau → déploiement du middleware et des modules → attente de santé. Voir [Déploiement en un clic et étape par étape](./部署最佳实践_fr.md#déploiement-en-un-clic).

---

## Déploiement macOS / Windows (images uniquement)

Les plateformes bureau ne prennent en charge que le déploiement par **images préconstruites** (`install_mac.sh` / `install_windows.ps1` / `install_windows.sh`). Pas de `build` / `build-runtime` local. Détails : [macOS](./平台macOS部署文档_fr.md), [Windows](./平台Windows部署文档_fr.md). Vue d’ensemble (ZH) : [平台部署文档_zh.md](./平台部署文档_zh.md#macos--windows-镜像部署).

```bash
bash .scripts/docker/install_mac.sh install
bash .scripts/docker/install_windows.sh install
```

---

## Profils de déploiement

Sélectionné de manière interactive lors du premier `install`, enregistré dans `.scripts/docker/.deploy_profile`. Réutilisé par les opérations `start` / `stop` / `update` ultérieures.

| Option | Nom | RAM recommandée | Cas d'usage |
|:------:|------|-----------------|-------------|
| 1 | **mini** | ≥ 8 Go | Nœuds edge, PoC |
| 2 | **standard** | ≥ 16 Go | Production courante |
| 3 | **full** (par défaut) | ≥ 20 Go | Fonctionnalités complètes + APP H5 |

```bash
.scripts/docker/install_linux.sh profile                              # Afficher le profil actuel
export EASYAIOT_DEPLOY_PROFILE=full && sudo .../install_linux.sh install  # Mode non interactif
```

Différences de services par profil : [Sélection du profil de déploiement](./部署最佳实践_fr.md#sélection-du-profil-de-déploiement).

---

## Référence des commandes du script

### Commandes

| Commande | Description |
|---------|-------------|
| `install` | Première installation et démarrage |
| `start` / `stop` / `restart` | Contrôle du cycle de vie |
| `status` | Afficher l'état d'exécution |
| `logs [module]` | Afficher les journaux, ex. `logs VIDEO` |
| `verify` | Contrôle de santé |
| `check` | Vérification de l'environnement Docker |
| `update` | Mettre à jour les images et redémarrer |
| `pull` | Télécharger les images préconstruites |
| `build` |
| `runtime` / `runtime-atomic` | **Mode atomique RUNTIME** (exécuteur seul ; `VIDEO_BASE_URL`) |
| `build` | Reconstruire les images localement |
| `profile` | Afficher le profil de déploiement |
| `analyze-logs` | Fusion multi-modules des journaux |
| `analyze-disk` | Analyse de l'utilisation disque |
| `diagnose` | Entrer dans le sous-menu [Analyze] |
| `clean` | Supprimer conteneurs et images ⚠️ (inclut les volumes) |
| `help` | Afficher l'aide |
| `menu` | Ouvrir le guide interactif |

### Collecte de journaux non interactive

```bash
cd .scripts/docker

./analyze_merge_logs.sh --non-interactive \
  --modules dev-iot-sink,dev-iot-message,biz-video --lines 500 --save

./analyze_merge_logs.sh --non-interactive --modules DEVICE --save
./analyze_disk_usage.sh --save --top 15
```

### Correspondance des modes

| Action | Interactif | Commande directe |
|--------|-------------|------------------|
| Première installation | 1 → 1 | `install` |
| Démarrer les services | 1 → 2 | `start` |
| Contrôle de santé | 1 → 7 | `verify` |
| Fusion des journaux | 2 → 1 | `analyze-logs` |
| Analyse disque | 2 → 2 | `analyze-disk` |

### Déploiement par module

```bash
cd .scripts/docker && ./install_middleware_linux.sh install   # Middleware uniquement
cd .scripts/docker && ./install_business_linux.sh install     # Modules métier uniquement
cd AI && ./install_linux.sh install                           # Module unique
```

---

---

## Mode atomique RUNTIME (nœuds de calcul)

Pour **boîtiers edge / workers** : installer **uniquement** l'exécuteur C++ — pas de VIDEO / WEB / DEVICE locaux. Alertes et heartbeats agrégés vers le VIDEO central ; les tâches `realtime` formelles poussent toujours par défaut le flux à cadres vers SRS `ai/`.

> **Atomique ≠ jamais de push.** Atomique = pas de pile métier locale. Détails : [`RUNTIME/README.md`](../../RUNTIME/README.md).

```bash
VIDEO_BASE_URL=http://<VIDEO-central>:6000 \
  bash .scripts/docker/install_linux.sh runtime

VIDEO_BASE_URL=http://192.168.1.10:6000 ./RUNTIME/install_linux.sh atomic
```

| Élément | Notes |
|---------|-------|
| Requis | `VIDEO_BASE_URL` |
| Répertoire | Défaut `/opt/easyaiot/RUNTIME` |
| Sorties | `bin/RUNTIME`, `node.env`, `env.sh`, `config/atomic.example.ini` |
| Tâches formelles | Créer des tâches `executor=cpp` sur le WEB central |
| Smoke | `source /opt/easyaiot/RUNTIME/env.sh && $RUNTIME_BIN …/atomic.example.ini` |

La pile complète du centre utilise toujours `install` ; le montage RUNTIME via VIDEO local est distinct du mode atomique.

---

## Accès aux services et ports

Une fois `verify` réussi :

| Service | URL |
|---------|-----|
| Console WEB | http://\<server-ip\>:8888 |
| Passerelle API | http://\<server-ip\>:48080 |
| Nacos | http://\<server-ip\>:8848/nacos |
| Console MinIO | http://\<server-ip\>:9001 |
| AI | http://\<server-ip\>:5000 |
| VIDEO | http://\<server-ip\>:6000 |
| APP H5 (full) | http://\<server-ip\>:9010 |

| Port | Service |
|------|---------|
| 8888 | WEB |
| 48080 | Gateway |
| 8848 | Nacos |
| 9000/9001 | MinIO |
| 5000 | AI |
| 6000 | VIDEO |
| 9010 | APP (full) |

Liste complète des ports : [Exigences d'environnement et contrôles pré-déploiement](./部署最佳实践_fr.md#exigences-denvironnement).

---

## FAQ

| Symptôme | Résolution |
|---------|------------|
| Docker `permission denied` | `sudo usermod -aG docker $USER && newgrp docker` |
| Version Compose trop ancienne | `sudo apt install -y docker-compose-plugin` |
| Port déjà utilisé | `ss -tlnp \| grep <port>` |
| Échec de l'installation | `tail .scripts/docker/logs/install_linux_*.log` |
| Services démarrés mais inaccessibles | `verify` + vérifier le pare-feu |
| Espace disque insuffisant | `df -h /`, réserver ≥ 300 Go |

**Collecter les diagnostics :**

```bash
# Interactif : 2 Analyze → 1 Logs + 2 Disk
# Commande directe :
.scripts/docker/install_linux.sh check
.scripts/docker/install_linux.sh status
.scripts/docker/install_linux.sh verify
cd .scripts/docker && ./analyze_merge_logs.sh --non-interactive --modules all --save
./analyze_disk_usage.sh --save
```

Plus d'informations : [Dépannage](./部署最佳实践_fr.md#dépannage).

---

## Exigences d'environnement

| Élément | Exigence |
|------|-------------|
| OS | Ubuntu 24.04+ (26.04 recommandé) ; également macOS, Windows, CentOS/RHEL, ARM, **Kylin (麒麟) / openEuler (欧拉)** |
| CPU | Min. 4 cœurs, 8+ recommandés |
| RAM | Dépend du profil (full ≥ 20 Go, 32 Go recommandés) |
| Disque | Min. 300 Go libres, 500 Go+ SSD recommandé |
| GPU | Optionnel ; GPU NVIDIA (CUDA 12.8) pour l'entraînement/inférence IA |
| Docker Compose | v2.35.0+ |

```bash
# Installation Docker (Ubuntu)
curl -fsSL https://get.docker.com | sudo sh
sudo apt install -y docker-compose-plugin
sudo usermod -aG docker $USER && newgrp docker
```

**Remarques :**

1. Utiliser `sudo` lors de la première installation (accélération par miroir et réservation des ports RTP)
2. Modifier les mots de passe middleware par défaut en production ([identifiants](./部署最佳实践_fr.md#identifiants-par-défaut))
3. `clean` supprime les volumes — effectuer une sauvegarde au préalable
4. Reconstruire WEB après changement de profil : `cd WEB && ./install_linux.sh build`

---

**Version du document** : 3.1  
**Dernière mise à jour** : 2026-07-08  
**Point d'entrée du script** : `.scripts/docker/install_linux.sh` (sans argument = interactif ; `<commande>` = direct)

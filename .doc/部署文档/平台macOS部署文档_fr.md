# Guide de déploiement EasyAIoT sur macOS

> Version du document : 1.1  
> Date de mise à jour : 2026-08-01  
> Systèmes pris en charge : macOS (Intel / Apple Silicon)  
> Mode de déploiement : **images préconstruites uniquement** (pas de compilation locale du code métier)

Vue d’ensemble et matrice des commandes : [Guide de déploiement de la plateforme](./平台部署文档_fr.md#déploiement-macos--windows-images-uniquement).  
Compilation de l’installateur PANEL : [COMPILE/README.md](../../COMPILE/README.md).

---

## Table des matières

1. [Vue d’ensemble](#1-vue-densemble)
2. [Préparation de l’environnement](#2-préparation-de-lenvironnement)
3. [Déploiement en un clic](#3-déploiement-en-un-clic)
4. [Commandes courantes](#4-commandes-courantes)
5. [Notes et dépannage](#5-notes-et-dépannage)

---

## 1. Vue d’ensemble

macOS utilise un point d’entrée unique :

```bash
.scripts/docker/install_mac.sh
```

Préférez Homebrew bash 4+ (le `/bin/bash` système est en 3.2) :

```bash
/opt/homebrew/bin/bash .scripts/docker/install_mac.sh <commande>
```

Le script :

1. **Vérifie les prérequis** (Docker Desktop / Compose / bash 4+ / curl) : indique quoi installer si manquant, puis **interrompt**
2. Si besoin, tente `open -a Docker` et attend que le moteur soit prêt
3. **Au besoin**, écrit les `registry-mirrors` (Chine) et ajuste la mémoire du moteur Docker selon le profil
4. Tire les images métier préconstruites selon le profil (mini / standard / full)
5. Tire et démarre les middleware via `install_middleware_desktop.sh` (**FUXA** via `pull_fuxa.sh` dédié)
6. Appelle `install_linux.sh` de chaque module avec `EASYAIOT_SKIP_BUILD=1` pour démarrer uniquement les conteneurs

**Non pris en charge :** `build`, `build-runtime`, `clean-build-runtime`. Les images doivent être construites sur CI/serveurs Linux et poussées vers le registre (voir `runtime_registry.conf`).

---

## 2. Préparation de l’environnement

### 2.1 Matériel et mémoire du moteur Docker

| Profil | Recommandation hôte | Mémoire cible du moteur Docker | Notes |
|--------|---------------------|--------------------------------|-------|
| mini | ≥ 8 Go | **8 Go** | Edge / PoC |
| standard | ≥ 24 Go | **16 Go** | Dev & démos quotidiennes |
| full | ≥ 32 Go (48 Go+ recommandé) | **24 Go** | Fonctionnalités complètes |

Disque : réserver **≥ 100 Go** libres (images et volumes).

> Desktop alloue souvent ~8 Go au moteur ; `resources` / `bootstrap` / `install` augmentent si besoin (écriture de `settings-store.json` Docker Desktop et redémarrage). Surcharge possible : `EASYAIOT_DOCKER_MEMORY_GB` / `EASYAIOT_DOCKER_CPUS` / `EASYAIOT_DOCKER_DISK_GB` ; ignorer avec `EASYAIOT_DOCKER_SKIP_RESOURCES=1`.

### 2.2 Dépendances logicielles

| Dépendance | Notes |
|------------|-------|
| Homebrew | [brew.sh](https://brew.sh) |
| Moteur Docker | Docker Desktop (recommandé) ou Colima (`brew install docker colima`) ; `docker info` doit fonctionner |
| Homebrew bash 4+ | `brew install bash` (le bash système 3.2 ne peut pas exécuter la logique de pull) |
| Git | Cloner le dépôt |
| curl | Contrôles de santé (généralement préinstallé) |
| python3 | Utilisé par `mirrors` / `resources` pour réécrire la config (souvent fourni par macOS / Homebrew) |

### 2.3 Installation des prérequis en un clic (recommandé)

Avant le premier déploiement, installer les dépendances et auto-vérifier :

```bash
bash .scripts/docker/install_mac.sh bootstrap   # Homebrew bash + Docker Desktop (repli Colima) + mirrors/ressources
bash .scripts/docker/install_mac.sh check       # Auto-contrôle des prérequis
bash .scripts/docker/install_mac.sh mirrors     # registry-mirrors Chine (aligné Linux)
bash .scripts/docker/install_mac.sh resources   # Mémoire moteur par profil : mini 8G / standard 16G / full 24G
```

`install` / `pull` / `update` / `start` **exécutent automatiquement** les contrôles préalables ; en cas d’échec, affichage du guide d’installation puis arrêt.

Vérification :

```bash
docker --version
docker compose version
docker info | grep -A5 'Registry Mirrors'
docker info | grep -E 'CPUs|Total Memory'
bash --version   # Préférer ≥ 4 ; chemin Homebrew souvent /opt/homebrew/bin/bash
```

### 2.4 Accélération d’images en Chine (identique à Linux)

Bureau et Linux partagent `DOCKER_MIRROR` / `DOCKER_MIRROR_FALLBACKS` :

| Usage | Comportement |
|-------|--------------|
| Docker Hub / middleware | Écrit `registry-mirrors` dans `~/.docker/daemon.json` : DaoCloud → 1ms → 1panel par défaut |
| **FUXA** | **Exception :** `pull_fuxa.sh` **préfère docker.1ms.run** (DaoCloud renvoie souvent 403 sur `frangoteam/fuxa`) ; compose fixe `docker.1panel.live/frangoteam/fuxa:…` |
| Images métier préconstruites | Depuis `runtime_registry.conf` (ex. `docker.cnb.cool/...`), **non** affectées par `registry-mirrors` |

```bash
# Écriture auto et redémarrage Docker Desktop (aussi via bootstrap / install)
bash .scripts/docker/install_mac.sh mirrors

# Ignorer l’écriture auto des mirrors
EASYAIOT_DOCKER_SKIP_MIRROR=1 bash .scripts/docker/install_mac.sh install
```

Configuration manuelle équivalente (GUI généralement inutile) :

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1ms.run",
    "https://docker.1panel.live"
  ]
}
```

### 2.5 Notes Apple Silicon

Les scripts utilisent la plateforme `linux/arm64` pour les images runtime et Nacos selon `uname -m`. Vérifiez que le registre distant publie ce manifeste ; s’il n’y a que amd64, ajoutez arm64 côté registre, ou utilisez un Mac Intel / Linux distant. Ne forcez pas amd64 pour Nacos (QEMU est extrêmement lent).

### 2.6 Installateur PANEL bureau (optionnel)

Pour un panneau d’ops « double-clic », compilez le paquet macOS en local (icône ronde fond blanc, comme Linux) :

```bash
bash COMPILE/build.sh macos --dmg
# Produit : COMPILE/dist/macos/easyaiot-panel-<version>.dmg
```

Voir [COMPILE/README.md](../../COMPILE/README.md#macos-打包dmg).

---

## 3. Déploiement en un clic

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

# Première fois : dépendances → contrôle → déploiement
bash .scripts/docker/install_mac.sh bootstrap
bash .scripts/docker/install_mac.sh check
EASYAIOT_DEPLOY_PROFILE=full bash .scripts/docker/install_mac.sh install

# Ou assistant interactif
bash .scripts/docker/install_mac.sh

# Vérification
bash .scripts/docker/install_mac.sh verify
```

Profil non interactif :

```bash
export EASYAIOT_DEPLOY_PROFILE=mini   # ou standard / full
bash .scripts/docker/install_mac.sh install
```

Après installation, accéder à :

| Service | Adresse |
|---------|---------|
| WEB | http://localhost:8888 |
| Gateway | http://localhost:48080 |
| Nacos | http://localhost:8848/nacos |
| MinIO | http://localhost:9001 |
| FUXA (full) | http://localhost:1881 |
| PANEL (si activé) | http://localhost:9200 |

---

## 4. Commandes courantes

| Commande | Description |
|----------|-------------|
| `bootstrap` | Installe les prérequis (bash4 + Docker) ; tente mirrors / resources |
| `check` | Auto-contrôle (liste ; conseils d’installation si manquant) |
| `mirrors` | Configure `registry-mirrors` Chine (aligné Linux) |
| `resources` | Ajuste CPU/mémoire/disque Docker par profil (`resources force` pour forcer) |
| `install` | Tire les images et installe/démarre |
| `pull` / `update` | Pull seul / pull dernier et redémarrage |
| `start` / `stop` / `restart` | Cycle de vie |
| `status` / `logs` / `verify` | État, journaux, santé |
| `profile` / `menu` / `help` | Profil, menu interactif, aide |

```bash
bash .scripts/docker/install_mac.sh start
bash .scripts/docker/install_mac.sh stop
bash .scripts/docker/install_mac.sh logs VIDEO
bash .scripts/docker/install_mac.sh update
```

Répertoire des journaux : `.scripts/docker/logs/install_mac_*.log`

---

## 5. Notes et dépannage

| Problème | Action |
|----------|--------|
| bash 4+ requis | `brew install bash`, exécuter avec `/opt/homebrew/bin/bash` ; ou `bootstrap` d’abord |
| Daemon Docker non prêt | Ouvrir Docker Desktop ; attendre que l’icône baleine soit stable |
| Mémoire moteur insuffisante / OOM | `EASYAIOT_DEPLOY_PROFILE=full bash .scripts/docker/install_mac.sh resources` ; ou Desktop → Settings → Resources ≥24 Go |
| Pull middleware échoue | `bash .scripts/docker/install_mac.sh mirrors` puis vérifier Registry Mirrors dans `docker info` ; FUXA → logs `pull_fuxa.sh` |
| Images métier (cnb) échouent | `registry-mirrors` n’agit pas sur `docker.cnb.cool` ; vérifier réseau / proxy / `runtime_registry.conf` |
| Nacos unhealthy longtemps | Confirmer `NACOS_PLATFORM=linux/arm64` ; démarrage à froid peut prendre plusieurs minutes ; `docker logs nacos-server` |
| iot-tdengine Restarting | Assurer que `tdengine-server` est healthy, puis `start` |
| Adresse média / GB28181 anormal | `export HOST_IP=<IP LAN>` puis `start` / `install` à nouveau |
| `build` par erreur | Le bureau refuse ; utiliser `pull` + `install` |
| Répertoires de données SRS | Racine média `EASYAIOT_MEDIA_ROOT` (défaut `/mnt/easyaiot-media` ; fallback bureau `$HOME/easyaiot/media`) |
| Colima et Desktop mélangés | `docker context use desktop-linux` (ou `colima`) ; un seul moteur avant déploiement |

Pour la production et les builds locaux complets, utiliser Linux : `.scripts/docker/install_linux.sh`.

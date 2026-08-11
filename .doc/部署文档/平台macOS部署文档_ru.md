# Руководство по развёртыванию платформы EasyAIoT на macOS

> Версия документа: 1.1  
> Дата обновления: 2026-08-01  
> Поддерживаемые системы: macOS (Intel / Apple Silicon)  
> Способ развёртывания: **только готовые образы** (без локальной сборки бизнес-кода)

Обзор и матрица команд: [Руководство по развёртыванию платформы](./平台部署文档_ru.md#развёртывание-macos--windows-только-образы).  
Сборка десктопного установщика PANEL: [COMPILE/README.md](../../COMPILE/README.md).

---

## Содержание

1. [Обзор](#1-обзор)
2. [Подготовка окружения](#2-подготовка-окружения)
3. [Развёртывание в один клик](#3-развёртывание-в-один-клик)
4. [Часто используемые команды](#4-часто-используемые-команды)
5. [Замечания и устранение неисправностей](#5-замечания-и-устранение-неисправностей)

---

## 1. Обзор

macOS использует единую точку входа:

```bash
.scripts/docker/install_mac.sh
```

Рекомендуется Homebrew bash 4+ (системный `/bin/bash` — 3.2):

```bash
/opt/homebrew/bin/bash .scripts/docker/install_mac.sh <команда>
```

Скрипт:

1. **Проверяет предварительные условия** (Docker Desktop / Compose / bash 4+ / curl): при отсутствии выводит, что установить, и **прерывается**
2. При необходимости запускает `open -a Docker` и ждёт готовности движка
3. **По необходимости** записывает китайские `registry-mirrors` и настраивает память движка Docker под профиль
4. Скачивает готовые бизнес-образы по профилю (mini / standard / full)
5. Через `install_middleware_desktop.sh` скачивает и запускает middleware (**FUXA** — отдельный `pull_fuxa.sh`)
6. Вызывает `install_linux.sh` модулей с `EASYAIOT_SKIP_BUILD=1`, только запуская контейнеры

**Не поддерживается:** `build`, `build-runtime`, `clean-build-runtime`. Образы нужно собирать на Linux CI/серверах и пушить в реестр (см. `runtime_registry.conf`).

---

## 2. Подготовка окружения

### 2.1 Оборудование и память движка Docker

| Профиль | Рекомендация для хоста | Целевая память движка Docker | Примечание |
|---------|------------------------|------------------------------|------------|
| mini | ≥ 8 ГБ | **8 ГБ** | Edge / PoC |
| standard | ≥ 24 ГБ | **16 ГБ** | Ежедневная разработка и демо |
| full | ≥ 32 ГБ (рекомендуется 48 ГБ+) | **24 ГБ** | Полный функционал |

Диск: зарезервируйте **≥ 100 ГБ** свободного места (образы и тома).

> Desktop часто даёт движку ~8 ГБ по умолчанию; `resources` / `bootstrap` / `install` при нехватке повышают значение (запись в `settings-store.json` Docker Desktop и перезапуск движка). Переопределение: `EASYAIOT_DOCKER_MEMORY_GB` / `EASYAIOT_DOCKER_CPUS` / `EASYAIOT_DOCKER_DISK_GB`; пропуск: `EASYAIOT_DOCKER_SKIP_RESOURCES=1`.

### 2.2 Программные зависимости

| Зависимость | Примечание |
|-------------|------------|
| Homebrew | [brew.sh](https://brew.sh) |
| Движок Docker | Docker Desktop (рекомендуется) или Colima (`brew install docker colima`); нужен рабочий `docker info` |
| Homebrew bash 4+ | `brew install bash` (системный bash 3.2 не выполняет логику pull образов) |
| Git | Клонирование репозитория |
| curl | Проверки здоровья (обычно уже есть) |
| python3 | Для перезаписи конфигурации `mirrors` / `resources` (обычно есть в macOS / Homebrew) |

### 2.3 Установка предварительных зависимостей в один клик (рекомендуется)

Перед первым развёртыванием установите зависимости и выполните самопроверку:

```bash
bash .scripts/docker/install_mac.sh bootstrap   # Homebrew bash + Docker Desktop (запасной Colima) + mirrors/ресурсы
bash .scripts/docker/install_mac.sh check       # Самопроверка окружения
bash .scripts/docker/install_mac.sh mirrors     # Китайские registry-mirrors (как на Linux)
bash .scripts/docker/install_mac.sh resources   # Память движка по профилю: mini 8G / standard 16G / full 24G
```

`install` / `pull` / `update` / `start` **автоматически проверяют** предварительные условия; при несоответствии выводят инструкцию по установке и прерываются.

Проверка:

```bash
docker --version
docker compose version
docker info | grep -A5 'Registry Mirrors'
docker info | grep -E 'CPUs|Total Memory'
bash --version   # Желательно ≥ 4; путь Homebrew часто /opt/homebrew/bin/bash
```

### 2.4 Ускорение образов в Китае (как на Linux)

Десктоп и Linux используют общие `DOCKER_MIRROR` / `DOCKER_MIRROR_FALLBACKS`:

| Назначение | Поведение |
|------------|-----------|
| Docker Hub / middleware | Запись `registry-mirrors` в `~/.docker/daemon.json`: по умолчанию DaoCloud → 1ms → 1panel |
| **FUXA** | **Исключение:** `pull_fuxa.sh` **предпочитает docker.1ms.run** (DaoCloud часто отвечает 403 на `frangoteam/fuxa`); в compose зафиксировано `docker.1panel.live/frangoteam/fuxa:…` |
| Готовые бизнес-образы | Из `runtime_registry.conf` (напр. `docker.cnb.cool/...`), **не** зависят от `registry-mirrors` |

```bash
# Автозапись и перезапуск Docker Desktop (также через bootstrap / install)
bash .scripts/docker/install_mac.sh mirrors

# Пропустить автозапись mirrors
EASYAIOT_DOCKER_SKIP_MIRROR=1 bash .scripts/docker/install_mac.sh install
```

Эквивалентная ручная конфигурация (GUI обычно не нужен):

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1ms.run",
    "https://docker.1panel.live"
  ]
}
```

### 2.5 Примечания для Apple Silicon

Скрипты по `uname -m` тянут runtime-образы и Nacos с платформой `linux/arm64`. Убедитесь, что удалённый реестр публикует соответствующий манифест; если есть только amd64 — добавьте arm64 на стороне реестра или используйте Intel Mac / удалённый Linux. Не форсируйте amd64 для Nacos (QEMU крайне медленный).

### 2.6 Десктопный установщик PANEL (опционально)

Для панели эксплуатации «двойной щелчок» соберите пакет macOS локально (круглая иконка на белом фоне, как на Linux):

```bash
bash COMPILE/build.sh macos --dmg
# Результат: COMPILE/dist/macos/easyaiot-panel-<версия>.dmg
```

Подробнее: [COMPILE/README.md](../../COMPILE/README.md#macos-打包dmg).

---

## 3. Развёртывание в один клик

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

# Первый раз: зависимости → проверка → развёртывание
bash .scripts/docker/install_mac.sh bootstrap
bash .scripts/docker/install_mac.sh check
EASYAIOT_DEPLOY_PROFILE=full bash .scripts/docker/install_mac.sh install

# Или интерактивный мастер
bash .scripts/docker/install_mac.sh

# Проверка
bash .scripts/docker/install_mac.sh verify
```

Неинтерактивный выбор профиля:

```bash
export EASYAIOT_DEPLOY_PROFILE=mini   # или standard / full
bash .scripts/docker/install_mac.sh install
```

После установки откройте:

| Сервис | Адрес |
|--------|-------|
| WEB | http://localhost:8888 |
| Gateway | http://localhost:48080 |
| Nacos | http://localhost:8848/nacos |
| MinIO | http://localhost:9001 |
| FUXA (full) | http://localhost:1881 |
| PANEL (если включён) | http://localhost:9200 |

---

## 4. Часто используемые команды

| Команда | Описание |
|---------|----------|
| `bootstrap` | Установка предварительных зависимостей (bash4 + Docker); попытка mirrors / resources |
| `check` | Самопроверка (список; подсказки по установке) |
| `mirrors` | Настройка китайских `registry-mirrors` (как на Linux) |
| `resources` | Настройка CPU/памяти/диска Docker по профилю (`resources force` — принудительная перезапись) |
| `install` | Pull образов и установка/запуск |
| `pull` / `update` | Только pull / pull последнего и перезапуск |
| `start` / `stop` / `restart` | Жизненный цикл |
| `status` / `logs` / `verify` | Статус, логи, проверка здоровья |
| `profile` / `menu` / `help` | Профиль, интерактивное меню, справка |

```bash
bash .scripts/docker/install_mac.sh start
bash .scripts/docker/install_mac.sh stop
bash .scripts/docker/install_mac.sh logs VIDEO
bash .scripts/docker/install_mac.sh update
```

Каталог логов: `.scripts/docker/logs/install_mac_*.log`

---

## 5. Замечания и устранение неисправностей

| Проблема | Действие |
|----------|----------|
| Нужен bash 4+ | `brew install bash`, запуск через `/opt/homebrew/bin/bash`; или сначала `bootstrap` |
| Docker daemon не готов | Откройте Docker Desktop; дождитесь стабильной иконки кита |
| Нехватка памяти движка / OOM | `EASYAIOT_DEPLOY_PROFILE=full bash .scripts/docker/install_mac.sh resources`; или Desktop → Settings → Resources ≥24 ГБ |
| Не тянется middleware | `bash .scripts/docker/install_mac.sh mirrors`, затем проверьте Registry Mirrors в `docker info`; для FUXA — логи `pull_fuxa.sh` |
| Не тянутся бизнес-образы (cnb) | `registry-mirrors` не действует на `docker.cnb.cool`; проверьте сеть / прокси / `runtime_registry.conf` |
| Nacos долго unhealthy | Убедитесь в `NACOS_PLATFORM=linux/arm64`; холодный старт может занять минуты; `docker logs nacos-server` |
| iot-tdengine Restarting | Сначала дождитесь healthy у `tdengine-server`, затем `start` |
| Проблемы медиа / GB28181 | `export HOST_IP=<LAN IP>` и снова `start` / `install` |
| Случайный `build` | Десктоп отклонит; используйте `pull` + `install` |
| Каталоги данных SRS | Корень медиа `EASYAIOT_MEDIA_ROOT` (по умолчанию `/mnt/easyaiot-media`; fallback `$HOME/easyaiot/media`) |
| Смешение Colima и Desktop | `docker context use desktop-linux` (или `colima`); перед развёртыванием оставьте один движок |

Для production и полной локальной сборки используйте Linux: `.scripts/docker/install_linux.sh`.

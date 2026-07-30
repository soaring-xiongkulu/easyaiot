# Руководство по развёртыванию платформы EasyAIoT

> Для первого развёртывания см. [Быстрый старт](#быстрый-старт). Для расширенных операций, GPU, баз данных и устранения неполадок см. [Лучшие практики развёртывания](./部署最佳实践_ru.md).

---

## Содержание

- [Обзор](#обзор)
- [Два режима использования](#два-режима-использования)
- [Быстрый старт](#быстрый-старт)
- [Профили развёртывания](#профили-развёртывания)
- [Справочник команд скрипта](#справочник-команд-скрипта)
- [Доступ к сервисам и порты](#доступ-к-сервисам-и-порты)
- [FAQ](#faq)
- [Требования к окружению](#требования-к-окружению)

---

## Обзор

EasyAIoT развёртывается с помощью **Docker-контейнеров и единого скрипта установки**. Платформа состоит из базового middleware и бизнес-модулей: DEVICE, AI, VIDEO, WEB и APP.

| Модуль | Каталог | Описание |
|--------|-----------|-------------|
| Базовые сервисы | `.scripts/docker` | Nacos, PostgreSQL, Redis, Kafka, MinIO и др. |
| DEVICE | `DEVICE/` | Управление устройствами и API-шлюз (Java / Spring Cloud) |
| AI | `AI/` | Обучение и инференс моделей (Python) |
| VIDEO | `VIDEO/` | Видеопоток, оповещения, запись (Python) |
| WEB | `WEB/` | Консоль управления (Vue 3) |
| APP | `APP/` | Мобильный H5 (**только профиль full**) |

**Единые точки входа скриптов** (примеры для Linux x86 ниже):

| ОС | Скрипт |
|----|--------|
| Linux x86 | `.scripts/docker/install_linux.sh` |
| CentOS / RHEL | `.scripts/docker/install_linux_centos.sh` |
| Linux ARM | `.scripts/docker/install_linux_arm.sh` |
| Kylin | `.scripts/docker/install_linux_kylin.sh` |
| macOS | `.scripts/docker/install_mac.sh` |
| Windows | `.scripts/docker/install_windows.ps1` / `install_windows.sh` |

---

## Два режима использования

Единый скрипт поддерживает режимы **интерактивного руководства** и **прямой команды** с идентичными базовыми возможностями:

| | Интерактивный | Прямая команда |
|---|---|---|
| **Вход** | Без аргументов / `menu` / `interactive` | `<команда> [аргументы]` |
| **Сценарий** | Первое развёртывание, ops на площадке, устранение неполадок | Разработка, скриптовые ops, CI/CD |
| **Операция** | Меню, числовой выбор | Прямое выполнение подкоманды |
| **После выполнения** | Возврат на текущий уровень меню | Завершение по окончании |

```bash
# Интерактивный
sudo .scripts/docker/install_linux.sh

# Прямая команда
sudo .scripts/docker/install_linux.sh install
.scripts/docker/install_linux.sh status
```

**Руководство по выбору:**

- Ежедневные ручные ops, незнакомы аргументы команд → Интерактивный
- Известная операция, скрипты или cron-задачи → Прямая команда (**не** вызывать без аргументов в Cron/CI — скрипт заблокируется в ожидании ввода)

### Интерактивный режим: структура меню

**Корневое меню**

```
  1) Deploy — install, start/stop, update, status, logs
  2) Analyze — log merge, disk usage, health checks
  0) Exit
```

**Подменю [Deploy]**

| # | Действие | Эквивалентная команда |
|:-:|----------|----------------------|
| 1 | Первая установка и запуск | `install` |
| 2 | Запуск всех сервисов | `start` |
| 3 | Остановка всех сервисов | `stop` |
| 4 | Перезапуск всех сервисов | `restart` |
| 5 | Просмотр состояния | `status` |
| 6 | Просмотр логов | `logs` |
| 7 | Проверка работоспособности | `verify` |
| 8 | Обновление образов и перезапуск | `update` |
| 9 | Проверка окружения Docker | `check` |
| 10 | Просмотр профиля развёртывания | `profile` |
| 11 | Полная справка CLI | `help` |

**Подменю [Analyze]**

| # | Действие | Эквивалентная команда |
|:-:|----------|----------------------|
| 1 | Объединение логов нескольких модулей (~500 строк на источник) | `analyze-logs` |
| 2 | Анализ использования диска | `analyze-disk` |
| 3 | Состояние + проверка работоспособности | `status` + `verify` |
| 4 | Проверка окружения Docker | `check` |

**Типичные пути:**

| Сценарий | Интерактивный путь |
|----------|-------------------|
| Первое развёртывание | 1 → 1 → 7 |
| Запуск после перезагрузки | 1 → 2 → 7 |
| Сбор диагностики | 2 → 3 → 1 → 2 |

---

## Быстрый старт

### Предварительные требования

- ОС: **Ubuntu 24.04+** (рекомендуется 26.04); также **CentOS/RHEL**, ARM, Kylin
- Docker + Docker Compose **v2.35+** (на CentOS: `install_linux_centos.sh` может установить/обновить Docker CE)
- **≥ 300 ГБ** свободного места на диске

```bash
docker --version && docker compose version && docker ps
```

### Вариант 1: Интерактивный

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

sudo .scripts/docker/install_linux.sh
# CentOS / RHEL: sudo .scripts/docker/install_linux_centos.sh
# 1 Deploy → 1 First install → 7 Health verify
```

Профиль выбирается интерактивно при первой установке. По завершении откройте `http://<server-ip>:8888`.

### Вариант 2: Прямая команда

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

# Необязательно: загрузить предсобранные образы для сокращения времени установки
sudo .scripts/docker/install_linux.sh pull
# CentOS: sudo .scripts/docker/install_linux_centos.sh pull

sudo .scripts/docker/install_linux.sh install
# CentOS: sudo .scripts/docker/install_linux_centos.sh install

.scripts/docker/install_linux.sh verify
```

### Примечания CentOS / RHEL

Используйте `.scripts/docker/install_linux_centos.sh` (CentOS 7/8/Stream, Rocky, Alma, RHEL). Подробности (ZH): [平台部署文档_zh.md](./平台部署文档_zh.md#centos--rhel-系说明).

### Длительность установки

| Сценарий | Ориентировочное время |
|----------|----------------------|
| Предсобранные образы загружены | 10–30 минут |
| Полная локальная сборка | от 30 минут до нескольких часов |

Процесс `install`: выбор профиля → проверка окружения → создание сети → развёртывание middleware и модулей → ожидание health-check. См. [Развёртывание в один клик и пошаговое](./部署最佳实践_ru.md#развёртывание-в-один-клик).

---

## Развёртывание macOS / Windows (только образы)

Настольные ОС поддерживают только **готовые образы** (`install_mac.sh` / `install_windows.ps1` / `install_windows.sh`). Локальный `build` / `build-runtime` недоступен. Подробности (ZH): [平台部署文档_zh.md](./平台部署文档_zh.md#macos--windows-镜像部署).

```bash
bash .scripts/docker/install_mac.sh install
bash .scripts/docker/install_windows.sh install
```

---

## Профили развёртывания

Выбирается интерактивно при первом `install`, сохраняется в `.scripts/docker/.deploy_profile`. Используется последующими операциями `start` / `stop` / `update`.

| Вариант | Имя | Рекомендуемая RAM | Сценарий |
|:------:|------|-----------------|----------|
| 1 | **mini** | ≥ 4 ГБ | Edge-узлы, PoC |
| 2 | **standard** | ≥ 16 ГБ | Обычная production |
| 3 | **full** (по умолчанию) | ≥ 20 ГБ | Полный функционал + APP H5 |

```bash
.scripts/docker/install_linux.sh profile                              # Просмотр текущего профиля
export EASYAIOT_DEPLOY_PROFILE=full && sudo .../install_linux.sh install  # Неинтерактивный режим
```

Различия сервисов по профилям: [Выбор профиля развёртывания](./部署最佳实践_ru.md#выбор-профиля-развёртывания).

---

## Справочник команд скрипта

### Команды

| Команда | Описание |
|---------|-------------|
| `install` | Первая установка и запуск |
| `start` / `stop` / `restart` | Управление жизненным циклом |
| `status` | Просмотр состояния выполнения |
| `logs [модуль]` | Просмотр логов, напр. `logs VIDEO` |
| `verify` | Проверка работоспособности |
| `check` | Проверка окружения Docker |
| `update` | Обновление образов и перезапуск |
| `pull` | Загрузка предсобранных образов |
| `build` | Локальная пересборка образов |
| `profile` | Просмотр профиля развёртывания |
| `analyze-logs` | Объединение логов нескольких модулей |
| `analyze-disk` | Анализ использования диска |
| `diagnose` | Вход в подменю [Analyze] |
| `clean` | Удаление контейнеров и образов ⚠️ (включая тома) |
| `help` | Показать справку |
| `menu` | Открыть интерактивное руководство |

### Неинтерактивный сбор логов

```bash
cd .scripts/docker

./analyze_merge_logs.sh --non-interactive \
  --modules dev-iot-sink,dev-iot-message,biz-video --lines 500 --save

./analyze_merge_logs.sh --non-interactive --modules DEVICE --save
./analyze_disk_usage.sh --save --top 15
```

### Соответствие режимов

| Действие | Интерактивный | Прямая команда |
|--------|-------------|----------------|
| Первая установка | 1 → 1 | `install` |
| Запуск сервисов | 1 → 2 | `start` |
| Проверка работоспособности | 1 → 7 | `verify` |
| Объединение логов | 2 → 1 | `analyze-logs` |
| Анализ диска | 2 → 2 | `analyze-disk` |

### Развёртывание по модулям

```bash
cd .scripts/docker && ./install_middleware_linux.sh install   # Только middleware
cd .scripts/docker && ./install_business_linux.sh install     # Только бизнес-модули
cd AI && ./install_linux.sh install                           # Один модуль
```

---

## Доступ к сервисам и порты

После успешного `verify`:

| Сервис | URL |
|---------|-----|
| Консоль WEB | http://\<server-ip\>:8888 |
| API Gateway | http://\<server-ip\>:48080 |
| Nacos | http://\<server-ip\>:8848/nacos |
| Консоль MinIO | http://\<server-ip\>:9001 |
| AI | http://\<server-ip\>:5000 |
| VIDEO | http://\<server-ip\>:6000 |
| APP H5 (full) | http://\<server-ip\>:9010 |

| Порт | Сервис |
|------|---------|
| 8888 | WEB |
| 48080 | Gateway |
| 8848 | Nacos |
| 9000/9001 | MinIO |
| 5000 | AI |
| 6000 | VIDEO |
| 9010 | APP (full) |

Полный список портов: [Требования к окружению и проверки перед развёртыванием](./部署最佳实践_ru.md#требования-к-окружению).

---

## FAQ

| Симптом | Решение |
|---------|------------|
| Docker `permission denied` | `sudo usermod -aG docker $USER && newgrp docker` |
| Слишком старая версия Compose | `sudo apt install -y docker-compose-plugin` |
| Порт занят | `ss -tlnp \| grep <port>` |
| Сбой установки | `tail .scripts/docker/logs/install_linux_*.log` |
| Сервисы запущены, но недоступны | `verify` + проверка файрвола |
| Недостаточно места на диске | `df -h /`, зарезервировать ≥ 300 ГБ |

**Сбор диагностики:**

```bash
# Интерактивный: 2 Analyze → 1 Logs + 2 Disk
# Прямая команда:
.scripts/docker/install_linux.sh check
.scripts/docker/install_linux.sh status
.scripts/docker/install_linux.sh verify
cd .scripts/docker && ./analyze_merge_logs.sh --non-interactive --modules all --save
./analyze_disk_usage.sh --save
```

Подробнее: [Устранение неполадок](./部署最佳实践_ru.md#устранение-неполадок).

---

## Требования к окружению

| Параметр | Требование |
|------|-------------|
| ОС | Ubuntu 24.04+ (рекомендуется 26.04); также macOS, Windows, CentOS/RHEL, ARM, Kylin |
| CPU | Мин. 4 ядра, рекомендуется 8+ |
| RAM | Зависит от профиля (full ≥ 20 ГБ, рекомендуется 32 ГБ) |
| Диск | Мин. 300 ГБ свободно, рекомендуется 500 ГБ+ SSD |
| GPU | Необязательно; NVIDIA GPU (CUDA 12.8) для обучения/инференса AI |
| Docker Compose | v2.35.0+ |

```bash
# Установка Docker (Ubuntu)
curl -fsSL https://get.docker.com | sudo sh
sudo apt install -y docker-compose-plugin
sudo usermod -aG docker $USER && newgrp docker
```

**Примечания:**

1. Используйте `sudo` при первой установке (ускорение через зеркало и резервирование RTP-портов)
2. Измените пароли middleware по умолчанию в production ([учётные данные](./部署最佳实践_ru.md#учётные-данные-по-умолчанию))
3. `clean` удаляет тома — сначала выполните резервное копирование
4. Пересоберите WEB после смены профиля: `cd WEB && ./install_linux.sh build`

---

**Версия документа**: 3.1  
**Последнее обновление**: 2026-07-08  
**Точка входа скрипта**: `.scripts/docker/install_linux.sh` (без аргументов = интерактивный; `<команда>` = прямой)

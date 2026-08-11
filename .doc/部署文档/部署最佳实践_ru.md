# Лучшие практики развертывания EasyAIoT

> Этот документ синхронизирован со скриптами проекта и охватывает развертывание и эксплуатацию в production.  
> Для быстрого старта см. [Руководство по развертыванию платформы](./平台部署文档_ru.md).

---

## Содержание

- [Два режима использования (подробно)](#два-режима-использования-подробно)
- [Процесс развертывания за 5 минут](#процесс-развертывания-за-5-минут)
- [Выбор профиля развертывания](#выбор-профиля-развертывания)
- [Требования к окружению и проверки перед развертыванием](#требования-к-окружению-и-проверки-перед-развертыванием)
- [Развертывание в один клик и поэтапное развертывание](#развертывание-в-один-клик-и-поэтапное-развертывание)
- [Атомарный режим RUNTIME (лёгкие вычислительные узлы)](#атомарный-режим-runtime-лёгкие-вычислительные-узлы)
- [Типовые операции](#типовые-операции)
- [Предварительно собранные образы](#предварительно-собранные-образы)
- [Настройка GPU](#настройка-gpu)
- [Особые среды](#особые-среды)
- [Примечания по базам данных](#примечания-по-базам-данных)
- [Учетные данные по умолчанию](#учетные-данные-по-умолчанию)
- [Устранение неполадок](#устранение-неполадок)
- [Расположение журналов](#расположение-журналов)
- [Обновление и удаление](#обновление-и-удаление)
- [Справка по архитектуре](#справка-по-архитектуре)

---

## Два режима использования (подробно)

Единые входные скрипты (`install_linux.sh` / `install_linux_centos.sh` / `install_linux_centos_arm.sh` / `install_linux_openeuler.sh` / `install_linux_arm.sh` / `install_linux_kylin.sh`) поддерживают **два эквивалентных способа использования**:

| Режим | Вход | Аудитория | Характеристики |
|-------|------|-----------|----------------|
| **Интерактивный** | Без аргументов / `menu` / `interactive` | Операции на месте, ручные действия | Управление через меню, пошагово, возврат в текущее меню после выполнения |
| **Прямая команда** | `<command> [args]` | Разработка, SRE, CI/CD | Скриптуемый, повторяемый, завершается по окончании |

```bash
# Интерактивный
sudo .scripts/docker/install_linux.sh

# Прямая команда
sudo .scripts/docker/install_linux.sh install
.scripts/docker/install_linux.sh status
```

**Руководство по выбору:** Для ручных операций предпочитайте интерактивный режим; для сценариев со скриптами (Cron / Ansible / CI) используйте прямые команды. **Не** вызывайте без аргументов в автоматизации.

### Интерактивный: структура меню

**Корневое меню**

```
  1) Deploy — install, start/stop, update, status, logs
  2) Analyze — logs, disk, status diagnostics
  0) Exit
```

**Подменю [Deploy]**

| # | Действие | Эквивалентная команда |
|:-:|----------|----------------------|
| 1 | Первая установка и запуск | `install` |
| 2 | Запустить все сервисы | `start` |
| 3 | Остановить все сервисы | `stop` |
| 4 | Перезапустить все сервисы | `restart` |
| 5 | Просмотр состояния | `status` |
| 6 | Просмотр журналов | `logs` |
| 7 | Проверка работоспособности | `verify` |
| 8 | Обновить образы и перезапустить | `update` |
| 9 | Проверка окружения Docker | `check` |
| 10 | Просмотр профиля развертывания | `profile` |
| 11 | Полная справка CLI | `help` |

**Подменю [Analyze]** — вывод, подходящий для команд поддержки

| # | Действие | Эквивалентная команда |
|:-:|----------|----------------------|
| 1 | Объединение журналов нескольких модулей | `analyze-logs` |
| 2 | Анализ использования диска | `analyze-disk` |
| 3 | Состояние + проверка работоспособности | `status` + `verify` |
| 4 | Проверка окружения Docker | `check` |

**Внутреннее меню объединения журналов** (из Analyze → 1): выберите источники по номеру (напр. `24,23,27`), `0` = все для текущего профиля, `b` = назад в [Analyze].

### Прямая команда: полный справочник

```bash
cd .scripts/docker   # или используйте .scripts/docker/install_linux.sh из корня проекта

# Жизненный цикл
./install_linux.sh install | start | stop | restart | update | clean

# Наблюдаемость
./install_linux.sh status | logs | logs WEB | verify | check | profile

# Сборка и образы
./install_linux.sh build | pull | build-runtime [module]

# Диагностика
./install_linux.sh diagnose          # Вход в подменю [Analyze] (по-прежнему интерактивно)
./install_linux.sh analyze-logs      # Объединение журналов
./install_linux.sh analyze-disk      # Отчет по диску

# Справка
./install_linux.sh help | menu
```

### Инструменты анализа: расширенное использование

Скрипты анализа в `.scripts/docker/` можно запускать автономно:

**Объединение журналов нескольких модулей `analyze_merge_logs.sh`**

```bash
cd .scripts/docker

# Неинтерактивный (рекомендуется для runbook)
./analyze_merge_logs.sh --non-interactive \
  --modules dev-iot-sink,dev-iot-message,biz-video --lines 500 --save

# Псевдонимы модулей
./analyze_merge_logs.sh --non-interactive --modules DEVICE
./analyze_merge_logs.sh --non-interactive --modules .scripts/docker
./analyze_merge_logs.sh --non-interactive --modules all --save

# Распространенные ID юнитов: mw-nacos / mw-postgres / dev-iot-gateway / dev-iot-sink / biz-ai / biz-video / biz-web
./analyze_merge_logs.sh --help
```

Стратегия сбора: `docker logs` (последние N строк) → файлы журналов хоста, если контейнер недоступен → tail последнего ротированного файла.

**Использование диска `analyze_disk_usage.sh`**

```bash
./analyze_disk_usage.sh                  # Отчет в терминале
./analyze_disk_usage.sh --save           # Сохранить в logs/disk_usage_*.log
./analyze_disk_usage.sh --top 20
```

Ключевые каталоги: MinIO `record-space` / `alert-images`, локальный `playbacks`, промежуточное хранение изображений оповещений.

### Примечания по автоматизации

- Cron / Ansible / CI **не должны** вызывать без аргументов (блокируется на меню)
- Операции, запущенные из меню, устанавливают `EASYAIOT_FROM_MENU=1`, чтобы не возвращаться в корневое меню после установки
- Неинтерактивный профиль: `export EASYAIOT_DEPLOY_PROFILE=full`

### Связь со скриптами отдельных модулей

Каталоги модулей (`DEVICE/`, `AI/`, `VIDEO/` …) имеют независимый `install_linux.sh` только для этого модуля — **без** единого меню [Analyze].  
Полная оркестрация платформы + интерактивное руководство + межмодульный анализ журналов/диска → используйте только `.scripts/docker/install_linux.sh`.

---

## Процесс развертывания за 5 минут

```bash
git clone https://gitee.com/volara/easyaiot.git && cd easyaiot

docker --version && docker compose version

# Вариант A: Прямая команда
sudo .scripts/docker/install_linux.sh pull    # Опционально: предсобранные образы
sudo .scripts/docker/install_linux.sh install
.scripts/docker/install_linux.sh verify

# Вариант B: Интерактивный
sudo .scripts/docker/install_linux.sh         # 1 Deploy → 1 Install → 7 Verify

# Доступ: http://<server-ip>:8888
```

### Длительность установки

| Сценарий | Время |
|----------|-------|
| Предсобранные образы загружены | 10–30 минут |
| Полная локальная сборка | от 30 минут до нескольких часов |

---

## Выбор профиля развертывания

Выбирается интерактивно при первом `install` или через `export EASYAIOT_DEPLOY_PROFILE=mini|standard|full`.  
Сохраняется в `.scripts/docker/.deploy_profile`, повторно используется `start` / `stop` / `update`.

| Профиль | Псевдонимы | Рекомендуемая RAM | Сценарий |
|---------|------------|-------------------|----------|
| **mini** | `1` / `4g` | ≥ 8 ГБ | Edge-узлы, PoC |
| **standard** | `2` / `16g` | ≥ 16 ГБ | Обычный production |
| **full** | `3` (по умолчанию) | ≥ 20 ГБ | Полный функционал + APP H5 |

```bash
.scripts/docker/install_linux.sh profile
```

### Сервисы по профилям

**mini**

- Бизнес: `iot-system`, `iot-gateway`, `iot-sink`, `iot-infra`, VIDEO, AI, WEB
- Middleware: Nacos, PostgreSQL, Redis, Kafka, MinIO, SRS, EMQX
- Не запускаются: `iot-device`, `iot-dataset`, `iot-node`, `iot-visualize`, `iot-file`, `iot-message`, `iot-gb28181`, `iot-tdengine`, Milvus, ZLMediaKit, Node-RED, FUXA, TDengine, APP / VISUALIZE / TRANSFORM и др.
- Событийный контур: как standard/full — MQTT → Gateway → iot-sink
- Медиа: NFS-стек готовится при установке (`EASYAIOT_MEDIA_ROOT`)
- Маршрутизация API: единая точка входа Gateway (48080)

**standard**

- Не запускаются: TDengine, Node-RED, `iot-device`, `iot-tdengine`
- Все остальные запускаются

**full**

- Все бизнес-модули и middleware, включая **мобильное APP H5** (9010)

Анализ памяти:

```bash
.scripts/docker/analyze_deploy_memory.sh
.scripts/docker/analyze_deploy_memory.sh --all-profiles
```

---

## Требования к окружению и проверки перед развертыванием

### Оборудование

| Ресурс | Минимум | Рекомендуется |
|--------|---------|---------------|
| CPU | 4 ядра | 8+ ядер |
| RAM | См. профили (full ≥ 20 ГБ) | 32 ГБ+ |
| Диск | **300 ГБ** свободно | 500 ГБ+ SSD |
| GPU | Нет (работает CPU) | NVIDIA GPU (CUDA 12.8) |

### Программное обеспечение

| ПО | Требование |
|----|------------|
| ОС | Ubuntu 24.04+ (рекомендуется 26.04); также поддерживаются CentOS/RHEL, **Kylin (麒麟) / openEuler (欧拉)**, ARM64 |
| Docker | Установлен, демон доступен |
| Docker Compose | **v2.35.0+** (плагин `docker compose`) |
| NVIDIA Driver / Container Toolkit | Только для сценариев с GPU |

### Права Docker

```bash
sudo usermod -aG docker $USER && newgrp docker
docker ps   # должно выполняться без permission denied
```

Используйте `sudo` при первой установке для настройки зеркала и портов RTP.

### Проверки перед развертыванием

```bash
.scripts/docker/detect_system_info.sh
.scripts/docker/install_linux.sh check
df -h / && docker system df
```

### Требования к портам

| Порт | Сервис | Примечания |
|------|--------|------------|
| 1880 | Node-RED | full/standard |
| 1883 | EMQX | full/standard |
| 1935 | SRS | RTMP |
| 5432 | PostgreSQL | Основная база данных |
| 6000 | VIDEO | Обработка видео |
| 6030 | TDengine | full |
| 6080 | ZLMediaKit | Медиасервер |
| 6379 | Redis | Кэш |
| 8848 | Nacos | Реестр/конфигурация |
| 8888 | WEB | Панель управления |
| 9000/9001 | MinIO | Объектное хранилище |
| 9010 | APP | только full |
| 9092 | Kafka | Очередь сообщений |
| 19530 | Milvus | Векторная БД |
| 48080 | Gateway | API-шлюз |
| 5000 | AI | Сервис ИИ |
| 30000-30500 | ZLM RTP | Скрипт пытается зарезервировать |

```bash
ss -tlnp | grep -E '8848|5432|6379|9092|5000|6000|8888|48080'
```

---

## Развертывание в один клик и поэтапное развертывание

### В один клик

```bash
sudo .scripts/docker/install_linux.sh install
.scripts/docker/install_linux.sh verify
```

**Автоматический поток `install`:**

1. Выбор профиля → сохранение в `.deploy_profile`
2. Обнаружение предсобранных образов (пропуск локальной сборки, если загружены)
3. Проверки Docker / Compose / создания контейнеров
4. Определение IP хоста (переопределить: `HOST_IP=<ip>`)
5. Резервирование портов RTP 30000-30500 (требуется root)
6. Настройка зеркала Docker (требуется root)
7. Создание `easyaiot-network`
8. Развертывание по порядку: middleware → DEVICE → AI → VIDEO → WEB → APP (full)
9. Ожидание PostgreSQL / Nacos / Redis
10. Обеспечение edge Agent при необходимости

### Поэтапное

Сначала задайте профиль:

```bash
export EASYAIOT_DEPLOY_PROFILE=full
```

**Шаг 1: Middleware**

```bash
cd .scripts/docker && ./install_middleware_linux.sh install
```

| Middleware | Порт | Назначение |
|------------|------|------------|
| Nacos | 8848 | Реестр/конфигурация |
| PostgreSQL | 5432 | Основная БД (6 баз) |
| Redis | 6379 | Кэш |
| Kafka | 9092 | Очередь сообщений |
| MinIO | 9000/9001 | Объектное хранилище |
| Milvus | 19530/9091 | Векторная БД |
| SRS | 1935 | Стриминг |
| EMQX | 1883 | MQTT (full/standard) |
| ZLMediaKit | 6080 | Медиасервер |
| TDengine | 6030 | БД временных рядов (full) |
| Node-RED | 1880 | Движок правил |

**Шаги 2+: Бизнес-модули**

```bash
cd DEVICE && ./install_linux.sh install
cd AI    && ./install_linux.sh install
cd VIDEO && ./install_linux.sh install
cd WEB   && ./install_linux.sh install
cd APP   && ./install_linux.sh install   # только full
```

**Только бизнес-модули**

```bash
cd .scripts/docker
./install_business_linux.sh install
./install_business_linux.sh update DEVICE WEB
./install_business_linux.sh verify
```

---

## Атомарный режим RUNTIME (лёгкие вычислительные узлы)

Планируйте полный стек центра и лёгкие compute-узлы раздельно:

| Роль | Что ставить | Вход |
|------|-------------|------|
| **Центр / all-in-one** | Middleware + DEVICE/AI/VIDEO/WEB…; VIDEO монтирует RUNTIME | `install_linux.sh install` |
| **Вычислительный узел** | **Только RUNTIME** | `VIDEO_BASE_URL=… install_linux.sh runtime` |
| **Пакет узлов** | То же через SSH | WEB «дистрибуция runtime» → RUNTIME(C++) |

```bash
VIDEO_BASE_URL=http://<центр-VIDEO>:6000 \
  sudo -E bash .scripts/docker/install_linux.sh runtime

./RUNTIME/install_linux.sh status
source /opt/easyaiot/RUNTIME/env.sh
```

Обязателен `VIDEO_BASE_URL`. Атомарный ≠ никогда не пушить. Не связан с профилями mini/standard/full — не запускайте полный `install` на compute-боксах. Подробности: [`RUNTIME/README.md`](../../RUNTIME/README.md).

---

## Типовые операции

### Единый скрипт

```bash
./install_linux.sh install | start | stop | restart | status
./install_linux.sh logs | logs WEB | verify | check | profile
./install_linux.sh build | pull | update | clean
./install_linux.sh diagnose | analyze-logs | analyze-disk | help
```

### Скрипты по модулям

Каждый модуль (`DEVICE` / `AI` / `VIDEO` / `WEB` / `APP`):

```bash
./install_linux.sh install | start | stop | restart | status | logs | build | clean | update
```

Middleware:

```bash
cd .scripts/docker
./install_middleware_linux.sh install | start | stop | restart | status | logs | build | clean | update
```

### Переменные окружения

| Переменная | Описание |
|------------|----------|
| `EASYAIOT_DEPLOY_PROFILE` | `mini` / `standard` / `full` |
| `HOST_IP` | Принудительно задать IP хоста |
| `PARALLEL_MODULES=true` | Параллельный запуск/обновление бизнес-модулей |
| `PARALLEL_BUILD=true` | Параллельная сборка (по умолчанию последовательно, чтобы избежать OOM) |
| `FORCE_NETWORK_RECREATE=true` | Пересоздать сеть после смены IP |
| `EASYAIOT_RUNTIME_REGISTRY` | Реестр предсобранных образов |

---

## Предварительно собранные образы

Конфигурация: `.scripts/docker/runtime_registry.conf`

```bash
.scripts/docker/install_linux.sh pull                    # Интерактивная загрузка
.scripts/docker/install_linux.sh build-runtime           # Сборка и push (CI/release)
.scripts/docker/install_linux.sh build-runtime DEVICE    # Один модуль
```

После загрузки `install` / `update` обнаруживает `.runtime_images_pulled` и запускает контейнеры напрямую.

---

## Настройка GPU

```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu24.04 nvidia-smi
```

Автоопределение: GPU есть → `runtime: nvidia`; GPU нет → режим CPU.

Несколько GPU: `export CUDA_VISIBLE_DEVICES=0,1`

---

## Особые среды

```bash
# CentOS / RHEL / Rocky / Alma x86 (автообновление Docker CE, порты firewalld)
sudo .scripts/docker/install_linux_centos.sh install
# Только Docker: sudo .scripts/docker/install_linux_centos.sh --upgrade-docker-only

# CentOS / RHEL ARM (затем делегирование install_linux_arm.sh)
sudo .scripts/docker/install_linux_centos_arm.sh install
# Только Docker: sudo .scripts/docker/install_linux_centos_arm.sh --upgrade-docker-only

# openEuler
sudo .scripts/docker/install_linux_openeuler.sh install
# Только Docker: sudo .scripts/docker/install_linux_openeuler.sh --upgrade-docker-only

# Kylin OS
sudo .scripts/docker/install_linux_kylin.sh install

# ARM64 (общий)
sudo .scripts/docker/install_linux_arm.sh install

# macOS / Windows
bash .scripts/docker/install_mac.sh install
bash .scripts/docker/install_windows.sh install
```

---

## Примечания по базам данных

### PostgreSQL (6 баз, скрипты в `.scripts/postgresql/`)

| База данных | Назначение |
|-------------|------------|
| ruoyi-vue-pro20 | Управление системой |
| iot-ai20 | Сервис ИИ |
| iot-device10 | Управление устройствами |
| iot-gb2818110 | Видеонаблюдение |
| iot-message10 | Обмен сообщениями |
| iot-video10 | Обработка видео |

### TDengine

SQL в `.scripts/tdengine/tdengine_super_tables.sql`; автоматическая инициализация в профиле full.

### Резервное копирование

```bash
.scripts/postgresql/backup_databases.sh
```

---

## Учетные данные по умолчанию

| Middleware | Имя пользователя | Пароль | Консоль |
|------------|------------------|--------|---------|
| Nacos | nacos | nacos | :8848/nacos |
| PostgreSQL | postgres | iot45722414822 | — |
| Redis | — | basiclab@iot975248395 | — |
| MinIO | minioadmin | basiclab@iot975248395 | :9001 |
| EMQX | admin | basiclab@iot6874125784 | :18083 |
| Milvus | — | — | :9091 |

> **Измените все пароли по умолчанию в production.**

---

## Устранение неполадок

### Рекомендуемый поток

**Интерактивный:**

```
No args → 2 Analyze → 4 Docker check → 3 Status+health → 1 Logs → 2 Disk
```

**Прямая команда:**

```bash
.scripts/docker/install_linux.sh check
.scripts/docker/install_linux.sh status
.scripts/docker/install_linux.sh verify

cd .scripts/docker
./analyze_disk_usage.sh --save
./analyze_merge_logs.sh --non-interactive --modules dev-iot-sink,biz-video,mw-nacos --lines 500 --save
```

### Распространенные проблемы

**Сбои запуска сервисов**

```bash
docker ps -a
docker logs -f postgres-server
.scripts/docker/install_linux.sh logs
```

**Сеть (изменился IP хоста)**

```bash
export FORCE_NETWORK_RECREATE=true
.scripts/docker/install_linux.sh restart
```

**PostgreSQL / Redis**

```bash
.scripts/docker/fix_postgresql.sh
.scripts/docker/fix_redis.sh
```

**Система Docker**

```bash
sudo .scripts/docker/diagnose_docker_systemd.sh diagnose
.scripts/docker/cleanup_docker_space.sh
```

**Группа потребителей Kafka**

```bash
cd VIDEO && ./fix_kafka_consumer_group.sh
```

**WEB после смены профиля**

```bash
cd WEB && ./install_linux.sh build
```

---

## Расположение журналов

| Расположение | Описание |
|--------------|----------|
| `.scripts/docker/logs/` | Журналы скрипта установки; отчеты `merged_logs_*`, `disk_usage_*` |
| `.scripts/docker/standalone-logs/` | Журналы на диске Nacos и другого middleware |
| `.build-cache/device/logs/` | Spring-журналы микросервисов DEVICE |
| `${EASYAIOT_MEDIA_ROOT:-/mnt/easyaiot-media}/srs.log` | Стриминг SRS (корень медиа через `deploy_profile`) |
| `WEB/logs/runtime.log` | Журнал выполнения WEB |
| `docker logs <container>` | stdout контейнера (типично для AI/VIDEO) |

| Потребность | Интерактивный | Прямая команда |
|-------------|---------------|----------------|
| Последние 500 строк, несколько сервисов | Analyze → 1 | `analyze-logs` или `analyze_merge_logs.sh --modules ...` |
| Один модуль, live tail | Deploy → 6 | `logs VIDEO` или `docker compose logs -f` |
| Сбой установки | — | `tail .scripts/docker/logs/install_linux_*.log` |

---

## Обновление и удаление

```bash
git pull origin main
sudo .scripts/docker/install_linux.sh update
.scripts/docker/install_linux.sh verify
```

Один модуль: `cd AI && ./install_linux.sh update`

Удаление:

```bash
sudo .scripts/docker/install_linux.sh clean   # ⚠️ Удаляет контейнеры, образы, тома
```

---

## Справка по архитектуре

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

*Версия документа: 3.1 | 2026-07-08 | Точка входа скрипта: `.scripts/docker/install_linux.sh` (без аргументов=интерактивный; `<command>`=прямой)*

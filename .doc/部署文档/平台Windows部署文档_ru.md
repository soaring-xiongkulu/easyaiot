# Руководство по локальному развертыванию платформы EasyAIoT для Windows

> Версия документа: 1.0
> Дата обновления: 6 декабря 2025 года
> Поддерживаемые системы: Windows 10/11


## Содержание

1. [Обзор системы](#1-обзор-системы)
2. [Подготовка окружения](#2-подготовка-окружения)
3. [Развертывание промежуточного ПО](#3-развертывание-промежуточного-по)
4. [Запуск сервисов](#4-запуск-сервисов)
5. [Конфигурация видеопотока](#5-конфигурация-видеопотока)
6. [Записи о проблемах и решения](#6-записи-о-проблемах-и-решения)
7. [Сводка часто используемых команд](#7-сводка-часто-используемых-команд)
8. [Приложение](#8-приложение)


## 1. Обзор системы

### 1.1 Описание проекта

EasyAIoT — это платформа для анализа видео с использованием IoT и искусственного интеллекта, поддерживающая подключение камер, пересылку видеопотоков и анализ алгоритмов ИИ.

### 1.2 Архитектура системы

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

### 1.3 Описание компонентов сервисов

| Сервис | Технологический стек | Порт | Описание |
|--------|---------------------|------|----------|
| WEB | Vue3 + Vite | 3100 | Интерфейс фронтенда |
| Gateway | Spring Cloud | 48080 | API-шлюз |
| VIDEO | Python Flask | 6000 | Видеосервис |
| AI | Python FastAPI | 8100 | Сервис вывода ИИ |
| DEVICE | Spring Boot | Несколько | Микросервисы управления устройствами |


## 2. Подготовка окружения

### 2.1 Требования к оборудованию

- CPU: 4 ядра и более
- Память: 16 ГБ и более (рекомендуется 32 ГБ)
- Жесткий диск: 100 ГБ и более свободного места
- Сеть: Локальная сеть с доступом к камерам

### 2.2 Программные зависимости

#### 2.2.1 JDK 21

Адрес загрузки: https://adoptium.net/

После установки настройте переменные окружения:
```
JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-21.0.x
Path 添加: %JAVA_HOME%\bin
```

Проверка установки:
```powershell
java -version
```

#### 2.2.2 Node.js 18+

Адрес загрузки: https://nodejs.org/

Проверка установки:
```powershell
node -v
npm -v
```

#### 2.2.3 Python 3.10+ (Anaconda)

Адрес загрузки: https://www.anaconda.com/

Создание виртуального окружения:
```powershell
conda create -n easyaiot python=3.10
conda activate easyaiot
```

#### 2.2.4 FFmpeg

Адрес загрузки: https://www.gyan.dev/ffmpeg/builds/

Скачайте `ffmpeg-release-essentials.zip`, распакуйте в указанную директорию, например:
```
G:\ffmpeg-7.0.2-essentials_build\
```

Проверка установки:
```powershell
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" -version
```

#### 2.2.5 Docker Desktop

Адрес загрузки: https://www.docker.com/products/docker-desktop/

Используется для запуска медиасервера SRS. Docker используется только для запуска медиасервера SRS, все остальные сервисы развертываются локально без использования Docker.

### 2.3 Планирование путей проекта

В этом документе предполагается путь проекта:
```
F:\EASYLOT\easyaiot-V4.0.0\
```

Пути установки промежуточного ПО:
```
F:\EASYLOT\PostgreSQL16\
F:\EASYLOT\Redis\
F:\EASYLOT\nacos\     ####要开启鉴权   自行百度
F:\EASYLOT\minio\  #####项目里边有数据库或者说minio的密码  所有密码都要和项目的配套一至  如minion  账号：minionminion 密码iot******
F:\EASYLOT\kafka\   ###自行下载
F:\EASYLOT\TDengine\  ####自行下载
```


## 3. Развертывание промежуточного ПО

### 3.1 PostgreSQL

#### Информация об установке
- Версия: 16.x
- Порт: 5432
- Имя пользователя: postgres
- Пароль: `iot45722414822`

#### Команды запуска
```powershell
# Запуск службы PostgreSQL
pg_ctl -D "F:\EASYLOT\PostgreSQL16\data" start

# Или использование службы Windows
net start postgresql-x64-16
```

#### Создание базы данных
```powershell
$env:PGPASSWORD='iot45722414822'
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "CREATE DATABASE \"iot-system\";"
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "CREATE DATABASE \"iot-video20\";"
```

#### Проверка подключения
```powershell
$env:PGPASSWORD='iot45722414822'
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "\l"
```


### 3.2 Redis

#### Информация об установке
- Версия: 7.x
- Порт: 6379
- Пароль: `basiclab@iot975248395`

#### Команда запуска
```powershell
cd F:\EASYLOT\Redis
.\redis-server.exe redis.windows.conf
```

#### Проверка подключения
```powershell
cd F:\EASYLOT\Redis
.\redis-cli.exe -a "basiclab@iot975248395" ping
# Должен вернуть PONG
```


### 3.3 Nacos

#### Информация об установке
- Версия: 2.x
- Порт: 8848
- Имя пользователя: nacos
- Пароль: `basiclab@iot78475418754`
- Пространство имен: local

#### Команда запуска
```powershell
cd F:\EASYLOT\nacos\bin
.\startup.cmd -m standalone
```

#### Адрес доступа
```
http://localhost:8848/nacos
```

#### Настройка пространства имен
1. Войдите в консоль Nacos
2. Перейдите в «Пространства имен»
3. Создайте пространство имен, установите ID как `local`


### 3.4 MinIO

#### Информация об установке
- Версия: Последняя версия
- Порт API: 9000
- Порт консоли: 9001
- Имя пользователя: minioadmin
- Пароль: `basiclab@iot975248395`

#### Команда запуска
```powershell
cd F:\EASYLOT\minio
.\minio.exe server data --console-address ":9001"
```

#### Адреса доступа
```
Консоль: http://localhost:9001
API: http://localhost:9000
```


### 3.5 Kafka

#### Информация об установке
- Версия: 3.x
- Порт: 9092
- Порт Zookeeper: 2181

#### Команды запуска (сначала нужно запустить Zookeeper)
```powershell
# Терминал 1: Запуск Zookeeper
cd F:\EASYLOT\kafka
.\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties

# Терминал 2: Запуск Kafka
cd F:\EASYLOT\kafka
.\bin\windows\kafka-server-start.bat .\config\server.properties
```


### 3.6 TDengine

#### Информация об установке
- Версия: 3.x
- Порт: 6030 (нативное подключение), 6041 (REST API)
- Имя пользователя: root
- Пароль: taosdata

#### Команда запуска
```powershell
# Запуск службы TDengine
net start taosd

# Или ручной запуск
cd F:\EASYLOT\TDengine
.\taosd.exe
```

#### Проверка подключения
```powershell
cd F:\EASYLOT\TDengine
.\taos.exe -u root -p taosdata
```


### 3.7 Медиасервер SRS (Docker)

#### Информация об установке
- Версия: ossrs/srs:5
- Порт RTMP: 1935
- Порт HTTP-FLV: 8080
- Порт HTTP API: 1985
- Порт WebRTC: 8000/udp

#### Создание файла конфигурации

Создайте файл конфигурации `.scripts/srs/conf/simple.conf` в директории проекта:
```conf
# Упрощенная конфигурация SRS
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

#### Команда запуска
```powershell
docker run -d --name srs-server `
  -p 1935:1935 `
  -p 8080:8080 `
  -p 1985:1985 `
  -p 8000:8000/udp `
  -v "F:\EASYLOT\easyaiot-V4.0.0\.scripts\srs\conf\simple.conf:/usr/local/srs/conf/docker.conf" `
  ossrs/srs:5 ./objs/srs -c conf/docker.conf
```

#### Проверка состояния работы SRS
```powershell
# Просмотр состояния контейнера
docker ps | findstr srs

# Просмотр API SRS
Invoke-RestMethod -Uri "http://127.0.0.1:1985/api/v1/versions"
```

#### Часто используемые команды Docker
```powershell
# Остановка SRS
docker stop srs-server

# Запуск SRS
docker start srs-server

# Просмотр логов
docker logs srs-server

# Удаление контейнера (при необходимости пересоздания)
docker rm srs-server
```


## 4. Запуск сервисов

### 4.1 Порядок запуска

**Необходимо запускать в следующем порядке:**

1. Промежуточное ПО (PostgreSQL → Redis → Nacos → MinIO → Kafka → TDengine → SRS)
2. Микросервисы DEVICE (Java)
3. Сервис VIDEO (Python)
4. Сервис AI (Python)
5. Фронтенд WEB (Vue)


### 4.2 Запуск микросервисов DEVICE

В директории DEVICE есть несколько микросервисов Spring Boot, которые нужно запускать отдельно.

#### 4.2.1 Запуск сервиса шлюза
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\DEVICE\iot-gateway
mvn spring-boot:run
# Или используйте IDE для запуска
```

#### 4.2.2 Запуск системного сервиса
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\DEVICE\iot-system\iot-system-biz
mvn spring-boot:run
```

#### 4.2.3 Запуск сервиса инфраструктуры
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\DEVICE\iot-infra\iot-infra-biz
mvn spring-boot:run
```

#### Расположение файлов конфигурации
- Шлюз: `DEVICE/iot-gateway/src/main/resources/bootstrap-dev.yaml`
- Система: `DEVICE/iot-system/iot-system-biz/src/main/resources/bootstrap-dev.yaml`
- Инфраструктура: `DEVICE/iot-infra/iot-infra-biz/src/main/resources/bootstrap-dev.yaml`


### 4.3 Запуск сервиса VIDEO

#### 4.3.1 Установка зависимостей
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\VIDEO
conda activate easyaiot
pip install -r requirements.txt
```

#### 4.3.2 Настройка переменных окружения

Отредактируйте файл `VIDEO/.env`, убедитесь, что следующие настройки правильны:
```properties
# База данных
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

# Путь FFmpeg (в Windows необходимо указать полный путь)
FFMPEG_PATH=G:/ffmpeg-7.0.2-essentials_build/bin/ffmpeg.exe

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

#### 4.3.3 Запуск сервиса
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\VIDEO
conda activate easyaiot
python run.py
```

После запуска сервис прослушивает порт: 6000


### 4.4 Запуск сервиса AI

#### 4.4.1 Установка зависимостей
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\AI
conda activate easyaiot
pip install -r requirements.txt
```

#### 4.4.2 Запуск сервиса
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\AI
conda activate easyaiot
python run.py
```

После запуска сервис прослушивает порт: 8100


### 4.5 Запуск фронтенда WEB

#### 4.5.1 Установка зависимостей
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\WEB
npm install
# Или используйте pnpm
pnpm install
```

#### 4.5.2 Запуск сервера разработки
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\WEB
npm run dev
```

Адрес доступа после запуска сервиса: http://localhost:3100

#### 4.5.3 Информация для входа
- Имя пользователя: admin
- Пароль: admin123


## 5. Конфигурация видеопотока

### 5.1 Процесс воспроизведения видео

```
Камера(RTSP) → FFmpeg → SRS(RTMP) → HTTP-FLV → Плеер фронтенда(flv.js)
```

### 5.2 Добавление камеры

1. Войдите в систему фронтенда
2. Перейдите в «Потоковое вещание» → «Список устройств»
3. Нажмите «Добавить устройство видеоисточника»
4. Выберите тип камеры (Hikvision/Dahua/Uniview/Пользовательский)
5. Заполните информацию о камере:
   - IP-адрес
   - Порт (по умолчанию 554)
   - Имя пользователя
   - Пароль
6. Нажмите «ОК», система автоматически сгенерирует адрес RTSP

### 5.3 Запуск потока

1. Найдите добавленную камеру в списке устройств
2. Нажмите кнопку «Включить пересылку RTSP»
3. Система автоматически запустит поток FFmpeg в SRS
4. Нажмите кнопку «Воспроизведение» для просмотра видео

### 5.4 Ручное тестирование потока

Если автоматический поток не работает, можно протестировать вручную:

```powershell
# Команда тестирования потока
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" `
  -re `
  -rtsp_transport tcp `
  -i "rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101" `
  -c:v copy `
  -an `
  -f flv `
  "rtmp://127.0.0.1:1935/live/camera1"
```

### 5.5 Тестирование воспроизведения

После успешного запуска потока можно протестировать воспроизведение следующими способами:

1. **Встроенный плеер SRS**
   ```
   http://127.0.0.1:8080/players/srs_player.html?autostart=true&stream=live/camera1.flv
   ```

2. **Адрес HTTP-FLV**
   ```
   http://127.0.0.1:8080/live/camera1.flv
   ```

3. **Плеер VLC**
   - Откройте VLC
   - Медиа → Открыть сетевой поток
   - Введите: `rtmp://127.0.0.1:1935/live/camera1`


## 6. Записи о проблемах и решения

### 6.1 Ограничение длины имени потока SRS

#### Описание проблемы
При использовании ID устройства (например, `1765004744998329500`) в качестве имени потока FFmpeg выдает ошибку:
```
Error opening output rtmp://127.0.0.1:1935/live/1765004744998329500: I/O error
```

Но при использовании короткого имени (например, `camera1`) поток работает нормально.

#### Решение
Измените логику генерации имени потока, используя `cam_` + первые 8 символов ID устройства:
```python
# VIDEO/app/services/camera_service.py
short_stream_name = f"cam_{device_id[:8]}"
rtmp_stream = f"rtmp://127.0.0.1:1935/live/{short_stream_name}"
http_stream = f"http://127.0.0.1:8080/live/{short_stream_name}.flv"
```

#### Ручное исправление существующих данных
```powershell
$env:PGPASSWORD='iot45722414822'
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20" -c "UPDATE device SET rtmp_stream = 'rtmp://127.0.0.1:1935/live/cam_' || SUBSTRING(id, 1, 8), http_stream = 'http://127.0.0.1:8080/live/cam_' || SUBSTRING(id, 1, 8) || '.flv';"
```


### 6.2 Проблема с путем FFmpeg (Windows)

#### Описание проблемы
При запуске потока сервисом VIDEO возникает ошибка, команда `ffmpeg` не найдена.

#### Анализ причины
В системе Windows, если FFmpeg не добавлен в системный PATH, необходимо использовать полный путь.

#### Решение
1. Настройте полный путь FFmpeg в `VIDEO/.env`:
   ```properties
   FFMPEG_PATH=G:/ffmpeg-7.0.2-essentials_build/bin/ffmpeg.exe
   ```

2. Измените класс FFmpegDaemon в `VIDEO/app/blueprints/camera.py`:
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


### 6.3 Проблема конфигурации daemon в SRS Docker

#### Описание проблемы
Контейнер SRS Docker запускается и сразу же завершается.

#### Анализ причины
В файле конфигурации SRS `daemon on;` приводит к переходу SRS в фоновый режим, но контейнеру Docker нужен процесс переднего плана.

#### Решение
В файле конфигурации SRS установите:
```conf
daemon off;
```


### 6.4 Порт 8080 занят

#### Описание проблемы
Порт HTTP-FLV SRS 8080 конфликтует с другими сервисами.

#### Решение
1. Проверьте процесс, занимающий порт:
   ```powershell
   netstat -ano | findstr :8080
   ```

2. Если порт занят другим сервисом, можно изменить конфигурацию SRS для использования другого порта или остановить занимающий сервис.

3. Убедитесь, что Java-шлюз использует порт 48080, а не 8080.


### 6.5 Проблема со звуком в плеере flv.js

#### Описание проблемы
При воспроизведении видео во фронтенде возникает ошибка или видео не воспроизводится.

#### Анализ причины
Камера может не иметь аудиопотока, но FFmpeg пытается кодировать аудио, что приводит к ошибке.

#### Решение
1. Отключите аудио при потоке FFmpeg:
   ```
   -an
   ```

2. Настройте flv.js для отключения аудио:
   ```javascript
   flvPlayer = flvjs.createPlayer({
       type: 'flv',
       url: url,
       isLive: true,
       hasAudio: false,  // Отключить аудио
       hasVideo: true,
   });
   ```


### 6.6 Ошибка подключения к базе данных

#### Описание проблемы
При запуске сервиса VIDEO возникает ошибка подключения к базе данных.

#### Шаги диагностики
1. Убедитесь, что служба PostgreSQL запущена:
   ```powershell
   $env:PGPASSWORD='iot45722414822'
   & "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "\l"
   ```

2. Убедитесь, что база данных `iot-video20` существует

3. Проверьте настройку DATABASE_URL в `VIDEO/.env`


### 6.7 Ошибка регистрации в Nacos

#### Описание проблемы
Сервис не может зарегистрироваться в Nacos при запуске.

#### Шаги диагностики
1. Убедитесь, что служба Nacos запущена:
   ```
   http://localhost:8848/nacos
   ```

2. Убедитесь, что пространство имен `local` создано

3. Проверьте адрес и пароль Nacos в файле конфигурации


### 6.8 Капча фронтенда не отображается

#### Описание проблемы
Изображение капчи на странице входа фронтенда не загружается.

#### Анализ причины
Обычно это происходит из-за того, что сервис шлюза не запущен или порт настроен неправильно.

#### Решение
1. Убедитесь, что сервис шлюза DEVICE запущен (порт 48080)
2. Убедитесь, что адрес API фронтенда настроен правильно
3. Проверьте ошибки сетевых запросов в консоли браузера


## 7. Сводка часто используемых команд

### 7.1 Операции с базой данных

```powershell
# Установка переменной окружения пароля
$env:PGPASSWORD='iot45722414822'

# Подключение к базе данных
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20"

# Просмотр всех баз данных
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "\l"

# Просмотр таблицы устройств
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20" -c "SELECT id, name, source, rtmp_stream, http_stream FROM device;"

# Обновление адреса потока устройства
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20" -c "UPDATE device SET http_stream = 'http://127.0.0.1:8080/live/cam_12345678.flv' WHERE id = '1234567890';"
```

### 7.2 Операции SRS

```powershell
# Просмотр состояния контейнера SRS
docker ps | findstr srs

# Просмотр логов SRS
docker logs srs-server

# Перезапуск SRS
docker restart srs-server

# Просмотр текущего списка потоков
Invoke-RestMethod -Uri "http://127.0.0.1:1985/api/v1/streams/" | ConvertTo-Json

# Просмотр версии SRS
Invoke-RestMethod -Uri "http://127.0.0.1:1985/api/v1/versions"
```

### 7.3 Тестирование потока FFmpeg

```powershell
# Тестирование потока камеры Hikvision
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" `
  -re `
  -rtsp_transport tcp `
  -i "rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101" `
  -c:v copy `
  -an `
  -f flv `
  "rtmp://127.0.0.1:1935/live/test"

# Тестирование потока камеры Dahua
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" `
  -re `
  -rtsp_transport tcp `
  -i "rtsp://admin:password@192.168.1.64:554/cam/realmonitor?channel=1&subtype=0" `
  -c:v copy `
  -an `
  -f flv `
  "rtmp://127.0.0.1:1935/live/test"
```

### 7.4 Запуск и остановка сервисов

```powershell
# Сервис VIDEO
cd F:\EASYLOT\easyaiot-V4.0.0\VIDEO
conda activate easyaiot
python run.py

# Сервис AI
cd F:\EASYLOT\easyaiot-V4.0.0\AI
conda activate easyaiot
python run.py

# Фронтенд WEB
cd F:\EASYLOT\easyaiot-V4.0.0\WEB
npm run dev
```


## 8. Приложение

### 8.1 Сводная таблица портов

| Сервис | Порт | Протокол | Описание |
|--------|------|----------|----------|
| PostgreSQL | 5432 | TCP | База данных |
| Redis | 6379 | TCP | Кэш |
| Nacos | 8848 | HTTP | Центр регистрации сервисов |
| MinIO API | 9000 | HTTP | API объектного хранилища |
| MinIO Console | 9001 | HTTP | Консоль объектного хранилища |
| Kafka | 9092 | TCP | Очередь сообщений |
| Zookeeper | 2181 | TCP | Зависимость Kafka |
| TDengine | 6030 | TCP | Нативное подключение к базе данных временных рядов |
| TDengine REST | 6041 | HTTP | REST API базы данных временных рядов |
| SRS RTMP | 1935 | TCP | Поток RTMP (отправка/получение) |
| SRS HTTP-FLV | 8080 | HTTP | Воспроизведение HTTP-FLV |
| SRS API | 1985 | HTTP | API управления SRS |
| SRS WebRTC | 8000 | UDP | WebRTC |
| DEVICE Gateway | 48080 | HTTP | Java-шлюз |
| VIDEO | 6000 | HTTP | Видеосервис |
| AI | 8100 | HTTP | Сервис ИИ |
| WEB | 3100 | HTTP | Сервер разработки фронтенда |

### 8.2 Сводная таблица паролей

| Сервис | Имя пользователя | Пароль |
|--------|------------------|--------|
| PostgreSQL | postgres | iot45722414822 |
| Redis | - | basiclab@iot975248395 |
| Nacos | nacos | basiclab@iot78475418754 |
| MinIO | minioadmin | basiclab@iot975248395 |
| TDengine | root | taosdata |
| Фронтенд WEB | admin | admin123 |
| Тестовая камера | admin | sr336699 |

### 8.3 Формат адреса RTSP камеры

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

### 8.4 Часто задаваемые вопросы FAQ

**Q: Страница фронтенда не открывается?**
A: Проверьте, запущен ли сервис WEB, не занят ли порт 3100.

**Q: При входе появляется ошибка сети?**
A: Проверьте, запущен ли сервис шлюза DEVICE, нормально ли работает порт 48080.

**Q: Видео воспроизводится черным экраном?**
A: 
1. Проверьте, работает ли SRS: `docker ps | findstr srs`
2. Проверьте, есть ли поток: откройте `http://127.0.0.1:1985/api/v1/streams/`
3. Проверьте, работает ли команда ручного тестирования потока

**Q: Поток не запускается?**
A: 
1. Проверьте, правильный ли путь FFmpeg
2. Проверьте, доступен ли адрес RTSP камеры
3. Проверьте, работает ли SRS
4. Проверьте, не слишком ли длинное имя потока

**Q: Ошибка регистрации сервиса в Nacos?**
A: 
1. Проверьте, запущен ли Nacos
2. Проверьте, существует ли пространство имен `local`
3. Проверьте, правильный ли пароль


> Конец документа
> При возникновении проблем обратитесь к ИИ


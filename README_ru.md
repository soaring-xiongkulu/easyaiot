# EasyAIoT (Объединённая платформа интеллектуальных алгоритмов «Облако–Край–Устройство»)

[![Gitee star](https://gitee.com/volara/easyaiot/badge/star.svg?theme=gvp)](https://gitee.com/soaring-xiongkulu/easyaiot/stargazers)
[![Gitee fork](https://gitee.com/volara/easyaiot/badge/fork.svg?theme=gvp)](https://gitee.com/soaring-xiongkulu/easyaiot/members)

<p style="font-size: 16px; line-height: 1.8; color: #555; font-weight: 400; margin: 20px 0;">
Я надеюсь, что эта система будет использоваться по всему миру, чтобы сделать ИИ действительно доступным для всех, чтобы каждый мог испытать преимущества ИИ, а не только узкая группа людей.
</p>

<div align="center">
    <img src=".image/logo.png" width="30%" height="30%" alt="EasyAIoT">
</div>

<h4 align="center" style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; padding: 20px; font-weight: bold;">
  <a href="./README.md">English</a>
  <span style="display: flex; align-items: center; color: #666; font-weight: bold;">|</span>
  <a href="./README_zh.md">简体中文</a>
  <span style="display: flex; align-items: center; color: #666; font-weight: bold;">|</span>
  <a href="./README_zh_tw.md">繁體中文</a>
  <span style="display: flex; align-items: center; color: #666; font-weight: bold;">|</span>
  <a href="./README_ru.md">Русский</a>
  <span style="display: flex; align-items: center; color: #666; font-weight: bold;">|</span>
  <a href="./README_fr.md">Français</a>
  <span style="display: flex; align-items: center; color: #666; font-weight: bold;">|</span>
  <a href="./README_ko.md">한국어</a>
</h4>

## 🌐 Официальный сайт

Официальный сайт EasyAIoT: [http://36.111.47.113:8090/](http://36.111.47.113:8090/)

Представляет продукт, возможности, четыре уровня оборудования, загрузки установщиков и вход в документацию — чтобы быстро понять ценность платформы и начать внедрение.

## 📖 О проекте

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
<strong>EasyAIoT</strong> (Easy AI Internet of Things) — это <strong>интеллектуальная платформа алгоритмических приложений с архитектурой «облако — край — устройство»</strong>, ориентированная на глубокое слияние искусственного интеллекта и Интернета вещей: камеры, датчики и периферийные вычислительные ресурсы работают совместно прямо на объекте. От подключения устройств и сбора данных до визуального анализа в реальном времени, интеллектуальной оценки и оркестрации оповещений — весь цикл выполняется в рамках единого программного стека.
</p>

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Многие интеллектуальные IoT-проекты сталкиваются с одной и той же проблемой при внедрении: видеосистемы, платформы устройств и алгоритмические сервисы существуют изолированно — интеграция дорога, эксплуатация фрагментирована, масштабирование затруднено. <strong>EasyAIoT решает это одной платформой</strong> — то же ПО может сначала замкнуть умный контур на <strong>2 ГБ</strong> edge-standalone (edge), сесть на 4–8 ГБ edge-бокс (mini) для точечного интеллекта, заехать на AI-камеры «всё в одном» для покрытия этажа или в корпоративный full-stack апплаенс с управлением IoT, массовым видеодоступом и AI-анализом — без поддержки нескольких версий и повторной интеграции гетерогенных систем.
</p>

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Платформа включает основные модули <strong>WEB, APP, DEVICE, EDGE, SENTINEL, VIDEO, RTC, AI, RUNTIME, VISUALIZE, TRANSFORM, PANEL, IDEA, HARNESS и SITE</strong>, а <strong>COMPILE</strong> отвечает за мультиплатформенную упаковку и поставку (включая Ubuntu / CentOS·RHEL <strong>7–9</strong> (x86 + <strong>CentOS ARM</strong>, пакеты el7/el8/el9) / <strong>Kylin (麒麟) / openEuler (欧拉)</strong> / Windows / macOS / ARM). На стороне возможностей платформа охватывает многопротокольный доступ к камерам GB28181 / ONVIF, <strong>P2P-мост потребительских камер RTC</strong> (на базе go2rtc, охватывает <strong>Tapo, Tuya, Ring, Nest, Xiaomi, Wyze, DoorBird, GoPro и Roborock</strong> — Tapo для магазинов, Tuya для белых брендов, Ring/Nest для зарубежных домофонов, Xiaomi для повторного использования, Wyze для дешёвого масштабирования, DoorBird для переговоров, GoPro для мобильных видов, Roborock для камер пылесосов — подключение в Web одним кликом в единое видео и ИИ-оценку), <strong>доступ к аэровзгляду DJI-дока и дрона</strong>, задачи алгоритмов в реальном времени / снимках / патруле, <strong>нативный высокоскоростной слой исполнения RUNTIME</strong> (скомпилированный бинарник закрывает pull/декодирование, YOLO-инференс, push с рамками и многоканальный сырой forward — ниже CPU/память и стабильнее задержка, чем у интерпретируемых цепочек; один бинарник покрывает realtime / snap / patrol / forward), детекция YOLO и zero-shot авторазметка SAM, распознавание лиц/номеров, оркестрируемая бизнес-постобработка, планирование федеративных вычислительных кластеров, <strong>часовой узлов SENTINEL</strong> (непрерывно выявляет готовность и планируемую бизнес-ёмкость каждого узла, запрашивает дополнение среды при пробелах и назначает работу по реальной способности), и <strong>режим бесконечного федеративного edge-кластера</strong> (обычные платы разработки готовы «из коробки», локальные решения на площадке, оповещения и доказательства автоматически собираются в облако, мощность растёт с бизнесом), плюс жизненный цикл IoT-устройств MQTT / TCP / HTTP / Modbus-TCP / Modbus-RTU / OPC UA, а <strong>EDGE C# среда сбора на периферии</strong> на объекте через подключаемые коллекторы берёт на себя сбор протоколов Modbus RTU/TCP, OPC UA и других, локальное планирование и MQTT-интеграцию cloud-edge, и <strong>визуализационные экраны и Web SCADA</strong>, чтобы данные устройств становились командной обстановкой и возвращались на технологические мнемосхемы; новый <strong>сервис кастомного суждения POST</strong>, который превращает детекции в полевые бизнес-события — меньше ложных тревог, настраиваемые правила, пробный прогон до запуска; и <strong>движок TRANSFORM многонаправленного потока данных</strong> доставляет бизнес-события платформы во внешние MES / ERP / CRM / WMS по контракту — многосторонняя стыковка настраиваема, прослеживаема и переиспользуема; сопутствующая <strong>точка поставки и дежурства PANEL</strong> позволяет в день прибытия установить и сдать комплекс, а дежурство и устранение неисправностей больше не ждут каждый раз удалённых команд разработчиков; плюс <strong>официальный сайт SITE</strong> представляет ценность продукта, четыре уровня оборудования и вход к установщикам — сначала понять, затем скачать и развернуть; а <strong>облачная IDE сообщества IDEA</strong> позволяет контрибьюторам открыть полный репозиторий в браузере, совместно творить с GitHub Copilot, публиковать изменения на хосте и открывать PR — вклад в open source из «сначала настроить среду» становится «открыл и правишь». На стороне пользовательского опыта веб-консоль управления и мобильное App / мини-приложение выровнены по возможностям — центр командования и полевая проверка делят одну бизнес-логику, в любое время и в любом месте; а новые <strong>упаковочные оболочки ANDROID / IOS / HARMONYOS</strong> доставляют этот мобильный опыт установщиками (APK / IPA / HAP) на все массовые ОС телефонов — один фронтенд, сборка одной командой, единое управление версиями.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 16px 0 8px 0;">
<strong>Одной фразой:</strong> EasyAIoT = AI + IoT — соединить всё и одновременно обеспечить интеллектуальное зрение и интеллектуальное управление для всего.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
📄 Для более полного иллюстрированного описания см. <a href=".doc/项目介绍/EasyAIoT项目介绍 V2.0.pptx" style="color: #3498db; text-decoration: none; font-weight: 600;">Презентация проекта EasyAIoT V2.0 (PPT)</a>, а также <a href=".doc/项目介绍/AI视频监控分析平台.pdf" style="color: #3498db; text-decoration: none; font-weight: 600;">Платформа AI-анализа видеонаблюдения (PDF)</a>. Повседневные операции после развёртывания см. в <a href=".doc/操作手册/README.md" style="color: #3498db; text-decoration: none; font-weight: 600;">руководстве по эксплуатации платформы</a>.
</p>

### 🏆 Сертификаты

| | | | |
|:---:|:---:|:---:|:---:|
| <img src=".image/certificates/gitee-oss-award-2025-top1.jpg" width="200" alt="Gitee Annual OSS Award 2025 · Победитель трека «Промышленное ПО» (Top 1)"> | <img src=".image/certificates/gitee-2000-stars.jpg" width="200" alt="Gitee 2000+ звёзд"> | <img src=".image/certificates/gitee-gvp-2025.jpg" width="200" alt="Gitee GVP 2025 · Самый ценный открытый проект"> | <img src=".image/certificates/csdn-blog-expert.jpg" width="200" alt="Эксперт блога CSDN"> |

## 🚀 Быстрый старт

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Открываете README и тихо себе: «А моя железяка это потянет?» — <strong>Потянет. Не паникуйте.</strong>
</p>

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Самый лёгкий уровень, контейнеры съедают около <strong>1 ГБ</strong>. Камеры, анализ в реальном времени, умные оповещения — даже маленькая машина замыкает контур. Сначала старый ноутбук; апгрейд потом, когда втянетесь.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 16px 0 8px 0;">
<strong>Три шага (Linux):</strong>
</p>

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

# Вариант A (рекомендуется)
EASYAIOT_DEPLOY_PROFILE=edge sudo bash .scripts/docker/install_linux.sh install

# Вариант B
# sudo bash .scripts/docker/install_linux.sh edge install
```

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0;">
После установки откройте <code>https://&lt;IP-сервера&gt;:8888</code> — по умолчанию <code>admin</code> / <code>admin123</code>. Проверка:
</p>

```bash
.scripts/docker/install_linux.sh verify
# По желанию: глянуть память относительно бюджета уровня
.scripts/docker/install_linux.sh resources
```

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0;">
Всё зелёное? Готово — проще, чем казалось. Можно раньше взять кофе.
</p>

## 🌟 Размышления о проекте

### 📍 Позиционирование проекта

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT — это интеллектуальная платформа Интернета вещей с архитектурой "Облако-Край-Устройство", ориентированная на глубокую интеграцию ИИ и IoT. Через ключевые возможности, такие как управление алгоритмическими задачами, анализ потоков данных в реальном времени, кластерный вывод моделей и другие, платформа реализует полный замкнутый цикл от подключения устройств до сбора данных, анализа ИИ и интеллектуального принятия решений, по-настоящему воплощая идею "интернета всего" и "интеллектуального управления всем".
</p>

### 🎛️ PANEL: установить и сдать в день прибытия — дежурство без ожидания удалённых разработчиков

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Интеллектуальные IoT-проекты чаще всего спотыкаются на «последней миле»: машина уже на площадке, но <strong>не ставится, не проходит приёмку, а при сбое остаётся только ждать удалённых команд разработчиков</strong> — стоимость присутствия и сроки приёмки держатся на людях. PANEL — <strong>независимая точка поставки и дежурства</strong> для интеграторов и полевой эксплуатации: установка в один клик по уровню, здоровье и зависимости всей машины на виду, старт/стоп сервисов и логи на месте; <strong>ещё до готовности бизнес-консоли можно поднять, удержать и сдать комплекс</strong>, превращая «машина на площадке → платформа доступна → готова к приёмке» из ожидания людей в замкнутый цикл в тот же день.
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Короче цикл приёмки</strong>: На месте выбрать edge / mini / standard / full, установить, видеть прогресс и результат сразу — меньше «застряли на полпути, не зная где»; PoC и серийная поставка быстрее проходят приёмку</li>
  <li><strong>Меньше стоимость присутствия и remote</strong>: Работают ли контейнеры, хватает ли ресурсов, где застряли логи — видно с первого взгляда; перезапуск, очистка кэша и pull образов без охоты по документации и ожидания поддержки разработчиков; дежурные сами закрывают типовые сбои</li>
  <li><strong>Один канон на многие проекты</strong>: Одна и та же точка установки и ops переиспользуется на комплексах и в залах — поставка, дежурство и передача в одном стандарте, без «у каждой площадки своя устная традиция»</li>
</ul>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0 8px 0;">
📦 <strong>Скачать установщики</strong>: Пакеты для Ubuntu / Debian, CentOS / RHEL <strong>7–9</strong> (x86 + <strong>CentOS ARM</strong>, RPM el7/el8/el9), Windows, macOS и ARM / <strong>Kylin (麒麟) / openEuler (欧拉)</strong> — на <a href="https://gitee.com/volara/easyaiot/releases" style="color: #3498db; text-decoration: none; font-weight: 600;">Gitee Releases</a>.
</p>

| | | |
|:---:|:---:|:---:|
| ![Обзор](.image/banner/panel/panel_1000.png) | ![Контейнеры](.image/banner/panel/panel_1001.png) | ![Логи](.image/banner/panel/panel_1002.png) |
| ![Развёртывание](.image/banner/panel/panel_1003.png) | ![Готовность образов](.image/banner/panel/panel_1004.png) | ![Pull образов](.image/banner/panel/panel_1005.png) |
| ![Диагностика](.image/banner/panel/panel_1006.png) | ![Обслуживание](.image/banner/panel/panel_1007.png) | ![Топология](.image/banner/panel/panel_1008.png) |

### 📡 RTC: P2P-мост потребительских камер — устройства «без RTSP» в платформе

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Дома, в магазинах и лёгкой охране уже используются устройства <strong>Tapo, Tuya, Ring, Nest, Xiaomi, Wyze, DoorBird, GoPro и Roborock</strong> — они работают по частным P2P-протоколам и <strong>не предоставляют стандартный RTSP</strong>. Традиционные VMS часто отправляют к Micam, Home Assistant и другим прослойкам. EasyAIoT добавляет модуль <strong>RTC</strong> на базе <a href="https://github.com/AlexxIT/go2rtc" style="color: #3498db; text-decoration: none; font-weight: 600;">go2rtc</a>, которая <strong>объединяет поток и двустороннее аудио для всех девяти брендов</strong> — регистрация, просмотр, ретрансляция, ИИ-задачи и оповещения как у GB28181/ONVIF.
</p>

<table style="width: 100%; border-collapse: collapse; margin: 12px 0 20px; font-size: 14px;">
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; width: 14%;">Бренд</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; width: 18%;">Производитель</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; width: 28%;">Типичные устройства</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600;">Ценность</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Tapo</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">TP-Link</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Домашние/магазинные IPC</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Недорогое заполнение слепых зон; двустороннее аудио</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Tuya</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">Tuya Smart</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">IPC экосистемы Tuya</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Массовое подключение white-label/OEM</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Ring</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">Amazon</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Домофоны, уличные камеры</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Зарубежный мониторинг домофонов</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Nest</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">Google</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Nest Cam, Doorbell</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Премиум-объекты Google-экосистемы</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Xiaomi</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">Mi Home</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Камеры Mi Home</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Повторное использование установленного парка</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Wyze</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">Wyze</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Wyze Cam v3/v4</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Сверхдешёвое масштабирование</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>DoorBird</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">DoorBird</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Умные домофоны</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Премиум-переговоры у входа</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>GoPro</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">GoPro</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">HERO9–12</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Мобильные тактические виды</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Roborock</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">Roborock</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Пылесосы с камерами</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Подвижные виды под мебелью</td></tr>
</table>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Подключение в Web одним кликом</strong>: «Подключить RTC-камеру» с динамическими формами по брендам</li>
  <li><strong>Полная цепочка</strong>: WEB → VIDEO <code>/register/device/rtc-live</code> → RTC API → go2rtc P2P → RTSP → SRS → Jessibuca + ИИ</li>
  <li><strong>Двустороннее аудио</strong>: Tapo, Tuya, Ring, Wyze, DoorBird, Roborock</li>
  <li><strong>Синхронизация жизненного цикла</strong>: удаление устройства очищает потоки go2rtc</li>
  <li><strong>Docker all-in-one</strong>: <code>bash RTC/install_linux.sh start</code> запускает go2rtc + сервис управления; host network для P2P LAN</li>
</ul>

### 🔌 EDGE: C# среда сбора на периферии — «точный сбор на объекте, надёжная передача в облако»

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
На промышленных и зданийных площадках ПЛК, счётчики и датчики часто висят на RS-485 или Ethernet, а облачной платформе всё равно нужен отдельный стек сбора данных — протоколы пишутся разово, каждое изменение конфигурации требует выезда на объект. Длинные цепочки доступа, фрагментированная эксплуатация, расхождение метрик cloud-edge. EasyAIoT добавляет выделенный <strong>модуль EDGE</strong> (C#) как <strong>независимо развёртываемую среду сбора на периферии</strong>: подключаемые мультипротокольные коллекторы, локальное планирование, разбор по конфигурации и MQTT-интеграция с облачной платформой EasyAIoT — поднимает точки Modbus RTU/TCP, OPC UA и другие в единый uplink вещной модели, с push конфигурации из облака и записью свойств, доходящими до периферии для исполнения.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0;">
<strong>Отличие от «шлюза» в управлении устройствами:</strong> В управлении устройствами шлюз — это облачный тип продукта/устройства (топология GATEWAY + подустройства SUBSET) для регистрации, shadow, привязки и downlink. У EDGE нет отдельной страницы устройств — это процесс на объекте, который <strong>выступает этим шлюзом</strong>; собранные данные отображаются в том же управлении устройствами. Другой путь — <strong>облачный опрос</strong> Modbus/OPC UA через iot-sink (платформа должна достигать полевых устройств); EDGE собирает на объекте и поднимает только через MQTT — подходит для изоляции OT и RS-485. Uplink/downlink свойств шлюза, прокси-свойства подустройств и push конфигурации уже выровнены для использования как промышленный шлюз на объекте; проактивная топология, passthrough событий/сервисов подустройств, OTA и полная протокольная поверхность шлюза ещё развиваются.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0 8px 0;">
<strong>Почему C# для сбора IoT на периферии?</strong>
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Близость к промышленной площадке</strong>: C# имеет зрелую экосистему в промышленной автоматизации, SCADA и HMI — богатые библиотеки протоколов и инженерная практика для Modbus, OPC UA, последовательной связи и др.; низкий порог входа для интеграторов и инженеров автоматизации</li>
  <li><strong>Сильная типизация + структурированная инженерия</strong>: маппинг точек, разбор регистров и валидация конфигурации выявляются на этапе компиляции — стабильнее и тестируемее скриптовых языков при долгосрочном сопровождении мультипротокольных коллекторов</li>
  <li><strong>Асинхронная конкурентность без блокировки</strong>: <code>async/await</code> подходит для опроса множества устройств и параллельного serial/network I/O — один шлюз может планировать десятки подустройств без узких мест пропускной способности интерпретируемых путей вроде GIL Python при высокочастотном опросе</li>
  <li><strong>Стабильность долгоживущего сервиса</strong>: runtime .NET подходит для демонов edge-шлюзов 7×24 с предсказуемой памятью и GC; dependency injection и плагинная архитектура позволяют горячую замену коллекторов без перезапуска всей площадки</li>
  <li><strong>Кроссплатформенная поставка</strong>: тот же код C# публикуется на промышленные ПК Linux x86_64 / ARM64 и edge-боксы — single-file/self-contained развёртывание без Python virtualenv или JVM на объекте</li>
  <li><strong>Чёткое разделение с облачной платформой</strong>: периферия фокусируется на сбор—разбор—публикацию; DEVICE — на вещные модели и жизненный цикл устройств — C# не несёт тяжёлую бизнес-логику платформы и инференс ИИ, остаётся лёгким и работает независимо на стороне шины RS-485 или слабых шлюзах</li>
</ul>

<table style="width: 100%; border-collapse: collapse; margin: 12px 0 20px; font-size: 14px;">
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50; width: 18%;">Коллектор</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50;">Протокол / сценарий</td>
</tr>
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444;"><code>modbus-rtu</code></td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444; line-height: 1.7;">Modbus RTU (RS485/serial) — счётчики, приборы, ПЛК на шине</td>
</tr>
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444;"><code>modbus-tcp</code></td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444; line-height: 1.7;">Modbus TCP — Ethernet-оборудование, частотники, шлюзы</td>
</tr>
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444;"><code>opc-ua</code></td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444; line-height: 1.7;">OPC UA — современная промышленная автоматизация и взаимодействие с верхнеуровневыми системами</td>
</tr>
</table>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Плагинная архитектура сбора</strong>: реализуйте <code>ICollector</code> для расширения новых протоколов; Host управляет регистрацией, планированием и отчётностью — логика сбора отделена от runtime</li>
  <li><strong>Двойной канал конфигурации</strong>: локальный <code>device-jobs.json</code> для автономной работы; облачный MQTT <code>config/downstream/push</code> может удалённо переопределять задания сбора — без выезда на объект для смены конфигурации</li>
  <li><strong>MQTT cloud-edge интеграция</strong>: подключается как GATEWAY платформы — отчёт свойств шлюза, прокси-свойства подустройств, downlink записи свойств через EMQX к DEVICE/<strong>iot-sink</strong>; автосоздание подустройств и сохранение shadow; данные отображаются в управлении устройствами</li>
  <li><strong>Автономная упаковка</strong>: <code>pack_linux.sh</code> создаёт пакеты развёртывания Linux x86_64 / ARM64 для промышленных ПК и edge-шлюзов — отделено от основного стека платформы</li>
  <li><strong>E2E интеграция из коробки</strong>: <code>bash EDGE/demo/run_e2e.sh</code> проверяет полную цепочку — сбор → MQTT uplink → сохранение в облаке</li>
</ul>

### 🛰️ SENTINEL: часовой узлов кластера — «подключил готовым, планируй по реальной способности»

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Федеративное расширение чаще всего упирается в «машина уже в кластере, но никто не знает, может ли она брать работу» — видеоаналитика, ретрансляция потоков и обучение моделей требуют разной готовности; задачи уходят вниз только чтобы обнаружить пробелы среды, а на объекте снова и снова заходят на серверы ставить зависимости, пока приёмка не зависает на «установили, но не стартует». EasyAIoT добавляет отдельный <strong>модуль SENTINEL</strong> — <strong>часовой бизнес-готовности</strong>, который идёт с каждым планируемым узлом: непрерывно проверяет, может ли машина реально взять отмеченные нагрузки, сводит планируемую ёмкость в консоль и может запросить дополнение среды — меньше входов на серверы, меньше «мертвых» задач, приёмка в день расширения.
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Способность по выбранному бизнесу</strong>: видеоаналитика, ретрансляция, live, обучение, большие модели, умная разметка — что отмечено, то и отслеживается; без догадок по роли</li>
  <li><strong>Мониторинг сразу после подключения</strong>: после ввода узла часовой стартует сам — в день расширения видно «может ли брать работу»</li>
  <li><strong>Планирование по реальной способности</strong>: в пул попадают только действительно готовые узлы — меньше переделок «назначили, а не стартует»</li>
  <li><strong>Самообслуживаемое дополнение</strong>: при отсутствии ожидаемой среды можно запросить дополнение у платформы — меньше ручных установок на объекте</li>
  <li><strong>Расширение без публичного интернета</strong>: офлайн-подключение и синхронизация среды на изолированных или ограниченных площадках</li>
  <li><strong>Приёмка с одного экрана</strong>: здоровье компонентов и планируемые функции видны вместе — единый язык поставки</li>
</ul>


### 🧭 POST: кастомное суждение — превратить «детекцию» в операционные бизнес-события

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Визуальные проекты часто упираются в «модель уже обвела людей/машины/объекты, а оповещениями пользоваться нельзя» — прохожие вне зоны всё равно тревожат, нормальная работа тоже, заказчику нужны пересечение линии, задержка, превышение численности, а команда лишь переобучает модели, останавливает задачи и ждёт разработку. EasyAIoT добавляет отдельный <strong>сервис кастомного суждения POST</strong>, разделяя <strong>визуальное восприятие</strong> и <strong>бизнес-решение</strong>: детекция продолжает «видеть», суждение по задаче оркестрирует «нужно ли оповещать и о чём» — правила меняются без переобучения, анализ не останавливается, оповещения наконец совпадают со стандартами стройки, кампуса, транспорта и завода.
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Оркестрация суждения по задаче</strong>: у каждой алгоритмической задачи свои шаги постобработки — по умолчанию фильтр по зонам детекции, затем стандартное оповещение; бизнес-скрипты или отраслевые плагины собирают подсчёт людей, пересечение линии, таймаут пребывания, задержку в зоне и составные тревоги в полевую цепочку правил — один раз настроили сценарий, переиспользуете на многих задачах</li>
  <li><strong>Оповещения только там, где важно бизнесу</strong>: связь с «детекцией зон» устройства — цели вне зоны отфильтровываются, без залива экрана; без нарисованных зон оповещения не блокируются. Внимание дежурных — на запретных зонах, проходах и рабочих местах; ложные тревоги и ручная проверка резко падают</li>
  <li><strong>Бизнес-скрипты и цепочки правил сосуществуют</strong>: скрипты в базовой конфигурации пишут решение «языком поля»; страница правил отвечает за фильтр и порядок шагов. Обе возможности независимы и могут работать вместе — не нужно выбирать между «писать скрипт» и «настраивать шаги»</li>
  <li><strong>Отраслевая логика подключается</strong>: дифференцированное суждение для кампусов, строек и транспорта без правок ядра. Интеграторы регистрируют, запускают/останавливают свои возможности и вешают на задачи — одна модель детекции обслуживает много проектов заказчиков</li>
  <li><strong>Пробный прогон до запуска</strong>: онлайн-воспроизведение текущих правил на примерах или реальных событиях детекции — по шагам видно pass/drop и будет ли тревога. Приёмка отвечает «что именно отсекло это правило»</li>
  <li><strong>Смена правил действует сразу</strong>: сохранение правил на работающей задаче принимает новый стандарт — без остановки анализа и без повторной публикации видео. Временная смена запретной зоны или добавление шага — в тот же день</li>
  <li><strong>Восприятие и суждение не душат друг друга</strong>: мониторинг продолжает анализ, бизнес-логика расширяется по необходимости; при сбое суждения — «пропустить шаг и продолжить оповещение» или «лучше не тревожить, чем ошибиться». В standard/full включено по умолчанию; лёгкий standalone сначала замыкает цикл детекция–тревога и повышает уровень при необходимости</li>
  <li><strong>Четыре встроенных плагина суждения (без регистрации)</strong>: <strong><code>line_cross</code></strong> (пересечение линии с линиями <code>line</code> + трекинг), <strong><code>region_enter_exit</code></strong> (вход/выход из зоны), <strong><code>dwell_timer</code></strong> (таймаут пребывания/задержки), <strong><code>headcount_gate</code></strong> (порог численности) — составляются с фильтром зон, пропуском, бизнес-скриптами и отраслевыми плагинами в полевые цепочки правил</li>
</ul>

### 🤖 AI-ассистент: совместная работа в разделённом экране IDEA — править код и спрашивать об архитектуре и здоровье

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Вклад в open source и полевые PoC часто упираются в одно и то же: много модулей, длинные цепочки — для правок нужна локальная среда, для здоровья — SSH, для архитектуры — документация и люди. EasyAIoT встраивает <strong>разговорного ассистента HARNESS</strong> в <strong>облачную IDE IDEA</strong> — слева полный workspace VS Code, справа AI-ассистент в split; перетащите файлы из проводника для авто <code>@</code>-упоминания, читайте исходники и спрашивайте о портах, конфиге и здоровье сервисов, сокращая цикл «не знаю → спросить → править снова».
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Совместная работа IDEA в split</strong>: панель инструментов открывает AI-ассистента справа — редактор и Agent рядом; deep-link <code>?file=путь&harness=1</code> открывает файл и split</li>
  <li><strong>Перетащить для авто @</strong>: файлы из проводника на панель ассистента автоматически становятся контекстом чата — меньше путей вручную, меньше потери контекста</li>
  <li><strong>Спросил — проверил</strong>: Agent вызывает Tools платформы для Gateway / видео / AI и указывает конфиг и исходники — SSH + compose в одном диалоге</li>
  <li><strong>Знает онтологию</strong>: встроенный <code>HARNESS/ontology/AGENTS.md</code> и workspace всего репозитория — архитектура, порты, API и соглашения об установке в одном месте</li>
  <li><strong>Та же семантика в консоли</strong>: плавающий drawer / полноэкранный «AI-ассистент» делят возможности с IDEA; MCP + Cursor Skill переиспользуются между средами</li>
  <li><strong>Двусторонний переход</strong>: ассистент может сгенерировать ссылку портала через <code>easyaiot_open_in_idea</code> — из Q&amp;A обратно в полный IDE, где можно править и публиковать</li>
</ul>

| | | |
|:---:|:---:|:---:|
| ![Вход IDEA](.image/banner/banner1203.png) | ![Рабочая область IDEA](.image/banner/banner1204.png) | ![Разработка IDEA](.image/banner/banner1205.png) |
| ![Диалог AI-ассистента](.image/banner/banner1210.png) | ![Анализ AI-ассистента](.image/banner/banner1211.png) | ![Совместная работа AI-ассистента](.image/banner/banner1212.png) |

### 📱 ANDROID / IOS / HARMONYOS: один фронтенд, три нативные оболочки — один App для любого телефона

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Мобильная поставка часто упирается в покрытие платформ: приложение, работающее только на одной ОС, привязывает полевой персонал к выданным компанией телефонам, а каждая дополнительная нативная кодовая база удваивает затраты и разводит функциональность. Мобильная часть EasyAIoT — это <strong>один фронтенд uni-app + три нативные оболочки</strong>: одни и те же страницы <strong>APP</strong> компилируются в устанавливаемые приложения <strong>ANDROID</strong> (офлайн-рантайм DCloud + Gradle → APK), <strong>IOS</strong> (оболочка WKWebView + xcodebuild → .app / .ipa) и <strong>HARMONYOS</strong> (оболочка ArkWeb + hvigor → HAP) — одна бизнес-логика и нативные установщики на всех массовых ОС телефонов, без поддержки трёх кодовых баз.
</p>

<table style="width: 100%; border-collapse: collapse; margin: 12px 0 20px; font-size: 14px;">
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; width: 14%;">Платформа</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; width: 34%;">Технология оболочки</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; width: 30%;">Артефакт сборки</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600;">Скрипт одной командой</td>
</tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>ANDROID</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Офлайн-рантайм uni-app DCloud + Gradle</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;"><code>easyaiot-&lt;версия&gt;-&lt;окружение&gt;-android.apk</code></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;"><code>ANDROID/make-apk.sh</code> / <code>make-apk.bat</code></td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>IOS</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Оболочка WKWebView + xcodebuild (Xcode 16+)</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;"><code>.app</code> (симулятор, без подписи) / <code>.ipa</code> (устройство)</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;"><code>IOS/make-ipa.sh</code></td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>HARMONYOS</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Оболочка ArkWeb + hvigor (DevEco Studio)</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;"><code>easyaiot-&lt;версия&gt;-&lt;окружение&gt;-harmonyos.hap</code></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;"><code>HARMONYOS/make-hap.sh</code></td></tr>
</table>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Один код, ноль расхождений</strong>: Все три оболочки используют одни и те же страницы APP и один admin-api — управление устройствами, живой просмотр, ретрансляция потоков, алгоритмические задачи, центр тревог, инференс/обучение моделей — с той же функциональностью, что и PC-консоль, на Android, iOS и HarmonyOS; различия нативных возможностей фронтенда изолированы условной компиляцией — одно изменение применяется ко всем трём платформам</li>
  <li><strong>Системный нативный рендеринг на каждой платформе</strong>: Android запускает офлайн-рантайм uni-app для нативного опыта App; iOS отдаёт H5-сборку через кастомную схему <code>easyiot://</code>, чтобы страницы работали как обычный сайт (ES-модули, localStorage и cross-origin запросы к admin-api ведут себя как при реальном развёртывании); HarmonyOS отображает ресурсы rawfile через виртуальный хост <code>http://appassets.local/</code> в ArkWeb — никаких сторонних движков, ограничений file:// и расхождений в поведении</li>
  <li><strong>Сборка одной командой на платформу</strong>: <code>make-apk.sh</code> / <code>make-ipa.sh</code> (симулятор .app или устройство .ipa) / <code>make-hap.sh</code> выполняют проверку согласованности версий → сборку фронтенда → синхронизацию ресурсов → нативную сборку → именованный артефакт; окружения prod / test / dev дают независимые пакеты, которые никогда не перезаписывают друг друга</li>
  <li><strong>Единая точка управления</strong>: <code>.scripts/docker/mobile.sh</code> охватывает все три платформы — <code>status</code> (согласованность версий + готовность тулчейнов + готовые артефакты), <code>build android|ios|harmonyos|all</code>, <code>bump</code>, <code>artifacts</code> и <code>clean</code> — для рутинных операций не нужно заходить в каждый модуль</li>
  <li><strong>Одна команда выравнивает все пять полей версии</strong>: manifest APP + build.gradle Android + <code>dcloud_control.xml</code> + pbxproj iOS (Debug/Release) + <code>app.json5</code> HarmonyOS — <code>.scripts/docker/mobile.sh bump 1.0.1 101</code> обновляет каждую копию и перечитывает для проверки; каждый скрипт сборки отказывается выпускать пакет при расхождении копий — несогласованная версия никогда не выйдет</li>
  <li><strong>Стандартизированные имена артефактов</strong>: нижний регистр kebab-case <code>easyaiot-&lt;версия&gt;-&lt;окружение&gt;-&lt;платформа&gt;.&lt;формат&gt;</code> — стабильная сортировка для архивации, идеально для объектного хранилища / CDN и сбора артефактов в CI; <code>mobile.sh artifacts/clean/status</code> распознаёт и старые, и новые имена</li>
  <li><strong>Раздельный CI-конвейер</strong>: любой Linux-runner может выполнить <code>--skip-native</code> для сборки и синхронизации ресурсов фронтенда, затем передать подготовленный проект macOS-runner'у (iOS) или self-hosted DevEco-runner'у (HarmonyOS) для финальной нативной компиляции — один конвейер, три платформы, без тулчейна платформы на каждой машине</li>
  <li><strong>Подписи и распространение готовы</strong>: Android подписывается встроенным <code>iot.jks</code> (AppKey DCloud зарегистрирован); iOS-сборки для симулятора не требуют аккаунта, а сборки для устройств / App Store используют автоматическую подпись с Team ID; HarmonyOS автоматически генерирует отладочные подписи в DevEco и поддерживает подпись релиза через AppGallery Connect</li>
  <li><strong>Документация и диагностика в каждом модуле</strong>: каждый модуль поставляет собственный README с подготовкой окружения (JDK / Xcode 16+ / DevEco), управлением версиями, подписями и таблицей FAQ; единое руководство по трём платформам — в <a href="MOBILE.md" style="color: #3498db; text-decoration: none; font-weight: 600;">MOBILE.md</a></li>
</ul>

### 🎯 Четыре уровня оборудования, одна платформа

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Многие проекты интеллектуального IoT спотыкаются на этапе развёртывания: <strong>полный функционал не помещается на маленькие машины; чтобы поместить — сокращают возможности, делят версии и поддерживают несколько пакетов развёртывания.</strong> EasyAIoT решает эту дилемму одной платформой — от <strong>сверхлёгкого edge-standalone</strong> до <strong>edge-бокса для точечного интеллекта, AI-камеры «всё в одном» для анализа на стене, AIoT full-stack «всё в одном» для полного стека в одной коробке</strong>. Выберите один из четырёх распространённых классов полевого оборудования; одно и то же ПО — от «просто запустить» через пилот на точке и покрытие этажа до полной поставки — без разделения версий.
</p>

| Уровень | Типичное оборудование (примеры) | Реком. RAM | Что можно делать | Проверено |
| :-- | :-- | :--: | :-- | :--: |
| **edge** Edge Standalone | <strong>Лёгкий edge-standalone</strong> (промПК 2 ГБ, старый ноутбук, минимальная облачная ВМ, пробный бокс магазина) | ≥ 2 ГБ | <strong>Сначала замкнуть контур на одной машине</strong>: WEB + VIDEO + RUNTIME; доступ к камерам, анализ в реальном времени, оповещения; без DEVICE, логин ведёт VIDEO | ~**1,02 ГБ**, почти 1 ГБ запаса |
| **mini** Edge Lite | <strong>Edge-бокс</strong> (промышленный ПК 8 GB, «всё в одном» для магазина, шлюз на объекте) | ≥ 8 GB | <strong>Интеллект на одной точке</strong>: доступ к камерам, анализ в реальном времени, умные оповещения, инференс; событийный контур как у standard/full (Gateway + iot-sink + EMQX) | ~4–6 GB, достаточный запас |
| **standard** Standard | <strong>AI-камера «всё в одном»</strong> (интеллектуальный камерный терминал, AI-камера с вычислениями, мультисенсорный AI-анализатор) | ≥ 16 GB | <strong>Каждая камера — умный узел</strong>: несколько камер на стене покрывают этаж/кампус; устройства, правила и вычисления оркестрированы вместе; <strong>кастомное суждение POST</strong> делает оповещения по полевым стандартам | ~10 GB, стабильно с запасом |
| **full** Полный (по умолч.) | <strong>AIoT full-stack «всё в одном»</strong> (корпоративный full-stack, отраслевой IoT full-stack хост, облачно-периферийная платформа) | ≥ 20 GB | <strong>IoT + видео + AI в одной коробке</strong>: управление устройствами, массовый доступ, интеллектуальный анализ, единое командование — полные возможности долгосрочно; включает <strong>кастомное суждение POST</strong> и внешний бизнес-поток | ~14 GB, полный функционал с запасом |

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0 8px 0;">
<strong>Установка edge:</strong> <code>EASYAIOT_DEPLOY_PROFILE=edge sudo bash .scripts/docker/install_linux.sh install</code> (или <code>... install_linux.sh edge install</code>). При первой установке уровень можно выбрать интерактивно; подробности — в <a href="#-быстрый-старт">Быстром старте</a> выше.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 16px 0 8px 0;">
<strong>Выбор уровня и соответствие ресурсов (проверено):</strong>
</p>

| | |
|:---:|:---:|
| ![Edge standalone](.image/deploy-profile-edge.png) | ![Edge-бокс mini](.image/deploy-profile-mini.png) |
| ![AI-камера all-in-one standard](.image/deploy-profile-standard.png) | ![Full-stack комплекс full](.image/deploy-profile-full.png) |

#### 🧠 Возможности ИИ

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Высокоскоростной слой исполнения RUNTIME</strong>: Выносит «смотреть / считать / пушить» из интерпретируемых цепочек в <strong>нативный бинарник</strong>, который ведёт <strong>pull → декодирование → инференс → callback оповещений → push с рамками</strong>. По сравнению с Python избегает GIL и накладных расходов мультипроцессов — на том же железе <strong>больше каналов на бокс, ниже end-to-end задержка, меньше CPU/память</strong>. Realtime / snap / patrol и многоканальный сырой forward делят одну исполнительную способность; по умолчанию <code>executor=cpp</code>. На практике: сначала десятки каналов NVR «чётко и без рывков», затем ИИ только на ключевых; сырой просмотр и суждение с рамками переключаются без взаимного удушения; VIDEO/WEB оставляют оркестрацию, архив и права, RUNTIME фокусируется на пропускной способности и задержке — расширять каналы без смены всей машины</li>
  <li><strong>Высокопроизводительная пересылка потоков</strong>: Под поставку «сначала заполнить видеостену / split, не включая ИИ на каждом канале» — каналы NVR и точки здания в один клик. Путь по умолчанию — <strong>RUNTIME</strong> (режим совместимости доступен), чтобы многоканальное сырое видео держалось на стене дешевле. Сырой просмотр и ИИ-суждение параллельны; при старте/стопе алгоритмов политика пересылки следует автоматически. Параллельный превью ускоряет приёмку</li>
  <li><strong>Настройка названия и логотипа платформы на всех точках контакта</strong>: После развертывания EasyAIoT на объекте пользователи должны видеть «свою» платформу, а не общее название продукта. На панели мониторинга встроена визуальная панель «Идентичность платформы», где администратор может заменить брендинг в интерфейсе: название и логотип консоли администрирования (синхронизация с боковой панелью и вкладкой браузера); независимый заголовок командного центра на большом экране; настройка страницы входа — название, логотип, заголовок формы, светлые/тёмные фоновые изображения. Три точки контакта визуально согласованы, изменения применяются мгновенно, поддерживаются сохранение и сброс в один клик.
    <ul style="margin: 5px 0; padding-left: 20px;">
      <li><strong>Для системных интеграторов и поставщиков решений</strong>: исключает затраты на перекраску фронтенда, доработку и циклы релизов; быстрое переключение брендинга между PoC-демо и промышленной поставкой, одна кодовая база для нескольких заказчиков, сокращение цикла оплаты и повышение повторного использования решений</li>
      <li><strong>Для конечных пользователей (госорганы, кампусы, больницы и др.)</strong>: страница входа, командная панель и ежедневная консоль администрирования отображают название и идентичность организации — больше принадлежности и доверия при визитах руководства и внутреннем внедрении, соответствие требованиям брендинга ИТ-проектов госсектора и крупных предприятий</li>
      <li><strong>Для команд частного развертывания и эксплуатации</strong>: настройка на объекте в день установки для приёмки — без ожидания разработки; сброс в один клик после демо для нескольких заказчиков или пилотных фаз, снижение затрат на переключение и повторное развертывание</li>
    </ul>
  </li>
  <li><strong>Обнаружение объектов YOLO26 нового поколения</strong>: Встроенные возможности обнаружения объектов нового поколения, готовые к использованию «из коробки» для анализа в реальном времени и распознавания на снимках. На том же оборудовании можно подключить больше камер, получить более быстрый отклик и меньше ложных срабатываний. Поддерживается полный цикл от сбора данных, разметки и обучения до развертывания и инференса — помогает пользователям с меньшими затратами итеративно создавать собственные модели обнаружения и быстро покрывать типичные сценарии безопасности и промышленности (каски, несанкционированный доступ, пожарная опасность и др.), делая «точное зрение, быстрые вычисления, легкое масштабирование» стандартной возможностью</li>
  <li><strong>Анализ позы человека YOLO26</strong>: Дополняет обнаружение объектов анализом ключевых точек тела и скелетной позы, готов к использованию «из коробки», поддерживает три режима ввода: изображения, видео и потоки с камер в реальном времени. Режим изображений одновременно выводит разметку скелета и подсчёт людей; режим видео поддерживает отслеживание прогресса и загрузку результатов; режим камеры подключается к потокам RTSP/RTMP в реальном времени и накладывает результаты распознавания позы на ретранслируемый вывод для удалённого наблюдения и анализа поведения. На странице инференса модели доступно переключение в один клик между «Анализом позы» и «Обнаружением объектов», подходит для контроля норм работы на стройплощадках, оценки фитнес-движений, мониторинга скоплений людей и других сценариев, где нужно «чётко видеть структуру и форму движений тела», переводя платформу от «обведения целей рамкой» к «пониманию позы»</li>
  <li><strong>Поддержка доступа к камерам по нескольким протоколам</strong>: Полная поддержка двух основных протоколов видеонаблюдения GB28181 и ONVIF, обеспечивающая стандартизированный доступ и управление устройствами. GB28181, как национальный стандарт Китая, идеально адаптирован к основному отечественному оборудованию видеонаблюдения; ONVIF, как международный универсальный стандарт, широко совместим с основными мировыми брендами камер. Благодаря поддержке двух протоколов платформа бесшовно интегрируется с существующими системами видеонаблюдения, обеспечивая подключение устройств по принципу plug-and-play, автоматическое обнаружение и единое управление, значительно снижая барьеры доступа к устройствам, повышая совместимость и масштабируемость системы и создавая прочную техническую основу для крупномасштабного развертывания камер. Кроме того, добавлены массовое сканирование, регистрация и единое управление NVR в одной и между подсетями с поддержкой Hikvision, Dahua, Huawei, Ezviz, Xiaomi и других основных брендов — обнаружение по подсети, регистрация в один клик и массовый импорт каналов через нативные протоколы устройств. Для потребительских камер без RTSP, таких как Mi Home, <strong>модуль RTC (мост go2rtc)</strong> включает их в ту же платформу, дополнительно снижая затраты на подключение и эксплуатацию</li>
  <li><strong>Доступ воздушного обзора доков / дронов DJI</strong>: Преодолевает ограничение фиксированных камер «только земля, трудно покрыть широкую зону»; включает высотные кадры доков и дронов экосистемы DJI в единый контур видео и ИИ-оценки. Модуль стриминга предоставляет «Подключение прямой трансляции DJI»: поддерживаются <strong>запуск live через API</strong> и <strong>ручной источник</strong> — в API-режиме одним кликом поднимается поток производителя с автоматической регистрацией устройства; вручную можно указать RTSP / RTMP / HTTP-FLV / HLS. После подключения воздушные кадры совместно управляются с фиксированными точками GB28181/ONVIF; администраторы могут просматривать доки и летательные аппараты как обычные камеры и подключать анализ ИИ в реальном времени, оповещения и сохранение доказательств — для широкомасштабного патрулирования, аварийной разведки и дополнения периметра; сокращает цепочку «обнаружить — локализовать — действовать», переводя интеллектуальную безопасность от плоского развёртывания к совместному небо–земля восприятию.</li>
  <li><strong>P2P-мост потребительских камер RTC</strong>: Одна интеграция для <strong>Tapo, Tuya, Ring/Nest, Xiaomi Mi Home, Wyze, DoorBird, GoPro и Roborock</strong> — все девять брендов без стандартного RTSP. Модуль RTC на базе go2rtc обеспечивает P2P-мост и единый API управления. В веб-консоли «Подключить RTC-камеру» с формами по брендам или OAuth; после моста потребительские и профессиональные GB28181/ONVIF камеры <strong>на одном экране, с одними ИИ-задачами и оповещениями</strong></li>
  <li><strong>Интерком в реальном времени и удалённое управление PTZ</strong>: Преодолевает традиционное ограничение видеонаблюдения «только смотреть, нельзя управлять». Операторы могут выполнять голосовое оповещение и управление PTZ на одном экране предпросмотра в реальном времени — без переключения систем и без выезда на место. Удалённое общение, направление эвакуации или пресечение нарушений: реагирование сжимается от «отправить человека на место» до «сказал — и дошло». Управление PTZ позволяет свободно поворачивать, масштабировать и фокусировать камеру — при внезапных ситуациях быстро навести на зону инцидента и увеличить детали, формируя интегрированный цикл реагирования на месте: «видеть ясно, наводить точно, донести голос». Полная совместимость с устройствами GB28181 и ONVIF, использование существующих активов видеонаблюдения без дополнительного оборудования интеркома или стороннего ПО — развёрнутые камеры мгновенно получают возможности удалённого общения и гибкого диспетчерского управления, значительно снижая изоляцию систем и затраты на дежурство</li>
  <li><strong>Кастомное суждение POST (оркестрируемая постобработка)</strong>: Преодолевает узкое место «обнаружить можно, но оценить сложно» отдельным сервисом <strong>POST</strong> как слоем бизнес-суждения — визуальное восприятие становится операционными, подотчётными и статистически учитываемыми событиями. Внутри алгоритмической задачи оркестрируется цепочка правил: по умолчанию фильтр по зонам детекции, затем оповещение; бизнес-скрипты и отраслевые плагины — подсчёт людей, пересечение линии, таймаут пребывания, задержка в зоне, составные тревоги — без постоянной доработки моделей. Пробный прогон правил до запуска; сохранение на работающей задаче действует сразу, без остановки анализа. Восприятие и суждение параллельны — меньше ложных/пропущенных тревог и ручной проверки; от «видеть» к «судить ясно, управлять и использовать»</li>
  <li><strong>Федеративный кластер «N центральных узлов × N рабочих узлов»</strong>: Для межрегиональных, мультидатацентровых и облачно-периферийных развертываний платформа использует федеративную архитектуру «N центральных узлов + N рабочих узлов» — центральные узлы служат единой плоскостью управления, рабочие узлы — плоскостью выполнения вычислений и медиа, с возможностью горизонтального масштабирования. Каждый центральный узел управляет рабочими узлами своего домена, поддерживает удалённое распределение и развёртывание в один клик для стриминга, аудио- и видеотранскодирования, видеоаналитики, инференса и обучения моделей; несколько центральных узлов могут взаимно подключаться и синхронизироваться; вид «дорожек» кластера наглядно показывает топологию «центр — рабочий» и уровень ресурсов. Алгоритмические задачи, конвейеры автоматической разметки и ретрансляция потоков интеллектуально планируются по роли узла и возможностям GPU — массовый приём потоков, высококонкурентный инференс и распределённое обучение работают в одном кластере: «подключай легко, планируй ясно, масштабируй свободно, управляй полностью»</li>
  <li><strong>Часовой узлов SENTINEL</strong>: Для федеративного расширения и межмашинных вычислительных пулов — снимает боль «машина подключена, способность неизвестна». Непрерывно выявляет готовность и планируемую ёмкость по бизнес-функциям, назначает задачи только на реально готовые машины; может запросить дополнение среды и поддерживает офлайн-подключение без публичного интернета — кластер «подключает ясно, распознаёт точно, назначает верно, реже заходит на серверы»</li>

  <li><strong>Конвейер оркестрации автоматической разметки SAM с нулевого старта</strong>: Для сценариев холодного старта без размеченных образцов и пригодной модели обнаружения платформа объединяет сегментацию SAM с открытым словарём и предлагает конвейер автоматической разметки без участия оператора в один клик. По заданной стратегии система автоматически связывает извлечение кадров с камер, начальную разметку SAM по текстовым подсказкам, дообучение YOLO после достижения порогов, высокоскоростной инференс YOLO на этапе серийной работы с интеллектуальным переключением на SAM для пропущенных детекций, периодическое итеративное обучение и автоматическую упаковку и экспорт наборов данных — замыкая полный цикл «сбор — разметка — обучение — экспорт». Поддерживаются пауза/возобновление задач и эластичное планирование в локальных или кластерных очередях вычислений; визуальная настройка стратегий и журналы выполнения помогают пользователям с нуля образцов и нуля моделей быстро нарастить собственную способность обнаружения — «задайте категории словами, дождитесь формирования модели» становится стандартным путём построения наборов данных</li>
  <li><strong>Эластичный кластер вычислений на десятки тысяч узлов и пул горизонтального масштабирования</strong>: Для сверхкрупных нагрузок ИИ и видео платформа создаёт единую распределённую вычислительную основу «облако — периферия — терминал», объединяя алгоритмические задачи, ретрансляцию потоков, алгоритмические сервисы, обучение и инференс моделей в одной системе горизонтальной балансировки нагрузки и эластичного масштабирования. Новые серверы подключаются в один клик и сразу становятся планируемыми вычислительными единицами — планировщик автоматически распределяет задачи и балансирует нагрузку по уровню ресурсов и бизнес-давлению, обеспечивая линейное масштабирование от сотен до десятков тысяч камер и от одной машины до кластера на десятки тысяч узлов — без повторного развёртывания и ручной настройки. Массовый приём потоков, высококонкурентный инференс и распределённое обучение работают в одном пуле вычислений — «масштабируй по требованию, работай стабильно, управляй уверенно»</li>
  <li><strong>Драйвер распределённого хранилища (разделение кластеров вычислений и хранения)</strong>: Выходя за рамки устаревшей схемы монтирования локальных каталогов на каждом узле, жёстко прописанных путей и переконфигурации при каждом масштабировании, платформа заменяет драйверы локальных каталогов на <strong>управление событиями кластера</strong> — готовность Export, монтирование клиентов, переключение master/standby и мосты между кластерами воспринимаются и распространяются как события; снимки, записи, доказательства оповещений и модельные активы записываются в распределённый NFS-кластер без необходимости отслеживать пути монтирования на уровне бизнеса. Вычисления и хранение образуют <strong>два независимо масштабируемых домена</strong>: вычислительная сторона полностью опирается на высокоскоростной конвейер <strong>C++ RUNTIME</strong>, а сторона хранения строит пул NFS-кластеров с неограниченным горизонтальным масштабированием — вычисления и хранение растут по собственным уровням нагрузки, без жёсткой связки. Поддерживаются swimlane-кластеры, топологические представления и синхронизация через мосты между кластерами; новые узлы присоединяются к домену хранения в один клик — при массовом приёме потоков «вычислений хватает» и «места хватает» продвигаются параллельно: «разделение вычислений и хранения, независимое масштабирование, координация по событиям, единое управление, неограниченное расширение»</li>
  <li><strong>Пространственная визуализация Tianditu и анализ на карте</strong>: Интеграция с национальной картой Китая Tianditu объединяет камеры, оповещения и распознавание людей/транспорта на одной карте, переводя мониторинг от «просмотра потоков» к «обзору всей картины». Модули потокового медиа и оповещений предлагают вид «Распределение на карте» с деревом каталога устройств для регионального фокуса — мгновенный обзор расположения КПП и статуса онлайн. Клик по карте, поиск места и пакетный импорт координат позволяют быстро привязать каналы GB, NVR и прямое подключение камер, чтобы каждый поток имел чёткий пространственный контекст. События автоматически отображаются на карте через координаты камер; фильтрация по времени, типу события, задаче и бизнес-меткам, просмотр снимков и записей в один клик — быстрый переход от «где произошло» к действию. В сочетании с базами лиц и номеров совпадения на нескольких точках образуют пространственные цепочки — <strong>поиск следов по человеку</strong> для восстановления маршрута и зоны присутствия в контролируемой области; <strong>поиск следов по транспорту</strong> для связи проездов и определения маршрута и зон остановки — для поиска людей/авто, патрулирования и разбора инцидентов. Мобильные устройства поддерживают воспроизведение траекторий на временной шкале. Переключение векторной и спутниковой подложки с автоподбором обзора — карта как основа для обнаружения аномалий, фиксации целей и координации</li>
  <li><strong>Многокарточное развертывание Qwen / DeepSeek</strong>: Поддерживается параллельное развертывание больших языковых моделей, таких как Qwen и DeepSeek, на нескольких GPU. Ресурсы GPU можно гибко планировать на уровне кластера и Worker, обеспечивая эластичное масштабирование и балансировку нагрузки экземпляров моделей для стабильного инференса при высокой нагрузке и длинном контексте</li>
  <li><strong>Интеллектуальное понимание больших визуальных моделей</strong>: Интегрирована большая визуальная модель QwenVL3, поддерживает глубокое визуальное рассуждение и семантическое понимание видео в реальном времени, способна выполнять интеллектуальный анализ и понимание сцен содержимого кадров, предоставляет более богатые визуальные когнитивные возможности, достигая перехода от восприятия на уровне пикселей к пониманию на семантическом уровне</li>
  <li><strong>AI-анализ видеопотоков с камер в реальном времени</strong>: Для потоков RTSP/RTMP — полный конвейер от pull/декодирования и инференса до структурированного вывода и оповещений; по умолчанию через <strong>RUNTIME</strong> (тот же исполнитель, что для снимков/патруля), отклик на уровне миллисекунд и <strong>push по умолчанию потока детекции с рамками</strong>. Цепочки просмотра (сырое) и алгоритма (детекция) независимы; результаты связываются с зонами, периодами обороны, лицами/номерами и постобработкой</li>
  <li><strong>Интеллектуальный патруль камер</strong>: Для сценариев с большим числом камер и ограниченным штатом дежурных платформа предлагает патрулирование на разделённом экране и пакетное патрулирование по каталогу устройств, выполняя ротационный AI-анализ крупных парков камер при ограниченном числе одновременных подключений. Поддерживаются три режима планирования — ротация, пул соединений и гибридный: автоматический захват кадров по интервалу, запуск моделей обнаружения и связь с оповещениями и распознаванием лиц/номеров. В гибридном режиме приоритетные потоки остаются под постоянным наблюдением, фоновые ротируются через пул — баланс между целевым контролем и полным охватом. Прогресс патруля передаётся в реальном времени, кадры автоматически архивируются; сессии патруля на сотни камер запускаются в один клик с разделённого экрана или из каталога — «меньше подключений, шире охват, быстрее обнаружение», переход от ручного просмотра экран за экраном к интеллектуальному автоматическому патрулю</li>
  <li><strong>Объединенная панель мониторинга предупреждений алгоритмов "Облако-Край-Устройство"</strong>: Предоставляет унифицированную панель мониторинга предупреждений алгоритмов "Облако-Край-Устройство" для отображения в реальном времени ключевой информации: состояния устройств, работы алгоритмических задач, статистики событий тревоги, результатов анализа видеопотоков и т.д. Поддерживает визуализацию данных в нескольких измерениях, реализует унифицированный мониторинг и управление облачными, пограничными и устройствами, предоставляя центрам управления интеллектуального мониторинга глобальный обзор.</li>
  <li><strong>Распознавание лиц и управление базой лиц</strong>: Поддерживается гибкое включение распознавания лиц в задачах камер. Предоставляется управление базой лиц и признаками лиц, включая добавление, запрос, обновление, удаление и эффективный поиск по образцам/признакам. Поддерживаются сравнение лиц и поиск личности по кадрам захвата, при этом полностью фиксируются результаты сопоставления, снимки, местоположение камеры и контекст устройства для последующего анализа перемещений персонала, задач безопасности и многомерной аналитической отчётности.</li>
  <li><strong>Распознавание номерных знаков и управление базой номеров</strong>: Включайте распознавание номеров одним кликом в задачах мониторинга. Система автоматически считывает номера проезжающих автомобилей и в реальном времени сопоставляет их с вашими базами номеров. Гибко ведите белые и черные списки и бизнес-метки; при совпадении с правилами мгновенно срабатывают оповещения — контроль проезда на въезде/выезде, наблюдение за целевыми автомобилями, разделение гостевого и постоянного транспорта. Автоматически регистрирует новые номера и сохраняет полную историю снимков и совпадений для последующего поиска, проверки маршрутов и хранения доказательств. Распознавание выполняется параллельно с существующей видеоаналитикой, не влияя на стабильность и оперативность основного мониторинга и оповещений</li>
  <li><strong>Рисование областей обнаружения устройств</strong>: Предоставляет визуальный инструмент для рисования областей обнаружения устройств, поддерживает рисование прямоугольных и многоугольных областей обнаружения на снимках устройств, поддерживает гибкую конфигурацию связи между областями и алгоритмическими моделями, поддерживает визуальное управление, редактирование и удаление областей, поддерживает горячие клавиши для повышения эффективности рисования, обеспечивает точную конфигурацию обнаружения областей и предоставляет точные определения диапазона обнаружения для алгоритмических задач.</li>
  <li><strong>Интеллектуальный механизм связанных тревог</strong>: Поддерживает тройной механизм связи между областями обнаружения, периодами обороны и событиями тревоги. Система интеллектуально определяет, соответствует ли обнаруженное событие одновременно указанному диапазону области обнаружения, находится ли в периоде обороны и соответствует ли типу события тревоги. Тревоги активируются только при одновременном выполнении всех трех условий, обеспечивая точную пространственно-временную фильтрацию условий, значительно снижая частоту ложных срабатываний и повышая точность и практичность системы тревог.</li>
  <li><strong>Заявки по тревогам (замкнутый контур ответственности ИИ-оповещений)</strong>: Превращает «ИИ сообщил о тревоге» в реальный процесс «есть ответственный, есть этапы, результат проверяем». После записи тревоги она автоматически сопоставляется с <strong>правилами маршрутизации</strong> (комбинация условий: объект/событие/задача/устройство/краевой узел); при совпадении автоматически создаётся <strong>заявка по тревоге</strong> и запускается процесс обработки — без ручной диспетчеризации, ответственность сразу закрепляется за человеком. Заявки выполняются на встроенной <strong>оркестрации процессов</strong> платформы (визуальный конструктор: согласование, со-подписание, копия, условные и параллельные ветвления, напоминания по тайм-ауту и др.) с действиями одобрить / отклонить / вернуть / делегировать / передать / добавить подпись и напоминаниями о задачах в мессенджере/приложении (глубокие ссылки сразу на детали согласования). Статус обработки, текущий ответственный и длительность каждой тревоги полностью фиксируются, образуя замкнутый цикл «тревога → заявка → обработка → проверка»; для существующих тревог заявку можно запустить вручную, чтобы ничего не было упущено.</li>
  <li><strong>Управление крупномасштабными камерами</strong>: Поддерживает подключение сотен камер, предоставляет полный спектр услуг: сбор, аннотирование, обучение, вывод, экспорт, анализ, оповещение, запись, хранение, развертывание.</li>
  <li><strong>Управление алгоритмическими задачами</strong>: Поддерживает создание и управление задачами реального времени, захвата и патрулирования. Каждая задача может гибко связываться с экстрактором кадров и сортировщиком для точного извлечения видеокадров и сортировки результатов.
    <ul style="margin: 5px 0; padding-left: 20px;">
            <li><strong>Задачи алгоритмов реального времени</strong>: Анализ RTSP/RTMP; бэкенд по умолчанию <code>executor=cpp</code> (запуск <strong>RUNTIME</strong>, push AI с рамками + оповещения/heartbeat), опциональный путь совместимости <code>python</code></li>
      <li><strong>Задачи алгоритмов захвата изображений</strong>: Анализ снимков; также может использовать <code>executor=cpp</code> (RUNTIME SnapScheduler / Cron)</li>
      <li><strong>Задачи алгоритмов патрулирования</strong>: Многопотоковый round-robin / пул; также может использовать <code>executor=cpp</code> (RUNTIME PatrolScheduler)</li>
    </ul>
  </li>
  <li><strong>Аннотирование наборов данных и управление в нескольких форматах</strong>: Предоставляет визуальную рабочую среду для аннотирования изображений с поддержкой прямоугольников и полигонов, управления категориями и отслеживания прогресса; полностью поддерживает гибкий импорт и экспорт распространённых форматов наборов данных, включая YOLO, COCO и ImageFolder, с интеграцией облачных наборов данных — импорт в один клик и синхронизированный экспорт — обеспечивая непрерывность полного цикла: сбор данных, аннотирование, обучение и развёртывание.</li>
  <li><strong>Многокарточное обучение, возобновление с контрольной точки и развёртывание на стороне узла</strong>: Устраняет узкие места обучения — «GPU есть, но не используются; задачи сложно контролировать; при прерывании результаты теряются» — системно связывая многокарточное использование вычислительных ресурсов, управляемое планирование задач и развёртывание на стороне узла, чтобы полевые GPU действительно задействовались, а задачи обучения действительно контролировались. Платформа автоматически обнаруживает и планирует все GPU сервера; пользователь на странице обучения может выбрать одну или несколько карт. Поддерживаются распространённые форматы наборов данных, загрузка больших локальных наборов; после сбоя обучения исходные данные сохраняются для быстрого повтора. Прогресс обучения полностью виден, задачи можно останавливать и возобновлять; при сбое локального или удалённого планирования — своевременный откат и понятная обратная связь, делая цикл «обучение — публикация — использование» более гладким и надёжным.</li>
  <li><strong>Переадресация потоков</strong>: Смотреть live камер без включения алгоритмов; пакетный push и автосоздание задач каналов NVR готовы из коробки. Путь по умолчанию — <strong>RUNTIME</strong> высокопроизводительный — «сначала заполнить стену, ИИ на ключевых каналах»; особые площадки — режим совместимости Python/FFmpeg</li>
  <li><strong>Обнаружение GPU, распределение по нагрузке и многокарточная координация</strong>: Платформа обнаруживает доступные GPU и интеллектуально распределяет кодирование/декодирование видео и алгоритмический вывод с учётом текущей нагрузки на каждую карту, выполняя задачи параллельно на нескольких GPU там, где это уместно, повышая пропускную способность мультипотоковой обработки и утилизацию вычислений при сохранении устойчивости и согласованной работы конвейера кадров и вывода моделей.</li>
  <li><strong>Умный выбор транспорта и устойчивый приём потока</strong>: На путях приёма RTSP и аналогичных система может автоматически выбирать подходящий способ передачи с учётом сценария, балансируя задержку и стабильность. При серых кадрах, ошибках декодирования или зависании картинки автоматически выполняется переподключение и восстановление канала, снижая влияние длительных артефактов и зависаний на бизнес.</li>
  <li><strong>Двойной путь просмотра и суждения</strong>: Разделить «видеостена / split сырого» и «результаты алгоритма» — дежурство в первую очередь чёткость и плавность; суждение независимо выдаёт кадры с рамками, без взаимного удушения. Одна камера может держать и live, и анализ; расширение каналов больше не выбор между «видеть ясно» и «считать достаточно»</li>
  <li><strong>Кластерный вывод моделей</strong>: Поддерживает распределенный кластер служб вывода моделей, реализует интеллектуальную балансировку нагрузки, автоматическое переключение при сбоях и обеспечение высокой доступности, значительно повышая пропускную способность вывода и стабильность системы.</li>
  <li><strong>Управление периодами охраны</strong>: Поддерживает две стратегии охраны: полный режим и полурежим. Позволяет гибко настраивать правила охраны для разных периодов времени, реализуя точный интеллектуальный мониторинг и оповещение по расписанию.</li>
  <li><strong>OCR и распознавание речи</strong>: Обеспечивает высокоточное распознавание текста и преобразование речи в текст, поддерживает многоязычное распознавание.</li>
  <li><strong>Мультимодальные большие визуальные модели</strong>: Поддерживают различные визуальные задачи, такие как распознавание объектов, распознавание текста, предоставляют мощные возможности понимания изображений и анализа сцен.</li>
  <li><strong>Большие языковые модели (LLM)</strong>: Поддерживают интеллектуальный анализ и понимание различных форматов ввода: потоки RTSP, видео, изображения, аудио, текст, реализуя мультимодальное понимание контента.</li>
  <li><strong>Развертывание моделей и управление версиями</strong>: Поддерживает быстрое развертывание моделей ИИ и управление версиями, реализуя однокнопочный запуск моделей, откат версий и постепенный релиз.</li>
  <li><strong>Управление несколькими экземплярами</strong>: Поддерживает параллельный запуск и планирование ресурсов нескольких экземпляров моделей, повышая утилизацию системы и эффективность использования ресурсов.</li>
  <li><strong>Захват изображений с камер</strong>: Поддерживает функцию мгновенного захвата изображений с камер. Позволяет настраивать правила захвата и условия срабатывания, реализуя интеллектуальный захват и запись событий.</li>
  <li><strong>Управление пространством для захваченных изображений</strong>: Предоставляет управление пространством хранения для захваченных изображений, поддерживает квоты на пространство и стратегии очистки, обеспечивая рациональное использование ресурсов хранения.</li>
  <li><strong>Управление пространством для видеозаписей</strong>: Предоставляет управление пространством хранения для файлов видеозаписей, поддерживает автоматическую очистку и архивирование, реализуя интеллектуальное управление ресурсами хранения.</li>
  <li><strong>Управление захваченными изображениями</strong>: Поддерживает полный жизненный цикл управления захваченными изображениями: просмотр, поиск, загрузку, удаление и т.д. Предоставляет удобные функции управления изображениями.</li>
  <li><strong>Управление каталогом устройств</strong>: Предоставляет древовидное управление каталогом устройств, поддерживает группировку устройств, иерархическое управление и контроль доступа, реализуя упорядоченную организацию и детализированное управление устройствами.</li>
  <li><strong>Запись по тревоге</strong>: Поддерживает функцию автоматической записи видео при срабатывании события тревоги. При обнаружении аномального события автоматически записывается соответствующий видеофрагмент, предоставляя полную цепочку доказательств для тревоги. Поддерживает просмотр, загрузку и управление записями по тревоге.</li>
  <li><strong>События тревоги</strong>: Предоставляет полный набор функций управления событиями тревоги. Поддерживает отправку уведомлений о событиях тревоги в реальном времени, исторические запросы, статистический анализ, обработку событий и отслеживание статуса, реализуя полный жизненный цикл управления тревогами.</li>
  <li><strong>Воспроизведение записей</strong>: Поддерживает быстрый поиск и воспроизведение исторических записей. Предоставляет удобные операции: навигация по временной шкале, изменение скорости воспроизведения, переход по ключевым кадрам. Поддерживает синхронное воспроизведение нескольких видеопотоков, удовлетворяя потребности в ретроспективе и анализе событий.</li>
</ul>

#### 🌐 Возможности IoT

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0 8px 0;">
Многие проекты сводят IoT к «реестру устройств + ретрансляции сообщений»: подключиться можно — управлять нельзя; данные уходят — наружу ничего не толкается; тревоги есть — площадку не видно. EasyAIoT ставит IoT как исполнительный нерв в контуре <strong>восприятие — понимание — решение — исполнение</strong>: датчики и исполнители дают «цифры», камеры и ИИ — «картинку», большие экраны визуализации и SCADA превращают «цифры» в управляемую ситуацию, а правила и тени связывают оба потока в операционные бизнес-действия — чтобы платформа не только «видела», но и «выводила на экран, понимала технологию, управляла, точно контролировала и масштабировалась».
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Визуальное управление</strong>: Если точки измерений, тревоги и бизнес-показатели остаются только в списках и сообщениях, руководство не видит полную картину, дежурный не разберётся, а для отчёта придётся делать отдельную презентацию — ценность данных застревает на этапе «можно собрать, но нельзя показать». Платформа объединяет проекты визуализации, центр шаблонов, библиотеку ресурсов, источники данных и развёртывание сервисов: перетаскиванием собирают из IoT-данных большие экраны ситуации кампуса, KPI линии, эксплуатации оборудования и т. п.; черновик можно править, зрелый — публиковать, опубликованный — выводить на экран — IoT переходит от «данные есть в бэкенде» к «экран есть на фронте», командный анализ и внешняя демонстрация не требуют отдельного инструмента больших экранов</li>
  <li><strong>Полный жизненный цикл проектов визуализации</strong>: Если проекты больших экранов разбросаны по личным компьютерам и временным ссылкам, передача неизбежно хаотична, версии теряются, а запуск превращается в спор. Платформа централизованно управляет созданием, редактированием, предпросмотром, публикацией и снятием с публикации; табличный и карточный виды для инвентаризации; опубликованные и неопубликованные видны сразу — кто делает, на каком этапе, можно ли вывести на экран; статус проекта можно контролировать, передавать и принимать; «сделать один экран» становится управляемым активом поставки</li>
  <li><strong>Центр шаблонов визуализации</strong>: Если каждый проект начинается с пустого холста, срок поставки неизбежно растягивается из‑за дизайна и интеграции. Зрелые шаблоны обзора кампуса, заводской ситуации, панели оборудования и т. п. накапливаются и переиспользуются; новый проект создаётся в один клик с последующей доработкой — для похожих сценариев реже начинают с нуля; PoC и копирование между проектами быстрее и единообразнее; «умеем один раз» превращается в «можем поставить много раз»</li>
  <li><strong>Управление ресурсами визуализации и источниками данных</strong>: Если иконки, фоны и видео хранятся отдельно в каждом проекте, а интерфейсы данных пишутся для каждого экрана, позже неизбежны конфликты стилей и расхождения полей. Библиотека ресурсов централизует визуальные активы; источники данных единообразно подключают устройства и бизнес-интерфейсы — один стиль и одна семантика данных для нескольких экранов; изменение в одном месте приносит пользу многим; меньше дублирования и споров о трактовке</li>
  <li><strong>Публикация визуализации и развёртывание сервисов</strong>: Большой экран, который нельзя вывести, по сути бесполезен. После подтверждения публикации проект можно связать с развёртыванием сервиса и вывести в командный центр, диспетчерскую или на внешнюю витрину; предпросмотр и боевой показ используют один и тот же проект — от «режима редактирования» к «режиму дежурства» есть явный выход; приёмка и ежедневное дежурство не зависят от временных ссылок и устных договорённостей</li>
  <li><strong>Управление SCADA</strong>: На промышленных и зданийных объектах страшат не цифры, а «непонятную технологию» — у счётчиков, клапанов и уровней в ёмкостях есть показания, но дежурный не сопоставляет их с трубопроводами и операциями, а аномалии приходится объяснять устно и угадывать. Платформа предоставляет Web-SCADA: точки измерений привязываются к технологическим схемам водозабора, панели линии, топологии заводской сети, мониторингу электрощита и т. п.; редактирование и предпросмотр в одном месте, после публикации — сразу на дежурство — «цифры» возвращаются на «схему», состояние технологии видно сразу; дежурство из «листания таблиц и догадок» переходит к анализу и действиям по технологической схеме</li>
  <li><strong>Мониторинг SCADA в реальном времени и ограниченное управление</strong>: Чистый списочный мониторинг «видит точку, но не видит процесс» — медленная локализация аномалий, сложная передача смены, обучение новичков только через наставника. В режиме эксплуатации SCADA ключевые точки анимированы на ёмкостях, клапанах, двигателях и выключателях; тренды и статусы обновляются на одном экране; при необходимости — ограниченные операции пуск/стоп и сброс прямо на схеме — новичок может начать по картинке, смены смотрят одну и ту же схему; аномалия сжимается от «найти точку» до «увидеть на схеме»; полевой контроль действительно включается в ежедневную эксплуатацию, передачу смены и масштабирование</li>

  <li><strong>Управление моделями продуктов</strong>: Самая дорогая часть внедрения IoT часто не покупка устройств, а повторная настройка карточки на каждый новый класс. Платформа берёт продукт как шаблон однотипных устройств — создание, запуск/остановка, поиск, виды таблица/карточки; сценарий, производитель и модель настраиваются один раз — дальнейшее расширение применяет шаблон продукта без заполнения с нуля на каждое устройство; одна карточка класса, многократное переиспользование, стоимость доступа сжимается из линейного роста в воспроизводимый актив</li>
  <li><strong>Многотипное моделирование продуктов</strong>: Когда одновременно есть прямые терминалы, краевые шлюзы, подчинённые устройства шлюза и видеоустройства, один общий путь доступа ломает топологию и протоколы. Продукты создаются по четырём формам — прямое подключение, шлюз, подчинённое устройство шлюза и видео — каждая морфология идёт своим путём — топология не смешивается, протоколы не кабелируются ошибочно, закладывается правильный скелет продукта для масштабного управления</li>
  <li><strong>Протокол доступа и аутентификация на уровне продукта</strong>: Отдельные договорённости о протоколе и auth на каждое устройство — очаг переделок интеграции. На уровне продукта один раз фиксируются протокол (MQTT / TCP / HTTP / Modbus-TCP / Modbus-RTU / OPC UA), формат данных, способ аутентификации и стратегия шифрования/дешифрования; подчинённые устройства наследуют тот же контракт — больше не согласовывать auth и формат кадр за кадром; норма доступа из «устной передачи» становится «наследуемым контрактом уровня продукта»</li>
  <li><strong>Доступ промышленного Ethernet Modbus-TCP</strong>: Для счётчиков, ПЛК, преобразователей и другого Ethernet-оборудования на площадке платформа предоставляет встроенный сбор Modbus-TCP — достаточно настроить параметры доступа и точки измерения на уровне продукта/устройства. Показания автоматически поступают в тень устройства и онлайн-статус; запись значений и downlink свойств связаны — единый контур с вещными моделями, правилами и оповещениями без отдельного ПО сбора данных.</li>
  <li><strong>Доступ полевой шины Modbus-RTU</strong>: Многие приборы на площадке всё ещё подключены по шине RS-485; если доступ возможен только через TCP-шлюз, стоимость и точки отказа удваиваются. Платформа поддерживает сбор Modbus-RTU по последовательному порту — в виртуальных и реальных сценариях — устройства на шине включаются в единое управление и uplink/downlink, закрывая пробел «Ethernet недоступен, последовательный порт не управляется».</li>
  <li><strong>Доступ промышленной взаимосвязи OPC UA</strong>: Для современных промышленных сценариев и взаимодействия с верхнеуровневыми системами платформа поддерживает клиент OPC UA и настройку подписки/чтения/записи — сложные модели устройств могут быть отображены в свойства вещной модели; uplink и downlink связаны с тенью устройства, цепочками правил и push-уведомлениями, включая активы OPC UA в AIoT-экосистему «видеть, управлять, связывать».</li>
  <li><strong>EDGE C# среда сбора на периферии</strong>: Независимо развёртываемый модуль сбора для промышленных площадок — подключаемые коллекторы C# для Modbus RTU, Modbus TCP, OPC UA и др.; локальный плановый сбор и разбор по конфигурации; MQTT-интеграция с DEVICE/<strong>iot-sink</strong> на облачной платформе. Соответствует роли GATEWAY в управлении устройствами (не отдельная страница устройств): агрегация на объекте, управление в облаке; uplink/downlink свойств шлюза/подустройств и push конфигурации покрыты; топология и passthrough событий/сервисов подустройств ещё развиваются. Упаковка для промышленных ПК Linux x86_64 / ARM64 и edge-шлюзов — замкнутый контур cloud-edge «точно на объекте, управляемо в облаке»</li>
  <li><strong>Определение свойств модели вещи</strong>: Если дашборды, правила и тревоги пишут каждый свои имена точек, позже они перестают понимать друг друга. Сначала фиксируются точки, которые можно отправлять и читать/писать; стандартные и пользовательские шаблоны; черновик, затем публикация — дашборды, правила и тревоги делят один набор полей; «что можно наблюдать» получает единую семантику, переделки из-за разных имён точек отсекаются в корне</li>
  <li><strong>Определение сервисов модели вещи</strong>: Если каждый старт/стоп или сброс порождает разовое API, плоскость управления фрагментируется. Вызываемые удалённо сервисы с входными/выходными параметрами оформляются контрактом; черновик, затем публикация — «что можно делать удалённо» заполняется по контракту, без стопки разовых интерфейсов; управляемость становится переиспользуемой и аудируемой</li>
  <li><strong>Определение событий модели вещи</strong>: Без предварительного соглашения о бизнес-событиях, которые устройство будет сообщать, язык тревог расходится. Сначала договариваются о типах событий; после публикации черновика они действуют единообразно — журналы событий и триггеры правил делят одну семантику; «что может произойти» имеет общий язык, тревоги не спорят друг с другом</li>
  <li><strong>Контроль публикации модели вещи</strong>: Прямой удар правки модели по онлайн-устройствам одним ложным жестом может ударить по всей партии терминалов. Изменения сначала в черновик; на сторону устройств — только после подтверждения и публикации — буфер перед воздействием; непроверенные правки не бьют по полевым онлайн-устройствам, риск ошибки заметно ниже</li>
  <li><strong>Адаптация протоколов скриптами</strong>: Самое трудное на объекте — не стандартный MQTT, а частные кадры вендоров и «чёрные ящики», отлаживаемые только локальным инструментом. Стандартные кадры работают из коробки; для частного протокола пишут кодирование/декодирование вверх/вниз с шаблонами, проверкой, мгновенной отладкой и горячей перезагрузкой при сохранении — интеграция из «менять прошивку / ждать вендора» в «настроить скрипт, горячий эффект»; разнородный legacy входит в единую модель вещи без смены прошивки</li>
  <li><strong>Руководство по доступу продукта</strong>: Если интеграция новичков держится на устных инструкциях экспертов на объекте, ритм поставки упирается в людей. В карточке продукта — параметры интеграции, аутентификация, сообщения и приёмка; следовать странице достаточно для приёмки — каждый продукт несёт стандартный playbook; меньше устной зависимости, PoC и приёмка быстрее и стабильнее</li>
  <li><strong>Обзор устройств продукта</strong>: Ops и приёмка часто спорят «сколько эта партия реально покрывает и какова онлайн-доля». Открыть продукт — список устройств и онлайн-статус — онлайн-доля и покрытие с одного взгляда; ops и приёмка ведут свои участки, границы ответственности ясны</li>
  <li><strong>Управление карточками устройств</strong>: Устройства, разбросанные по таблицам, чатам и полевой памяти, делают инвентаризацию и передачу неуправляемыми. Полный CRUD, поиск по продукту/идентификатору/онлайн-статусу, переключение таблица/карточки — разрозненные терминалы становятся searchable-реестром; инвентаризация, передача и расширение идут через одну точку входа</li>
  <li><strong>Онлайн- и статус активации</strong>: Проблемные машины тонут в «всех устройствах», дежурный может только слепо листать. Списки и детали сразу показывают соединение, активацию, время активации и последней онлайн — офлайн и неактивированные всплывают первыми; силы ops сначала на реально аномальных устройствах</li>
  <li><strong>Регистрация устройств по продукту</strong>: При расширении заново выбирать протокол и заполнять auth на каждое устройство — главный friction масштабируемого go-live. При создании привязка к продукту наследует протокол и сценарий — регистрация сразу вешает нужный шаблон; масштабирование клонированием продукта, без повторного выбора протокола и заполнения auth</li>
  <li><strong>Конфигурация промышленного сбора</strong>: Если счётчики и датчики ещё требуют отдельного инструмента сбора, на объекте живут две системы. При регистрации устройства промышленного сбора настраивают хост, точки и период — полевые точки архивируются один раз; не переключаться в другой инструмент сбора, промышленный сбор и управление платформы — в одном жесте</li>
  <li><strong>Базовый профиль устройства</strong>: Замена, разбор ответственности и сверка, опирающиеся на устное «кто это», рвут цепочку ответственности. Имя, идентификатор, SN, продукт, версия, IP и прочие поля «одно устройство — одна карточка» — открыть карточку и подтвердить личность; меньше устных подтверждений и полевых поисков</li>
  <li><strong>Руководство по доступу устройства</strong>: Если полевая интеграция всё ещё ищет толстые документы и экспертов, цикл go-live растягивается. По типу устройства — рекомендуемые команды, параметры интеграции, auth, сообщения и приёмка; команды копируются после правки параметров — интеграция из «искать в документах» в «скопировать команды для приёмки»; go-live и PoC плотнее</li>
  <li><strong>Реальное состояние выполнения</strong>: Если дежурный каждый раз входит на устройство и грызёт сырые кадры, чтобы понять норму точки, стоимость дежурства зашкаливает. Текущие значения свойств раскладываются по модели вещи; виды таблица/карточки и обновление — без входа на устройство и без сырых кадров одним взглядом судить, нормальны ли ключевые точки сейчас</li>
  <li><strong>Прогноз float-данных датчиков</strong>: Если ключевые точки смотрят только после факта по историческим кривым, аномалии часто видны лишь после выхода за предел. Платформа прогнозирует тренды float-свойств датчиков, превращая прошлые показания в опережающую траекторию — эксплуатация из «смотреть цифры после» в «видеть заранее», выигрывая время на реакцию</li>
  <li><strong>Пороги атрибутов рабочего состояния</strong>: Если границы здоровья живут в коде или устных договорённостях, смена модели или сценария всегда означает переделку. Настраивать верхние/нижние пороги атрибутов рабочего состояния по модели вещи — границы определяемы, переиспользуемы и детализируемы; «нормальный диапазон» устройства становится управляемым активом, а не разрозненным опытом</li>
  <li><strong>Пороговые оповещения и правила</strong>: Пороги без обнаружения и связки — лишь декорация. Выход точки за предел автоматически оповещает и может включаться в правила действий — «узнать при пересечении, управлять когда известно», замыкая границы здоровья в операционный контур</li>
  <li><strong>Один экран связанных подчинённых центрального устройства</strong>: Если здоровье подчинённых смотрят по одному устройству, осмотр и реакция на аномалии всегда отстают. С точки зрения центрального устройства — одним экраном обзор рабочего состояния связанных подчинённых — без переключения поштучно; осмотр на объекте и локализация аномалий заметно быстрее, чтобы сторона устройств действительно замыкала «видеть цифры, держать границы, поднимать тревогу и видеть картину целиком»</li>
  <li><strong>Сравнение тени устройства</strong>: Худшее в классической диагностике — не отличить «что хотели» от «что есть». Reported, desired и разница на одном экране, полный JSON сохраняется — диагностика из догадок в сравнение; совпадение желаемого и факта видно сразу</li>
  <li><strong>Отправка desired-свойств</strong>: Ехать на объект ради одного параметра — типичная растрата масштабируемого ops. Пакетно менять desired для записываемых свойств и отправлять в один клик; отслеживать processing/success/failure — удалённая настройка с квитанцией; не ехать ради параметра, меньше пустых выездов</li>
  <li><strong>Вызов сервисов модели вещи</strong>: Старт/стоп или сброс без подтверждения исполнения оставляют разбор только на устную сверку. Заполнить параметры опубликованных сервисов и вызвать; отслеживать квитанции — после приказа подтвердить исполнение; процесс становится аудируемым, из «сказали, что управляли» в «замкнутый цикл с квитанцией»</li>
  <li><strong>Очередь команд офлайн</strong>: При слабой сети или кратком офлайне пропавшие команды заставляют всё делать заново. Временный офлайн — команды сначала в desired-тень; после выхода в онлайн — автозабор или приём по протоколу — джиттер слабой сети не теряет намерение управления; при возврате — догонка, одна повторная операция меньше</li>
  <li><strong>Прокси-управление подчинёнными через шлюз</strong>: Если каждый краевой терминал обязан напрямую связываться с платформой, сложность доступа и управление сертификатами растут экспоненциально. Управление подчинёнными идёт через родительский шлюз — краевые терминалы телеуправляются без прямой связи; сложность доступа ниже, шлюз становится настоящей операционной плоскостью агрегации</li>
  <li><strong>Связанные камеры</strong>: Тревога датчика без вида площадки заставляет дежурного «слушать цифры и гадать». IoT-устройства могут привязывать камеры из каталога; точки измерения и видеоточки соответствуют — при аномалии сразу знать, какой поток открыть; из «одна цифра» в «найти картинку»</li>
  <li><strong>Мультиэкранный мониторинг и связка с ИИ</strong>: Ключевое отличие EasyAIoT от чистого IoT — чистый IoT «видит цифры без площадки», чистое видео «видит площадку без управления устройствами». В вызове функций — превью связанных камер 1/4/9 и запуск ИИ-анализа — менять параметры и отдавать команды, глядя на объект; «цифры» и «картинка» проверяются и отрабатываются на одном экране; меньше переключений систем, меньше пропусков, реальная ценность слияния AI + IoT</li>
  <li><strong>Журналы событий</strong>: Всплывающая тревога мелькает и исчезает — разбор потом держится на памяти и спорах. Info/warning/error агрегируются; фильтр по типу, имени и времени — разбор читает сырой поток событий; «что происходило на объекте» имеет доказательства, не только вспышку окна</li>
  <li><strong>Журналы команд</strong>: Худшее в интеграции — «кто что сказал»: дошла ли команда, приняло ли устройство. Processing/success/failure настроек свойств и вызовов сервисов оставляют полный след — конец устной сверки; цепочка команд проверяема и вменяема</li>
  <li><strong>Журналы устройств</strong>: Искать прошивку и бизнес-сбои, входя на устройство за локальными файлами, упирается в сеть и права на объекте. Многоуровневые логи стороны устройства стекаются в облако; поиск по ключевым словам и времени — локализовать аномалию в облаке, без повторного входа за локальными логами</li>
  <li><strong>Привязка подчинённых устройств шлюза</strong>: В промышленности и зданиях часто «один шлюз несёт десятки и сотни подчинённых»; устная топология делает расширение и изоляцию аварии неуправляемыми. Пакетная привязка/отвязка — кто на ком висит ясно; при расширении, замене шлюза или изоляции границы ответственности не размываются</li>
  <li><strong>Инвентарь возможностей Topic</strong>: Если R&D и интеграция держат разные контракты каналов, интеграция переделывается из-за расхождений. По устройству — каналы вверх/вниз: config, shadow, свойства, сервисы, события, OTA, синхронизация часов и др. — стыковка против одного каталога; меньше переделок из-за расхождений контрактов каналов</li>
  <li><strong>Управление OTA-пакетами</strong>: Копировать патчи и прошивки с флешки на каждое устройство делает масштабное обновление почти невозможным. Централизованная загрузка и архив ПО/прошивки с версией, скачиванием, правкой, удалением и двойным видом — патчи и прошивки в одном месте и переиспользуются; без копирования носителей, прошивка становится управляемым активом поставки</li>
  <li><strong>Стратегия OTA-обновления</strong>: Пропуск обновления оставляет дыры безопасности; хаотичные обновления — риски совместимости: дилемма масштабируемого ops. Пометка критических версий; режим принудительный или нет — срочные фиксы доходят, повседневные версии не скачут хаотично; риски пропусков и совместимости под контролем</li>
  <li><strong>Управление цепочками правил</strong>: Разрозненные правила связок, которые нельзя центрально включать/выключать, множат ложные срабатывания и спящие цепочки. Создание, запуск/остановка, пакетное удаление; управление список/карточки — центральный выключатель бизнес-связок; ненужные правила отключаются в любой момент, ложных срабатываний меньше</li>
  <li><strong>Визуальная оркестрация цепочек правил</strong>: Полевой бизнес меняется каждый день — пороги подкрутить, связки добавить — ждать жёсткой разработки всегда опаздывает на полшага. На цепочечном холсте связать поток данных, условия и downstream-действия по намерению — смена сценария укладывается drag-and-drop; без ожидания спринта, «что делать с данными после входа» конфигурирует бизнес</li>
  <li><strong>Импорт/экспорт правил</strong>: Зрелые правила, которые нельзя унести, заставляют каждый проект писать с нуля. Импорт/экспорт — миграция между средами и переиспользование между проектами уносятся с собой; зрелые правила оседают как воспроизводимый актив поставки</li>
  <li><strong>Конфигурация сообщений</strong>: Смена канала или аккаунта с правкой бизнес-кода блокирует ops за разработкой. Каналы уведомлений и базовые настройки сообщений ведутся централизованно — смена канала или аккаунта трогает только конфигурацию, не бизнес-код</li>
  <li><strong>Шаблоны сообщений</strong>: Импровизированные формулировки тревог ошибаются и расходятся. Email, SMS, Enterprise WeChat, DingTalk, Feishu, Webhook и др. — свои шаблоны — текст один раз, переиспользование везде; единые формулировки, меньше ошибок импровизированной сборки</li>
  <li><strong>Отправка сообщений</strong>: Самое точное обнаружение и самое полное событие стоят ноль, если застревают в системе в ожидании, пока кто-то откроет. Создавать push-задачи по каналам; сначала тест, затем старт — тревоги и бизнес-события приземляются в повседневные инструменты ответственных; не застревают в системе</li>
  <li><strong>История отправок</strong>: Без записи об отправке и доставке аудит и оптимизация — только догадки. Просмотр записей push по каналам — отправлено или нет, доставлено или нет, с доказательствами; аудит и оптимизация стратегии охвата имеют опору</li>
  <li><strong>Пользователи и группы уведомлений</strong>: Критические тревоги «всем подряд» создают усталость; нужные люди не получают — пропуски. Вести пользователей и группы для точного охвата по роли/смене — нужные люди получают; меньше усталости от «всем»; контур «восприятие — суждение — уведомление — реакция» реально замыкается до человека</li>
  <li><strong>TRANSFORM — многонаправленный бизнес-поток</strong>: Если оповещения, события устройств и бизнес-результаты остаются внутри EasyAIoT, стыковка MES / ERP / CRM / WMS всё ещё требует кастомных API на проект — сроки и переделки растут. TRANSFORM превращает «кому слать, по каким правилам, как свести поля, дошло ли» в настраиваемую способность: назначения, правила пересылки и шаблоны маппинга задаются один раз и переиспользуются; доставка мониторятся и просматривается — многосистемная интеграция из «кастомный API на партнёра» становится «подключить по контракту, принять по трейлу», и данные платформы реально входят в существующий бизнес-контур клиента</li>
</ul>

#### 📱 Мобильное APP

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Мультиканальный доступ</strong>: Доступ с телефона, мини-программы и App — эксплуатация и управление не привязаны к рабочему месту; действуйте на объекте в реальном времени</li>
  <li><strong>Единые возможности</strong>: Те же бизнес-функции, что и в PC-консоли; смена устройства без потери контроля</li>
  <li><strong>Управление устройствами</strong>: Единое управление всеми способами подключения; списки и каналы на виду, просмотр в один клик — будьте в курсе при обходе</li>
  <li><strong>Ретрансляция потоков</strong>: Создавайте и останавливайте пересылку в любой момент; следите за узлами и каналами; многоканальное сырое видео эффективно выводится на экран — даже вне рабочего места</li>
  <li><strong>Задачи алгоритмов</strong>: Запуск и остановка задач в реальном времени и по снимкам на ходу; результаты детекции без ожидания возвращения в офис</li>
  <li><strong>Центр тревог</strong>: Мгновенный поиск тревог; снимки и записи в один клик — проверка и реагирование в мобильном дежурстве</li>
  <li><strong>Управление моделями</strong>: Статус развёртывания на виду; прогресс всегда под контролем</li>
  <li><strong>Инференс моделей</strong>: Загрузите изображение на объекте и получите результат сразу — проверки без возвращения к PC</li>
  <li><strong>Обучение моделей</strong>: Следите за прогрессом в любой момент; удалённая остановка при необходимости — без лишних затрат вычислений</li>
  <li><strong>Личный кабинет</strong>: Аккаунт, арендатор и настройки в одном месте — удобно на всех устройствах</li>
  <li><strong>Плавный просмотр</strong>: Прямые трансляции и записи тревог воспроизводятся плавно на мобильном — низкая задержка, без рывков, комфортное дежурство</li>
  <li><strong>Непрерывная работа</strong>: Сессия поддерживается автоматически, меньше повторных входов — интеллектуальное управление облако-граница-устройство на телефонах и в мини-программах</li>
</ul>

#### 💻 Онлайн-IDE IDEA

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Разработка в браузере</strong>: Онлайн-IDE в стиле VS Code на code-server; по умолчанию клонируется полный репозиторий EasyAIoT — контрибьюторы правят код, проверяют модули и открывают PR без предварительной настройки локальной среды</li>
  <li><strong>Автономный портал и многопользовательский режим</strong>: Консоль операций на <code>:9300</code>, отделена от админки WEB; одно Docker-пространство на человека; пул портов 13338–13437 для одновременной работы; плавающий шар консоли открывает портал</li>
  <li><strong>Шесть языков, выровненных с хостом</strong>: Предустановлены <strong>JDK 21</strong>, Node 22, Python, Go, CMake/C++ и .NET 8 — чтение, лёгкие правки и модульные проверки WEB / DEVICE / AI / RUNTIME / EDGE</li>
  <li><strong>Совместное творчество с ИИ</strong>: Предустановлен GitHub Copilot (вход своим аккаунтом GitHub; платформа не хранит ключи); без подписки Copilot — свой OpenAI-совместимый API-ключ через Continue; панель инструментов открывает HARNESS в split — перетащите файлы для авто <code>@</code> при правках</li>
  <li><strong>Локальная публикация</strong>: Предлагает модули по diff рабочей области, сборка и замена запущенных контейнеров на хосте одним кликом — обновите инстанс для приёмки, короче цикл «правил → увидел»</li>
  <li><strong>OAuth и возврат простоя</strong>: Вход Gitee / GitHub (можно обязать), одна зона на аккаунт; автоостанов после 8 ч простоя по умолчанию; heartbeat и открытие IDE обновляют активность, чтобы не крутить вычисления вхолостую</li>
  <li><strong>Цикл вклада</strong>: Привязать свой fork → ветка → правки → push в fork → PR в официальный репозиторий</li>
</ul>

#### 🤖 AI-ассистент HARNESS

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0 12px;">
Много модулей и длинные цепочки — проверка здоровья, вопросы об архитектуре и поиск конфигов часто требуют документации и SSH. HARNESS объединяет знания платформы и живые пробы в <strong>разговорного ассистента</strong>: спрашивайте и проверяйте из правого нижнего угла любой бизнес-страницы — короче цикл устранения неполадок и PoC, меньше зависимости от вендора и устных знаний.
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Спросил — проверил</strong>: Agent вызывает Tools платформы для Gateway / видео / AI и указывает конфиг и исходники — SSH + compose в одном диалоге</li>
  <li><strong>Знает онтологию</strong>: встроенный <code>HARNESS/ontology/AGENTS.md</code> и workspace всего репозитория — архитектура, порты, API и соглашения об установке в одном месте</li>
  <li><strong>Чат на странице</strong>: плавающий drawer iframe — без перехода и потери контекста на экранах тревог/устройств; полноэкранный «AI-ассистент» или новое окно</li>
  <li><strong>Совместная работа IDEA в split</strong>: панель инструментов открывает AI-ассистента справа — редактор и Agent рядом; deep-link <code>?file=путь&harness=1</code></li>
  <li><strong>Перетащить для авто @</strong>: файлы из проводника на панель ассистента автоматически становятся контекстом чата</li>
  <li><strong>Двусторонний переход</strong>: Agent может сгенерировать ссылку портала через <code>easyaiot_open_in_idea</code> — из Q&amp;A обратно в полный IDE; IDEA — код и PR, HARNESS — архитектура и здоровье</li>
  <li><strong>MCP + Cursor Skill</strong>: те же возможности <code>easyaiot_*</code> через MCP в Cursor и другие IDE — что можно спросить в консоли, можно вызвать в dev; Skills переиспользуются между проектами</li>
  <li><strong>Готов во всех профилях</strong>: Sidecar <a href="https://github.com/deepseek-ai/deepseek-harness" style="color: #3498db; text-decoration: none; font-weight: 600;">DeepSeek Harness</a> (<code>:3080</code>); по умолчанию в <code>mini / standard / full</code> (<code>EASYAIOT_ENABLE_HARNESS=0</code> для отключения); DeepSeek / OpenAI-совместимые endpoints; ключ в <code>harness.env</code> или UI</li>
  <li><strong>Безопасность</strong>: экспериментальный модуль; upstream <code>dsh</code> в Developer Preview; ограничьте доступ в prod и настройте одобрение записи/Shell; не коммитьте API Keys в Git</li>
</ul>

### 📦 Встроенные модели ИИ

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Платформа готова к использованию из коробки и включает несколько предобученных моделей для охранного видеонаблюдения, промышленных объектов, умного транспорта и других сценариев. Выбирайте их напрямую в задачах алгоритмов для быстрого развёртывания и инференса — без обучения с нуля для типовых задач визуального обнаружения.
</p>

| Название модели | Формат инференса | Базовая модель | Возможности |
| :-- | :--: | :--: | :-- |
| Модель каски | ONNX | YOLOv8 | Определение, носят ли работники защитные каски |
| Модель сна на посту | PyTorch | YOLOv8 | Выявление сна на посту, ухода с поста и другого аномального поведения |
| Модель обнаружения людей | PyTorch | YOLOv8 | Универсальное обнаружение людей для идентификации и локализации в кадре |
| Модель номерных знаков | ONNX | YOLOv8 | Распознавание информации с автомобильных номеров |
| Модель светоотражающего жилета | PyTorch | YOLOv8 | Определение, носят ли работники светоотражающие жилеты |
| Модель пламени | PyTorch | YOLOv8 | Обнаружение открытого пламени и пожарных рисков |
| Модель курения | PyTorch | YOLOv8 | Выявление курения |
| Модель телефонных звонков | ONNX | YOLOv8 | Выявление звонков и использования мобильного телефона |
| Модель затопления дороги | ONNX | YOLOv8 | Обнаружение скопления воды на дороге и подтопления |
| Модель маски | ONNX | YOLOv8 | Определение правильного ношения масок |
| Модель обнаружения падений | ONNX | YOLOv8 | Выявление падений и других аномальных поз |
| Модель обнаружения лиц | ONNX | YOLOv8 | Определение положения лиц в кадре для поддержки распознавания лиц |

### 💡 Техническая философия

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Мы считаем, что ни один язык программирования не может быть хорош во всём. EasyAIoT использует шесть языков программирования в смешанном режиме по сценариям: Java — архитектура платформы, Python — алгоритмы ИИ, C++ — видеоисполнение, Go — протокольный шлюз, TypeScript — интерфейс управления, C# — промышленный сбор на периферии — облачное управление, алгоритмы, исполнение, протоколы, интерфейс и полевой сбор каждый на своём месте, формируя полный технологический контур cloud-edge-device.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Java сильна в построении стабильной и надёжной архитектуры платформы, но плохо подходит для сетевого программирования и разработки ИИ; Python сильна в сетевом программировании и алгоритмах ИИ, но на высокой плотности каналов и низкой задержке упирается в GIL и накладные расходы процессов; C++ сильна в высокопроизводительном выполнении задач, но плохо подходит для архитектуры платформы и оркестрации алгоритмов; Go сильна в высоконагруженном сетевом программировании и реализации протоколов, но плохо подходит для плоскости управления платформой и алгоритмов ИИ; TypeScript сильна в сложных фронтенд-взаимодействиях и типобезопасных инженерных интерфейсах, но плохо подходит для высокопроизводительных бэкенд-вычислений и инференса ИИ; C# сильна в сборе промышленных протоколов и оркестрации edge-runtime, с сильной типизацией, обеспечивающей надёжный маппинг точек и разбор протоколов, <code>async/await</code> поддерживает параллельный опрос множества устройств, кроссплатформенная публикация .NET адаптирована к промышленным площадкам x86/ARM, зрелая экосистема промышленной автоматизации/SCADA и быстрый онбординг интеграторов, но плохо подходит для ядра облачной платформы и алгоритмов ИИ. Шесть языков каждый играет на своих сильных сторонах и избегает слабых — сложно реализовать, но чрезвычайно удобно использовать.
</p>

![EasyAIoT平台架构.jpg](.image/iframe2.jpg)

### 🔄 Поток данных между модулями

<img src=".image/iframe3.jpg" alt="EasyAIoT平台架构" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

### 🤖 Технология аннотирования с нулевым образцом

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Инновационно построена система аннотирования с нулевым образцом на основе больших моделей (в идеальном состоянии полностью устраняя ручной процесс аннотирования, реализуя автоматизацию процесса разметки). Эта технология использует большие модели для генерации исходных данных и завершает автоматическое аннотирование с помощью техник промптов, затем обеспечивает качество данных через проверку человеком (опционально), после чего обучает начальную малую модель. Эта малая модель через непрерывные итерации и самооптимизацию достигает совместной эволюции эффективности аннотирования и точности модели, в конечном итоге продвигая производительность системы вверх.
</p>

<img src=".image/iframe4.jpg" alt="EasyAIoT平台架构" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

### 🏗️ Особенности архитектуры проекта

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
EasyAIoT на самом деле не один проект, а несколько независимо развёртываемых подпроектов (WEB, DEVICE, EDGE, VIDEO, RTC, AI и др.).
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
В чем преимущество? Если вы находитесь на ограниченном устройстве (например, RK3588), вы можете просто взять один из этих проектов и развернуть его независимо. Поэтому, хотя этот проект выглядит как облачная платформа, на самом деле он также может быть пограничной платформой.
</p>

<div style="margin: 30px 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;">

<p style="font-size: 16px; line-height: 1.8; margin: 0; font-weight: 500;">
🌟 Настоящий open-source — это непросто. Если этот проект помог вам, пожалуйста, поставьте звезду (Star), прежде чем уйти, это будет для меня самой большой поддержкой!<br>
<small style="font-size: 14px; opacity: 0.9;">(В эпоху, когда псевдо-open-source повсюду, этот проект — исключение, работающий на чистом энтузиазме)</small>
</p>

</div>

### 🌍 Поддержка локализации

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT активно поддерживает стратегию локализации, всесторонне поддерживает локальное оборудование и операционные системы, предоставляя пользователям безопасные и контролируемые решения AIoT. Уже поддерживаются отечественные ОС, такие как <strong>Kylin (麒麟) / openEuler (欧拉)</strong>, включая развёртывание и поставку PANEL.
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🖥️ Поддержка на стороне сервера</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Полная совместимость с процессорами архитектуры x86 от Hygon</li>
  <li>Поддержка локальных серверных аппаратных платформ</li>
  <li>Предоставление целевых решений по оптимизации производительности</li>
  <li>Обеспечение стабильной работы корпоративных приложений</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">📱 Поддержка на пограничной стороне</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Обычные платы разработки могут выполнять интеллектуальное дежурство прямо на объекте</li>
  <li><strong>EDGE</strong> C# сбор на периферии можно развернуть независимо на промышленных ПК и площадках RS485</li>
  <li>Лёгкое полевое развёртывание — не нужно на каждой площадке наращивать тяжёлое хранилище</li>
  <li>Интеллект «из коробки», сокращая срок вывода edge-узлов в эксплуатацию</li>
  <li>Вычисления масштабируются по точкам, оповещения и доказательства автоматически агрегируются в облако</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🖱️ Поддержка операционных систем</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Совместимость с <strong>Kylin (麒麟) / openEuler (欧拉)</strong></li>
  <li>Поддержка локализованных дистрибутивов Linux, таких как Founder</li>
  <li>Адаптация к основным локализованным ОС, таким как Tongxin UOS</li>
  <li>Предоставление полных локализованных решений по развертыванию</li>
</ul>
</div>

</div>

## 🎯 Применимые сценарии

<img src=".image/适用场景.png" alt="适用场景" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

## 🧩 Структура проекта

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT включает основные модули WEB, APP, DEVICE, EDGE, SENTINEL, VIDEO, RTC, AI, RUNTIME, POST, VISUALIZE, TRANSFORM, PANEL, IDEA, HARNESS и SITE, а также COMPILE для мультиплатформенной упаковки и поставки:
</p>

<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50; width: 20%;">Модуль</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50;">Описание</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>SITE модуль</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Официальная точка входа</strong>: Отдельный официальный сайт для посетителей, интеграторов и заказчиков — ясно объяснить ценность «облако — край — устройство», затем вести к загрузке и развёртыванию</li>
    <li><strong>Короче путь к пониманию</strong>: Возможности, четыре уровня оборудования, установщики и документация на одном сайте — меньше поисков по репозиторию и устных уточнений</li>
    <li><strong>Поддержка выбора уровня</strong>: edge / mini / standard / full для лёгкого standalone, edge-боксов, AI-камер и full-stack комплексов — выбрать подходящий уровень с первого раза</li>
    <li><strong>От интереса к установке</strong>: Сайт, демо, открытые репозитории и Releases образуют замкнутый цикл — понять → попробовать → скачать → установить</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>WEB модуль</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Единый интерфейс управления</strong>: Frontend с согласованным UX</li>
    <li><strong>Мастер подключения</strong>: IPC / NVR / GB28181 / RTC; ONVIF, сканирование подсетей, RTSP, DJI live, P2P потребительских камер</li>
    <li><strong>Доступ RTC</strong>: «Подключить RTC-камеру» для <strong>Tapo / Tuya / Ring / Nest / Xiaomi / Wyze / DoorBird / GoPro / Roborock</strong>; OAuth через WebUI go2rtc</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>APP модуль</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Мультиканальный доступ</strong>: Одна разработка — телефон, мини-программа и App</li>
    <li><strong>Единые возможности</strong>: Те же функции, что и PC-консоль, с переключением арендаторов</li>
    <li><strong>Управление устройствами</strong>: Прямые камеры, GB28181, NVR и RTC потребительские камеры в едином управлении; статус онлайн, каналы и предпросмотр в один клик</li>
    <li><strong>Ретрансляция потоков</strong>: Создание/запуск/остановка задач, статус узлов и многоканальный просмотр; переключение высокопроизводительного / совместимого режима по площадке</li>
    <li><strong>Алгоритмические задачи</strong>: Список задач в реальном времени/снимков, управление запуском/остановкой и статистика детекции/кадров</li>
    <li><strong>Центр тревог</strong>: Поиск тревог, предпросмотр снимков, VOD-воспроизведение записей тревог</li>
    <li><strong>Модели и ИИ</strong>: Список и статус развёртывания, мобильная рабочая станция инференса, мониторинг и остановка обучения</li>
    <li><strong>Профиль</strong>: Личные данные, безопасность аккаунта, FAQ, обратная связь и настройки приложения</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Модуль ANDROID / IOS / HARMONYOS</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Один фронтенд, три нативные оболочки</strong>: страницы uni-app из APP упаковываются в устанавливаемые приложения Android (офлайн-рантайм DCloud + Gradle → APK), iOS (оболочка WKWebView + xcodebuild → .app / .ipa) и HarmonyOS (оболочка ArkWeb + hvigor → HAP) — одна бизнес-логика на всех массовых ОС телефонов</li>
    <li><strong>Сборка одной командой</strong>: <code>make-apk.sh</code> / <code>make-ipa.sh</code> / <code>make-hap.sh</code> с проверкой согласованности версий; окружения prod / test / dev собирают независимые артефакты</li>
    <li><strong>Единое управление</strong>: <code>.scripts/docker/mobile.sh</code> отвечает за status / build / bump / artifacts / clean; <code>bump</code> за раз выравнивает пять полей версии, а при расхождении сборка отклоняется</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>DEVICE модуль</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Управление устройствами</strong>: Регистрация устройств, аутентификация, мониторинг состояния, управление жизненным циклом.</li>
    <li><strong>Управление продуктами</strong>: Определение продукта, управление моделями вещей, конфигурация продукта.</li>
    <li><strong>Поддержка протоколов</strong>: MQTT, TCP, HTTP, Modbus-TCP, Modbus-RTU, OPC UA и другие протоколы IoT и промышленные протоколы.</li>
    <li><strong>Аутентификация устройств</strong>: Динамическая регистрация устройств, проверка подлинности, безопасное подключение.</li>
    <li><strong>Движок правил</strong>: Правила маршрутизации данных, маршрутизация сообщений, преобразование данных.</li>
    <li><strong>Сбор данных</strong>: Сбор данных с устройств, хранение, запрос и анализ.</li>
    <li><strong>Оркестрация узлов</strong>: Управление вычислительными/медиа-узлами, проверка связности, планирование рабочих нагрузок и распределение пула медиа-узлов.</li>
    <li><strong>Бэкенд визуализации</strong>: Единообразное управление проектами больших экранов/SCADA, шаблонами, ресурсами, источниками данных и развёртыванием сервисов — метаданные проектов и публикация для редактора VISUALIZE и Web-SCADA.</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Модуль EDGE</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Почему C#</strong>: Сильнотипированный маппинг точек, асинхронный параллельный опрос множества устройств, стабильность 7×24, кроссплатформенная self-contained публикация Linux x86/ARM — зрелая промышленная экосистема, быстрый онбординг интеграторов</li>
    <li><strong>C# среда сбора на периферии</strong>: Независимо развёртываемый сервис сбора на периферии — подключаемые коллекторы + локальное планирование + разбор по конфигурации</li>
    <li><strong>Мультипротокольные коллекторы</strong>: Встроенные коллекторы Modbus RTU (RS485/serial), Modbus TCP, OPC UA; расширение через плагины <code>ICollector</code> по заданиям</li>
    <li><strong>MQTT cloud-edge интеграция</strong>: подключается как GATEWAY управления устройствами — отчёт свойств, прокси-свойства подустройств, push конфигурации из облака (<code>config/downstream/push</code>) и downlink записи свойств — интеграция с DEVICE/<strong>iot-sink</strong>; данные в том же управлении устройствами, дополняет облачный промышленный опрос (платформа напрямую достигает полевых устройств) — EDGE подходит для изоляции OT и площадок RS-485</li>
    <li><strong>Двойной канал конфигурации</strong>: Локальный <code>device-jobs.json</code> и облачный MQTT push конфигурации оба управляют заданиями сбора</li>
    <li><strong>Linux-упаковка</strong>: <code>pack_linux.sh</code> создаёт автономные пакеты развёртывания x86_64 / ARM64 для промышленных ПК и edge-шлюзов</li>
    <li><strong>Готовая интеграция</strong>: Встроенная E2E-демо проверяет сбор → MQTT-аплинк → облачное сохранение; интеграция с облачной платформой включена</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>SENTINEL модуль</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Часовой бизнес-готовности</strong>: Идёт с каждым планируемым узлом и непрерывно проверяет, может ли машина реально взять отмеченные нагрузки</li>
    <li><strong>Мониторинг сразу после подключения</strong>: Автопроверка после ввода — приёмка готовности в день расширения</li>
    <li><strong>Сводка планируемой ёмкости</strong>: В консоли видно «может ли узел нести этот бизнес» — назначение по реальной способности</li>
    <li><strong>Самообслуживаемое дополнение</strong>: Запрос дополнения среды при пробелах — меньше установок на объекте</li>
    <li><strong>Офлайн-дружественное расширение</strong>: Офлайн-подключение и синхронизация среды без публичного интернета</li>
    <li><strong>Единый язык поставки</strong>: Здоровье компонентов и планируемые функции на одном экране</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>VIDEO модуль</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Обработка потокового мультимедиа</strong>: Поддерживает обработку и передачу потоков RTSP/RTMP в реальном времени.</li>
    <li><strong>Многопротокольный доступ</strong>: GB28181, ONVIF, NVR, DJI FlightHub live и RTC потребительские камеры</li>
    <li><strong>API интеграции RTC</strong>: <code>/register/device/rtc-live</code> — регистрация go2rtc и устройства; автоочистка при удалении</li>
    <li><strong>Управление алгоритмическими задачами</strong>: Realtime / snap / patrol; по умолчанию высокопроизводительный путь с кадрами суждения; режим совместимости по площадке</li>
    <li><strong>Оркестрация пересылки потоков</strong>: Многоканальный сырой вывод на экран по умолчанию высокопроизводительный; особые среды — совместимость; старт/стоп и политики следуют автоматически, меньше ручных правок</li>
    <li><strong>Экстракторы кадров и сортировщики</strong>: Поддерживает гибкие стратегии извлечения кадров и механизмы сортировки результатов. Каждая алгоритмическая задача может быть связана с независимым экстрактором кадров и сортировщиком.</li>
    <li><strong>Периоды охраны</strong>: Поддерживает конфигурацию по расписанию для полного и полурежимов охраны.</li>
    <li><strong>Оркестрация vs исполнение</strong>: VIDEO отвечает за оркестрацию устройств, сырой просмотр, архив оповещений и старт/стоп; тяжёлую работу берёт <strong>RUNTIME</strong> (инференс и высокопроизводительный forward) — «управлять» и «быстро» разделены, чтобы каналы и задержка не упирались в Python-оркестрацию</li>
    <li><strong>Связка с суждением POST</strong>: алгоритмические задачи настраивают правила постобработки — детекции входят в стандартное оповещение только после кастомного суждения; смена правил без остановки анализа</li>
    <li><strong>Превью приёмки</strong>: Сырое и суждение рядом — быстрее проверить задержку и качество разметки на объекте</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>RTC модуль</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>go2rtc</strong>: На базе <a href="https://github.com/AlexxIT/go2rtc">go2rtc</a>; vendor через install-скрипт</li>
    <li><strong>P2P-мост девяти брендов</strong>: Tapo, Tuya, Ring, Nest, Xiaomi, Wyze, DoorBird, GoPro, Roborock</li>
    <li><strong>Единый API управления</strong>: Реестр платформ, построение URL, REST-прокси go2rtc; порты 6100 / 1984 / 8554</li>
    <li><strong>Полная цепочка VIDEO</strong>: P2P → RTSP → SRS → Web + ИИ</li>
    <li><strong>Docker all-in-one</strong>: go2rtc + Python-сервис управления; host network для P2P LAN</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>AI модуль</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Интеллектуальный анализ</strong>: Отвечает за анализ видео и выполнение алгоритмов ИИ.</li>
    <li><strong>Кластер служб моделей</strong>: Поддерживает распределенный вывод моделей, реализует балансировку нагрузки и высокую доступность.</li>
    <li><strong>Вывод в реальном времени</strong>: Предоставляет возможности интеллектуального анализа в реальном времени с откликом на уровне миллисекунд.</li>
    <li><strong>Управление моделями</strong>: Поддерживает развертывание моделей, управление версиями и планирование нескольких экземпляров.</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>RUNTIME модуль</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
    <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Высокопроизводительное нативное исполнение</strong>: Один бинарник ведёт pull, декодирование, ONNX-инференс, callback оповещений/heartbeat и push с рамками; по умолчанию <code>executor=cpp</code> — больше каналов на бокс, ниже задержка, легче ресурсы, чем у Python</li>
    <li><strong>Четыре полевые формы</strong>: Realtime-наблюдение, плановый снимок, ротационный патруль и сырой-only forward — выбирать по бизнесу, чтобы «просто смотреть» не платило полную цену ИИ</li>
    <li><strong>Сырое + суждение</strong>: Realtime по умолчанию отдаёт поток детекции с рамками отдельно от сырого превью VIDEO — пути не отбирают полосу друг у друга</li>
    <li><strong>Экономичный многоканальный сырой вывод</strong>: Пересылка по умолчанию идёт по высокопроизводительного пути, чтобы на NVR «много каналов смотреть сырое, мало — гонять ИИ»</li>
    <li><strong>Оповещения и статус в центр</strong>: Оповещения и состояние исполнения агрегируются в VIDEO для хранения и уведомлений; на узле не копятся бизнес-данные</li>
    <li><strong>Сохранять realtime под нагрузкой</strong>: При нехватке compute приоритет текущей картинке и свежести оповещений — избегать «чем загруженнее, тем больше пропусков»</li>
    <li><strong>Ускорение предпочтительно, fallback без остановки</strong>: Есть ускоритель — использовать; нет — автоматически продолжать; задачи не рвутся</li>
    <li><strong>Раздача в один клик</strong>: WEB «раздача бизнес-runtime» или скрипты установки пакетом; установка VIDEO на центре автоматически монтирует локальный исполнитель</li>
    <li><strong>Событийная плоскость MQTT</strong>: Оповещения/снимки/пост-обработка через шину algo EMQX; <strong>iot-sink</strong> сохраняет, архивирует и обогащает уведомления</li>
    <li><strong>Управляющая плоскость HTTP heartbeat</strong>: Живучесть задач сообщается в VIDEO; старт/стоп и таблица задач управляются VIDEO</li>
    <li><strong>Корень медиа NFS</strong>: Изображения оповещений и DVR SRS пишутся в <strong>общий NFS media root</strong> (<code>EASYAIOT_MEDIA_ROOT</code>, по умолчанию <code>/mnt/easyaiot-media</code>; без sudo — <code>$HOME/easyaiot/media</code>); MQTT несёт только пути; <strong>iot-sink</strong> читает диск и архивирует в MinIO</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>POST модуль</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Кастомное суждение</strong>: независимое бизнес-решение поверх детекции — из «обвёл цель» в «нужно ли оповещать и по какому стандарту»</li>
    <li><strong>Правила по задаче</strong>: фильтр зон, пропуск, бизнес-скрипты и отраслевые плагины в цепочки для строек, кампусов, транспорта</li>
    <li><strong>Меньше ложных тревог, готово к приёмке</strong>: вне зоны без залива экрана; пробный прогон правил до запуска</li>
    <li><strong>Смена стандарта без остановки анализа</strong>: сохранение правил на работающей задаче действует сразу</li>
    <li><strong>Восприятие и суждение разделены</strong>: анализ видео продолжается; бизнес-логика расширяется; отраслевые возможности подключаются</li>
    <li><strong>Встроенные плагины</strong>: <code>line_cross</code> пересечение линии, <code>region_enter_exit</code> вход/выход из зоны, <code>dwell_timer</code> таймаут пребывания, <code>headcount_gate</code> порог численности — выбор в правилах постобработки алгоритмической задачи без регистрации; пересечение линии, вход/выход и пребывание требуют трекинга целей (<code>track_id</code>)</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>VISUALIZE модуль</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Редактор больших экранов drag-and-drop</strong>: Высокопроизводительный low-code редактор визуализации, сфокусированный на редактировании холста и предпросмотре.</li>
    <li><strong>Интеграция с WEB</strong>: Создание проектов, шаблоны, ресурсы, источники данных, публикация и вывод выполняются в меню «Визуализация» консоли администрирования; «Открыть редактор» переходит в этот модуль для работы на холсте.</li>
    <li><strong>Поставка больших экранов</strong>: Диаграммы, показатели и компоновка настраиваются перетаскиванием; компоненты подключаются к источникам данных платформы и IoT-точкам — быстрое создание экранов ситуации кампуса, KPI линии, эксплуатации оборудования, энергопотребления и т. п.</li>
    <li><strong>Чёткое разделение с SCADA</strong>: Большие экраны (dashboard) редактируются в этом модуле; технологическая SCADA — в Web-SCADA; метаданные проектов единообразно управляются бэкендом визуализации модуля DEVICE.</li>
    <li><strong>Форма развёртывания</strong>: Вместе с APP относится к возможностям full-версии; mini / standard можно пропустить по полевому оборудованию, уменьшая объём edge-развёртывания</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Модуль TRANSFORM</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Многонаправленный бизнес-поток</strong>: Доставляет оповещения, события устройств и бизнес-результаты во внешние MES / ERP / CRM / WMS по контракту, закрывая «последнюю милю» от «данные есть на платформе» до «бизнес-системы их используют»</li>
    <li><strong>Настраиваемая интеграция</strong>: Назначения, правила пересылки и маппинг полей настраиваются один раз и переиспользуются — меньше «кастомных API под каждого клиента»</li>
    <li><strong>Проверяемая доставка</strong>: Кластеры исполнения и трейлы доставки мониторятся и просматриваются — приёмка отвечает «дошло ли, где застряло», меньше устных сверок</li>
    <li><strong>Горизонтальное масштабирование</strong>: При росте трафика расширяйте потребление и доставку по бизнес-контракту — параллельная стыковка линий, заводов и систем</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Модуль PANEL</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Точка поставки и дежурства</strong>: Независимо от бизнес-консоли: установить, сдать и держать в день прибытия — короче приёмка, меньше стоимость присутствия и удалённой поддержки</li>
    <li><strong>Замкнутый цикл в тот же день</strong>: Установка по уровню через UI, прогресс и результат видны сразу; поднять и сдать комплекс ещё до готовности бизнес-консоли</li>
    <li><strong>Самостоятельная диагностика</strong>: Здоровье контейнеров, уровень ресурсов, логи задач и готовность образов с первого взгляда — типовые старт/стоп, pull и очистка кэша без ожидания команд разработчиков</li>
    <li><strong>Переиспользование на многих площадках</strong>: Одна точка для многих комплексов и машинных залов — PoC и серийная поставка в одном каноне</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Модуль IDEA</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Облачная IDE сообщества</strong>: Откройте рабочее пространство VS Code в браузере, по умолчанию полный репозиторий; одно Docker-пространство на человека, локальная публикация и возврат простоя — вклад в open source из «сначала настроить среду» в «открыл и правишь»</li>
    <li><strong>AI-ассистент в split</strong>: панель инструментов открывает HARNESS справа; перетащить для авто <code>@</code>; deep-link <code>?file=&harness=1</code></li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Модуль HARNESS</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Разговорный ассистент</strong>: здоровье, архитектура, локализация проблем — короче устранение неполадок и PoC, меньше зависимости от вендора</li>
    <li><strong>Плавающий drawer на странице</strong>: чат без ухода с бизнес-страниц; по умолчанию в <code>mini / standard / full</code></li>
    <li><strong>Связка IDEA в split</strong>: ассистент справа от редактора; drag-<code>@</code>, deep links и двусторонний переход</li>
    <li><strong>MCP / Skill</strong>: консоль и IDE делят семантику платформы; Skills переиспользуются между проектами</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Упаковка COMPILE</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Мультиплатформенные артефакты</strong>: Собирать PANEL и смежные возможности в пакеты/бинари для Ubuntu / Debian, CentOS / RHEL <strong>7–9</strong> (x86 + <strong>CentOS ARM</strong>, пакеты el7/el8/el9), Windows, macOS и ARM / <strong>Kylin (麒麟) / openEuler (欧拉)</strong> — клиент ставит без компиляции с исходников на площадке</li>
    <li><strong>Короче цепочка поставки</strong>: Интегратор берёт пакет под целевую ОС для развёртывания и обновления — единые пути install/start/stop/uninstall снижают разброс между ОС</li>
    <li><strong>В связке с PANEL</strong>: Сборки сразу дают точку полевой эксплуатации — «упаковать» и «поставить и держать по прибытии» на одной цепочке поставки</li>
  </ul>
</td>
</tr>
</table>

## 🖥️ Преимущества кроссплатформенного развертывания

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT поддерживает развертывание в трех основных операционных системах: Linux, Mac, Windows, предоставляя гибкие и удобные решения развертывания для пользователей в различных средах; <strong>COMPILE</strong> выпускает пакеты и бинари под целевую ОС, а <strong>PANEL</strong> закрывает установку на площадке и повседневное дежурство:
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🐧 Преимущества развертывания на Linux</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Подходит для производственных сред, стабилен, надежен, низкое потребление ресурсов.</li>
  <li>Поддерживает развертывание в контейнерах Docker, запуск всех служб одной кнопкой.</li>
  <li>Идеально адаптирован для серверов, пограничных вычислительных устройств (таких как RK3588 и другие устройства с архитектурой ARM).</li>
  <li>Предоставляет полные скрипты автоматической установки, упрощающие процесс развертывания.</li>
  <li>Поддержка серверных дистрибутивов: Ubuntu, CentOS/RHEL <strong>7–9</strong> (вкл. <strong>CentOS ARM</strong>), <strong>Kylin (麒麟) / openEuler (欧拉)</strong></li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🍎 Преимущества развертывания на Mac</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Подходит для сред разработки и тестирования, глубоко интегрирован с macOS.</li>
  <li>Поддерживает локальную разработку и отладку, быстрое подтверждение функциональности.</li>
  <li>Предоставляет удобные скрипты установки, поддерживает менеджеры пакетов, такие как Homebrew.</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🪟 Преимущества развертывания на Windows</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Подходит для сред Windows Server, снижает затраты на обучение.</li>
  <li>Поддерживает автоматизированные скрипты PowerShell, упрощает операции развертывания.</li>
  <li>Совместим с Windows Server и настольными версиями Windows.</li>
  <li>Предоставляет графические мастера установки, удобные для пользователя.</li>
</ul>
</div>

</div>


<p style="font-size: 14px; line-height: 1.8; color: #2c3e50; font-weight: 500; margin: 20px 0; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #3498db; border-radius: 4px;">
<strong>Единообразный опыт</strong>: Независимо от выбора операционной системы, EasyAIoT предоставляет согласованные скрипты установки и документацию по развертыванию, обеспечивая единообразие опыта кроссплатформенного развертывания.
</p>

## ☁️ EasyAIoT = AI + IoT = Объединенное решение "Облако-Край-Устройство"

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Поддерживает тысячи вертикальных сценариев, поддерживает кастомизацию моделей ИИ и разработку алгоритмов ИИ, глубокая интеграция.
</p>

<div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3498db;">
<h3 style="color: #2c3e50; margin-top: 0;">Расширение возможностей интеллектуального зрения всего: EasyAIoT</h3>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
Создает эффективную сеть подключения и управления устройствами Интернета вещей (особенно огромным количеством камер). Мы глубоко интегрируем технологии передачи потокового мультимедиа в реальном времени с передовым искусственным интеллектом (ИИ), создавая ядро единого сервиса. Это решение не только обеспечивает взаимодействие разнородных устройств, но и глубоко интегрирует видеопотоки высокой четкости с мощным движком анализа ИИ, наделяя системы видеонаблюдения "интеллектуальным зрением" — точно реализуя распознавание лиц, анализ аномального поведения, контроль над рискованными лицами и обнаружение вторжений на периметре.
</p>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
Платформа поддерживает задачи алгоритмов реального времени, захвата и патрулирования: все три могут по умолчанию использовать <strong>высокоскоростной слой исполнения RUNTIME</strong> (<code>executor=cpp</code>) — нативный бинарник для долгого pull, декодирования, YOLO-инференса и возврата результатов; realtime с <strong>push AI-потока с рамками по умолчанию</strong>; snap по Cron; патруль с многопотоковым round-robin; пересылка тоже может идти тем же высокопроизводительным путём для экономичной сырой видеостены. По сравнению с Python-бэкендом совместимости RUNTIME лучше держит высокую плотность каналов и низкую задержку. Оповещения и heartbeat возвращаются в VIDEO. Управление алгоритмическими задачами сохраняет гибкие стратегии извлечения кадров и сортировки; кластерный вывод моделей обеспечивает отклик на уровне миллисекунд и высокую доступность. Полный и полурежимы обороны дают точный мониторинг и оповещения по периодам.</p>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
В управлении устройствами Интернета вещей EasyAIoT предоставляет полные возможности управления жизненным циклом устройств, поддерживает множество протоколов IoT и промышленных протоколов (MQTT, TCP, HTTP, Modbus-TCP, Modbus-RTU, OPC UA). Шлюзы в управлении устройствами — это облачная топология GATEWAY / подустройства; среда сбора на периферии <strong>EDGE</strong> C# выступает этим шлюзом на объекте, берёт на себя сбор промышленных протоколов и MQTT-интеграцию cloud-edge, данные возвращаются в то же управление устройствами — реализуя быстрое подключение устройств, безопасную аутентификацию, мониторинг в реальном времени и интеллектуальное управление. Через движок правил реализуется интеллектуальная маршрутизация и обработка данных устройств. В сочетании с возможностями ИИ выполняется углубленный анализ данных устройств, реализуя полную автоматизацию процесса от подключения устройств, сбора данных, интеллектуального анализа до выполнения решений, по-настоящему воплощая идею "интернета всего" и "интеллектуального управления всем".
</p>
</div>

<img src=".image/iframe1.jpg" alt="EasyAIoT平台架构" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">

## ⚠️ Отказ от ответственности

EasyAIoT — это проект с открытым исходным кодом для обучения, не связанный с коммерческой деятельностью. При использовании данного проекта пользователи должны соблюдать законы и правила, не допуская незаконных действий. Если EasyAIoT обнаружит незаконные действия пользователя, он будет сотрудничать с соответствующими органами в расследовании и сообщать правительственным органам. Любая юридическая ответственность, возникающая в результате незаконных действий пользователей, лежит на самих пользователях. Если использование пользователем причиняет ущерб третьим сторонам, пользователь должен возместить ущерб в соответствии с законом. Все связанные ресурсы EasyAIoT используются пользователями на свой собственный риск.

## 📚 Документация по развертыванию

- [Документация по развертыванию платформы](.doc/部署文档/平台部署文档_ru.md) — Linux (Ubuntu / CentOS·RHEL **7–9** / **CentOS ARM** / ARM / **Kylin (麒麟) / openEuler (欧拉)**) / Mac / Windows
- [Развёртывание образов macOS](.doc/部署文档/平台macOS部署文档_ru.md) — One-click pull предсобранных образов (Docker Desktop)
- [Развёртывание образов Windows](.doc/部署文档/平台Windows部署文档_ru.md) — Рекомендуемый вход `install_windows.ps1`
- [Лучшие практики развертывания](.doc/部署文档/部署最佳实践_ru.md) — Профили, требования, one-click (включая CentOS **7–9** / **CentOS ARM** / **Kylin (麒麟) / openEuler (欧拉)**), устранение неполадок и production

## 📘 Руководство по эксплуатации

Для поставки, дежурства и бизнес-операций: организовано по **цепочкам операций** (цель → предпосылки → шаги → критерии приёмки). Предполагается, что платформа уже развёрнута и доступна. (Содержание пока на упрощённом китайском.)

- [Руководство по эксплуатации (оглавление)](.doc/操作手册/README.md) — Как читать, краткий контур и индекс
- [Обзор цепочек операций](.doc/操作手册/00-操作链总览.md) — Карта, меню, чек-лист PoC
- [Вход и базовая подготовка](.doc/操作手册/01-登录与基础准备.md) — Учётные записи, оргструктура, права, уведомления
- [Подключение видеоустройств](.doc/操作手册/02-视频设备接入.md) — ONVIF / NVR / GB28181 / RTC / DJI → просмотр и push
- [Контур задач алгоритмов ИИ](.doc/操作手册/03-AI算法任务闭环.md) — Разметка/модели → задачи → тревоги
- [Подключение IoT-устройств](.doc/操作手册/04-物联网设备接入.md) — Продукт / модель → устройства → EDGE / промсбор
- [Тревоги, уведомления и внешняя интеграция](.doc/操作手册/05-告警通知与对外联动.md) — Обработка тревог, уведомления, TRANSFORM
- [Визуализационные экраны](.doc/操作手册/06-可视化大屏.md) — Редактирование, публикация и вывод экранов
- [Мобильное дежурство APP](.doc/操作手册/07-APP移动值守.md) — Соответствие возможностей APP и WEB

## 🎮 Демонстрационная среда

- Демо-адрес: http://36.111.47.113:8888/
- Логин: admin
- Пароль: admin123

## 🎬 Демонстрационное видео

- Bilibili: https://www.bilibili.com/video/BV1d3846yEQz/?vd_source=5d3350c0182a2cf35c2739f3d16c1161

## ⚙️ Адреса проекта

- Gitee: https://gitee.com/soaring-xiongkulu/easyaiot
- Github: https://github.com/soaring-xiongkulu/easyaiot

## 📸 Скриншоты

<div>
  <img src=".image/banner/banner-video1000.gif" alt="Демо" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner-video1001.gif" alt="Демо" width="49%">
</div>

#### 🖥️ Панель мониторинга

| | | |
|:---:|:---:|:---:|
| ![Ситуационная осведомлённость](.image/banner/banner1001.png) | ![Обзор](.image/banner/banner1076.jpg) | ![Тревоги](.image/banner/banner1074.jpg) |
| ![Панель](.image/banner/banner1075.jpg) | ![Многомерный](.image/banner/banner1095.jpg) | ![Комплексный](.image/banner/banner1096.jpg) |
| ![Мониторинг](.image/banner/banner1078.jpg) | ![Реальное время](.image/banner/banner1077.jpg) |  |

#### 📺 Визуализация и SCADA

| | | |
|:---:|:---:|:---:|
| ![Проект](.image/banner/banner1185.png) | ![SCADA](.image/banner/banner1186.png) | ![Редактор](.image/banner/banner1187.png) |
| ![Просмотр](.image/banner/banner1188.png) | ![Компоненты](.image/banner/banner1189.png) | ![Источник данных](.image/banner/banner1190.png) |
| ![Публикация](.image/banner/banner1191.png) | ![Выполнение](.image/banner/banner1192.png) | ![Шаблон](.image/banner/banner1193.png) |
| ![Активы](.image/banner/banner1194.png) | ![Большой экран](.image/banner/banner1195.png) | ![Отображение](.image/banner/banner1196.png) |

#### 📹 Видеонаблюдение

| | | |
|:---:|:---:|:---:|
| ![Видеонаблюдение](.image/banner/banner1225.png) | ![Видеонаблюдение](.image/banner/banner1226.png) | ![Видеонаблюдение](.image/banner/banner1227.png) |
| ![Видеонаблюдение](.image/banner/banner1228.png) | ![Видеонаблюдение](.image/banner/banner1229.png) | ![Видеонаблюдение](.image/banner/banner1230.png) |
| ![Видеонаблюдение](.image/banner/banner1219.png) | ![Видеонаблюдение](.image/banner/banner1220.png) | ![Видеонаблюдение](.image/banner/banner1221.png) |
| ![Видеонаблюдение](.image/banner/banner1222.png) | ![Видеонаблюдение](.image/banner/banner1223.png) | ![Видеонаблюдение](.image/banner/banner1224.png) |
| ![Обнаружение зоны](.image/banner/banner1213.png) | ![Обнаружение зоны](.image/banner/banner1214.png) | ![Обнаружение зоны](.image/banner/banner1218.png) |
| ![Цепочка правил постобработки](.image/banner/banner1216.png) | ![Цепочка правил постобработки](.image/banner/banner1217.png) | ![Цепочка правил постобработки](.image/banner/banner1215.png) |
| ![Прямой эфир](.image/banner/banner1145.jpg) | ![Просмотр](.image/banner/banner1146.jpg) | ![Камера](.image/banner/banner1051.jpg) |
| ![Список](.image/banner/banner1053.jpg) | ![Пуш-поток](.image/banner/banner1083.jpg) | ![Ретрансляция](.image/banner/banner1084.jpg) |
| ![Хранилище](.image/banner/banner1121.png) | ![Снимок](.image/banner/banner1122.png) | ![Запись](.image/banner/banner1123.png) |
| ![Конфигурация](.image/banner/banner1124.png) | ![Ёмкость](.image/banner/banner1125.png) | ![Воспроизведение](.image/banner/banner1126.png) |
| ![Снимок](.image/banner/banner1117.png) | ![Файлы](.image/banner/banner1118.png) | ![Политика](.image/banner/banner1119.png) |
| ![Квота](.image/banner/banner1120.png) | ![Галерея](.image/banner/banner1057.jpg) | ![Архив](.image/banner/banner1058.jpg) |
| ![Мониторинг](.image/banner/banner1068.jpg) | ![Статистика](.image/banner/banner1069.jpg) | ![Карта](.image/banner/banner1113.png) |
| ![Локация](.image/banner/banner1114.png) | ![Распределение](.image/banner/banner1115.png) | ![Точки](.image/banner/banner1116.png) |
| ![Живой просмотр](.image/banner/banner1026.jpg) | ![Мультиканал](.image/banner/banner1028.jpg) | ![Пуш-поток](.image/banner/banner1103.png) |
| ![Просмотр](.image/banner/banner1104.png) | ![Подключение](.image/banner/banner1105.png) | ![NVR](.image/banner/banner1106.png) |
| ![Живой просмотр](.image/banner/banner1183.jpg) | ![Карта](.image/banner/banner1184.jpg) |  |

#### 🤖 AI-ассистент

| | | |
|:---:|:---:|:---:|
| ![Вход IDEA](.image/banner/banner1203.png) | ![Рабочая область IDEA](.image/banner/banner1204.png) | ![Разработка IDEA](.image/banner/banner1205.png) |
| ![Диалог AI-ассистента](.image/banner/banner1210.png) | ![Анализ AI-ассистента](.image/banner/banner1211.png) | ![Совместная работа AI-ассистента](.image/banner/banner1212.png) |

#### 🧠 AI-модели

| | | |
|:---:|:---:|:---:|
| ![Синхронизация мультикластеров](.image/banner/banner1200.png) | ![Топология кластера NFS](.image/banner/banner1198.png) | ![Управление кластером NFS](.image/banner/banner1197.png) |
| ![Управление узлами](.image/banner/banner1199.png) | ![Каталог файлов NFS](.image/banner/banner1201.png) | ![Просмотр каталога NFS](.image/banner/banner1202.png) |
| ![Qwen](.image/banner/banner1093.jpg) | ![Модель зрения](.image/banner/banner1094.jpg) | ![Список](.image/banner/banner1099.png) |
| ![Конфигурация](.image/banner/banner1100.png) | ![Детали](.image/banner/banner1101.png) | ![Вызов](.image/banner/banner1102.png) |
| ![Обучение](.image/banner/banner1019.jpg) | ![Задача](.image/banner/banner1020.jpg) | ![Список](.image/banner/banner1023.jpg) |
| ![Прогресс](.image/banner/banner1024.jpg) | ![Параметры](.image/banner/banner1017.jpg) | ![Оценка](.image/banner/banner1018.jpg) |
| ![Детали](.image/banner/banner1021.png) | ![Журналы](.image/banner/banner1022.jpg) | ![Управление](.image/banner/banner1097.png) |
| ![Репозиторий](.image/banner/banner1098.png) | ![Версия](.image/banner/banner1039.jpg) | ![Активы](.image/banner/banner1061.jpg) |
| ![Инференс](.image/banner/banner1040.jpg) | ![Конфигурация](.image/banner/banner1042.jpg) | ![Результаты](.image/banner/banner1043.jpg) |
| ![Онлайн](.image/banner/banner1044.jpg) | ![Пакет](.image/banner/banner1047.jpg) | ![Мониторинг](.image/banner/banner1048.jpg) |
| ![Сервис](.image/banner/banner1045.jpg) | ![Развёртывание](.image/banner/banner1046.jpg) | ![Кластер](.image/banner/banner1049.jpg) |
| ![Вызов](.image/banner/banner1050.jpg) | ![Веса](.image/banner/banner1111.png) | ![Загрузка](.image/banner/banner1112.png) |
| ![Поза](.image/banner/banner1147.jpg) | ![Распознавание](.image/banner/banner1148.jpg) | ![Задача](.image/banner/banner1085.jpg) |
| ![Конфигурация](.image/banner/banner1086.jpg) | ![Детали](.image/banner/banner1087.jpg) | ![Выполнение](.image/banner/banner1088.jpg) |
| ![Область](.image/banner/banner1079.jpg) | ![Рамка детекции](.image/banner/banner1080.jpg) | ![Охрана](.image/banner/banner1081.jpg) |
| ![Просмотр](.image/banner/banner1082.jpg) | ![Алгоритм](.image/banner/banner1062.jpg) | ![Создать](.image/banner/banner1063.png) |
| ![Кадр](.image/banner/banner1064.jpg) | ![Анализ](.image/banner/banner1065.jpg) | ![Результаты](.image/banner/banner1066.jpg) |
| ![Повтор](.image/banner/banner1067.jpg) | ![Живой просмотр](.image/banner/banner1052.jpg) | ![Интеллект](.image/banner/banner1054.jpg) |

#### 📋 Заявки по тревогам

| | | |
|:---:|:---:|:---:|
| ![Конструктор процессов](.image/banner/banner1231.png) | ![Настройка узла](.image/banner/banner1232.png) | ![Выбор согласующих](.image/banner/banner1233.png) |
| ![Условные ветвления](.image/banner/banner1234.png) | ![Правила условий](.image/banner/banner1235.png) | ![Параллельные ветвления](.image/banner/banner1236.png) |

#### 📦 Наборы данных

| | | |
|:---:|:---:|:---:|
| ![Управление](.image/banner/banner1015.png) | ![Список](.image/banner/banner1010.jpg) | ![Разметка](.image/banner/banner1027.png) |
| ![Задача](.image/banner/banner1016.jpg) | ![Инструменты](.image/banner/banner1059.jpg) | ![Просмотр](.image/banner/banner1060.jpg) |
| ![Детали](.image/banner/banner1107.png) | ![Импорт](.image/banner/banner1108.png) | ![Проект](.image/banner/banner1109.png) |
| ![Проверка](.image/banner/banner1110.png) | ![Создать](.image/banner/banner1007.jpg) | ![Образцы](.image/banner/banner1008.jpg) |

#### 🔌 IoT

| | | |
|:---:|:---:|:---:|
| ![Модель вещи](.image/banner/banner1149.jpg) | ![Определение](.image/banner/banner1150.jpg) | ![Продукт](.image/banner/banner1151.jpg) |
| ![Детали](.image/banner/banner1152.jpg) | ![Устройство](.image/banner/banner1153.jpg) | ![Детали](.image/banner/banner1154.jpg) |
| ![Статус](.image/banner/banner1155.jpg) | ![Свойства](.image/banner/banner1156.jpg) | ![Сервис](.image/banner/banner1157.jpg) |
| ![События](.image/banner/banner1158.jpg) | ![Тень](.image/banner/banner1159.jpg) | ![Топология](.image/banner/banner1160.jpg) |
| ![Подустройства](.image/banner/banner1161.jpg) | ![Группы](.image/banner/banner1162.jpg) | ![Управление](.image/banner/banner1163.jpg) |
| ![Телеметрия](.image/banner/banner1164.jpg) | ![История](.image/banner/banner1165.jpg) | ![Протокол](.image/banner/banner1166.jpg) |
| ![Соединение](.image/banner/banner1167.jpg) | ![Аутентификация](.image/banner/banner1168.jpg) | ![Отладка](.image/banner/banner1169.jpg) |
| ![Функции](.image/banner/banner1170.jpg) | ![Чтение/Запись](.image/banner/banner1171.jpg) | ![Сервис](.image/banner/banner1172.jpg) |
| ![Подписка](.image/banner/banner1173.jpg) | ![Журналы](.image/banner/banner1174.jpg) | ![Онлайн](.image/banner/banner1175.jpg) |
| ![Статистика](.image/banner/banner1176.jpg) | ![Обзор](.image/banner/banner1177.jpg) | ![Панель](.image/banner/banner1178.jpg) |
| ![Продукт](.image/banner/banner1006.jpg) | ![Устройство](.image/banner/banner1009.jpg) | ![OTA](.image/banner/banner1179.jpg) |
| ![Прошивка](.image/banner/banner1180.jpg) | ![Задача](.image/banner/banner1181.jpg) | ![Прогресс](.image/banner/banner1182.jpg) |
| ![Правила](.image/banner/banner1013.jpg) | ![Оркестрация](.image/banner/banner1014.png) | ![Пересылка](.image/banner/banner1206.png) |
| ![Работа](.image/banner/banner1209.png) | ![Назначение](.image/banner/banner1207.png) | ![Доставка](.image/banner/banner1208.png) |

#### 🖥️ Кластер

| | | |
|:---:|:---:|:---:|
| ![Обзор](.image/banner/banner1127.jpg) | ![Вычислительная мощность](.image/banner/banner1128.jpg) | ![Узел](.image/banner/banner1129.jpg) |
| ![Детали](.image/banner/banner1130.jpg) | ![Мониторинг](.image/banner/banner1131.jpg) | ![Планирование](.image/banner/banner1132.jpg) |
| ![Список](.image/banner/banner1133.jpg) | ![Статус](.image/banner/banner1134.jpg) | ![Конфигурация](.image/banner/banner1135.jpg) |
| ![Распределение](.image/banner/banner1136.jpg) |  |  |

#### 🔔 Тревоги

| | | |
|:---:|:---:|:---:|
| ![События](.image/banner/banner1089.jpg) | ![Обработка](.image/banner/banner1090.jpg) | ![Уведомление](.image/banner/banner1029.jpg) |
| ![Конфигурация](.image/banner/banner1030.jpg) | ![Список](.image/banner/banner1072.jpg) | ![Детали](.image/banner/banner1031.jpg) |
| ![Обработка](.image/banner/banner1070.jpg) | ![Статистика](.image/banner/banner1071.jpg) |  |

#### ⚙️ Система

| | | |
|:---:|:---:|:---:|
| ![Брендинг](.image/banner/banner1143.jpg) | ![Сброс](.image/banner/banner1144.jpg) | ![Пользователи](.image/banner/banner1003.png) |
| ![Права](.image/banner/banner1004.png) | ![Меню](.image/banner/banner1005.png) | ![Конфигурация](.image/banner/banner1002.png) |

#### 📱 APP

| | | |
|:---:|:---:|:---:|
| ![Скриншот APP](.image/banner/app/app_1008.jpg) | ![Скриншот APP](.image/banner/app/app_1009.jpg) | ![Скриншот APP](.image/banner/app/app_1010.jpg) |
| ![Скриншот APP](.image/banner/app/app_1011.jpg) | ![Скриншот APP](.image/banner/app/app_1012.jpg) | ![Скриншот APP](.image/banner/app/app_1013.jpg) |
| ![Скриншот APP](.image/banner/app/app_2023.png) | ![Скриншот APP](.image/banner/app/app_2024.png) | ![Скриншот APP](.image/banner/app/app_2025.png) |
| ![Скриншот APP](.image/banner/app/app_2026.png) | ![Скриншот APP](.image/banner/app/app_2027.png) | ![Скриншот APP](.image/banner/app/app_2028.png) |
| ![Скриншот APP](.image/banner/app/app_1014.jpg) | ![Скриншот APP](.image/banner/app/app_1015.jpg) | ![Скриншот APP](.image/banner/app/app_1016.jpg) |
| ![Скриншот APP](.image/banner/app/app_1017.jpg) | ![Скриншот APP](.image/banner/app/app_1018.jpg) | ![Скриншот APP](.image/banner/app/app_1019.jpg) |
| ![Скриншот APP](.image/banner/app/app_1020.jpg) | ![Скриншот APP](.image/banner/app/app_1021.jpg) | ![Скриншот APP](.image/banner/app/app_1022.jpg) |
| ![Скриншот APP](.image/banner/app/app_2029.jpg) | ![Скриншот APP](.image/banner/app/app_2030.jpg) | ![Скриншот APP](.image/banner/app/app_2031.jpg) |

## 📞 Контакты

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Сначала подпишитесь на официальный аккаунт ниже, затем свяжитесь с нами через техническую группу или WeChat.
</p>

## 👥 Официальный аккаунт

<div>
  <img src=".image/公众号.jpg" alt="Официальный аккаунт" width="30%">
</div>

## 💬 Техническая группа

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
После подписки на официальный аккаунт отсканируйте QR-код ниже через WeChat, чтобы вступить в техническую группу EasyAIoT.
</p>

<div>
  <img src=".image/交流群3群.jpg" alt="Техническая группа EasyAIoT" width="30%">
</div>

## 💬 WeChat

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
После подписки на официальный аккаунт отсканируйте QR-код ниже, чтобы добавить нас в друзья WeChat для личного общения.
</p>

<div>
  <img src=".image/微信联系方式.jpg" alt="WeChat контакт" width="200">
</div>

## 🪐 Знаниевая планета:

<p>
  <img src=".image/知识星球.jpg" alt="知识星球" width="30%">
</p>

## 💰 Спонсорство и пожертвования

<div>
    <img src=".image/微信支付.jpg" alt="微信支付" width="30%" height="30%">
    <img src=".image/支付宝支付.jpg" alt="支付宝支付" width="30%" height="10%">
</div>

## 🤝 Руководство по участию

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Мы приветствуем все формы участия! Независимо от того, являетесь ли вы разработчиком кода, автором документации или сообщающим о проблемах, ваш вклад поможет сделать EasyAIoT лучше. Вот основные способы участия:
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">💻 Вклад в код</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Сделайте Fork проекта в свой аккаунт GitHub/Gitee</li>
  <li>Создайте ветку функции (git checkout -b feature/AmazingFeature)</li>
  <li>Зафиксируйте изменения (git commit -m 'Add some AmazingFeature')</li>
  <li>Отправьте в ветку (git push origin feature/AmazingFeature)</li>
  <li>Откройте Pull Request</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">📚 Вклад в документацию</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Улучшите существующее содержание документации</li>
  <li>Добавьте примеры использования и лучшие практики</li>
  <li>Предоставьте многоязычные переводы</li>
  <li>Исправьте ошибки в документации</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🌟 Другие способы участия</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Сообщайте и исправляйте ошибки</li>
  <li>Предлагайте улучшения функций</li>
  <li>Участвуйте в обсуждениях сообщества и помогайте другим разработчикам</li>
  <li>Делитесь опытом использования и примерами</li>
</ul>
</div>

</div>

## 🌟 Ключевые участники

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Ниже представлены выдающиеся участники, внесшие значительный вклад в проект EasyAIoT. Их вклад сыграл ключевую роль в развитии проекта. Мы выражаем нашу самую искреннюю благодарность!
</p>

<table style="width: 100%; table-layout: fixed; border-collapse: collapse; margin: 20px 0; font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
<thead>
<tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
<th style="padding: 15px; text-align: left; font-weight: 600; border: 1px solid #e0e0e0; width: 32%; min-width: 9rem;">Участник</th>
<th style="padding: 15px; text-align: left; font-weight: 600; border: 1px solid #e0e0e0;">Вклад</th>
</tr>
</thead>
<tbody>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>℡夏别</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Внес вклад в документацию по развертыванию Windows для проекта EasyAIoT, предоставив полное руководство по развертыванию для пользователей платформы Windows, значительно снизив сложность развертывания в средах Windows и позволив большему количеству пользователей легко использовать платформу EasyAIoT.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>YiYaYiYaho</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Внес вклад в скрипт однокликового развертывания контейнеров Mac для проекта EasyAIoT, предоставив автоматизированное решение для развертывания для пользователей платформы Mac, значительно упростив процесс развертывания в средах Mac и улучшив опыт развертывания для разработчиков и пользователей.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>山寒</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Внес вклад в скрипт развертывания контейнеров Linux для проекта EasyAIoT, предоставив решение для контейнеризованного развертывания для пользователей платформы Linux, достигнув быстрого и надежного развертывания контейнеров и обеспечив важные гарантии для стабильной работы в производственных средах.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>玖零。</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Внес вклад в скрипт развертывания контейнеров Linux для проекта EasyAIoT, дополнительно улучшив решение для контейнеризованного развертывания для платформ Linux, предоставив больше возможностей для пользователей различных дистрибутивов Linux и способствуя возможностям кроссплатформенного развертывания проекта.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>爱吃小柚子</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Внёс значительный вклад в развитие EasyAIoT в направлении обучения, которое действительно запускается, стабильно работает и удобно управляется: системно связал многокартовое обучение, возобновление с контрольной точки и развёртывание на стороне узла, чтобы полевые вычислительные ресурсы реально использовались, а задачи обучения оставались под контролем. Серверы автоматически обнаруживают и задействуют все GPU, на странице обучения можно выбрать одну или несколько карт — больше не приходится ограничиваться одной видимой картой; поддерживаются распространённые форматы и структуры датасетов, загрузка крупных локальных наборов, сохранение исходных данных после сбоя для быстрого повтора — заметно снижая затраты на подготовку данных и повторные попытки; сделаны видимым прогресс обучения и возможность остановить/продолжить задачу, чтобы не терять результаты после прерывания и не оставлять процессы «крутиться» в фоне после нажатия «Стоп», а при сбое локального или удалённого планирования — своевременно откатываться и давать понятную обратную связь; также улучшены выбор GPU, продолжение обучения и отображение статуса остановки во фронтенде, исправлены ложные «ошибки публикации», перезапись пользовательских превью, поиск моделей по имени/версии и таймауты/конфликты синхронизации датасетов — чтобы цикл «обучение — публикация — использование» стал плавнее и надёжнее. Ранее также руководил сквозной интеграционной проверкой GB28181 и ИИ-процессов, а также целевой оценкой чёткости изображения, дав важную основу для надёжного подключения по национальному стандарту и улучшения качества просмотра.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>Dark</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Внёс вклад в сквозную реализацию возможностей GB28181 для EasyAIoT в сфере видеонаблюдения по национальному стандарту: обеспечены воспроизведение видео и управление PTZ (поворотная платформа), благодаря чему подключение устройств по GB28181 стало пригодным для живого просмотра и удалённого управления камерой.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>machh</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Внёс вклад в проект EasyAIoT-Edge: выполнена сквозная проверка подключения камер и функций ИИ, а также согласованная связка возможностей в единый работоспособный контур на периферии.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>遗忘的星空</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Внёс вклад в развитие прямого подключения устройств EasyAIoT: инвентаризация IP-камер разных брендов и сканирование подсетей с массовым обнаружением IPC и NVR Hikvision; улучшены массовый поиск и регистрация в один клик для напрямую подключённых устройств в одной подсети и между подсетями. Доступ реализован через нативные протоколы устройств, с обходом SDK Hikvision и снижением зависимости от платформы Hikvision — заложена основа для открытого и контролируемого масштабного подключения камер.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>阿龙</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Внёс вклад в развитие EasyAIoT в направлении картографической визуализации и пространственного анализа, самостоятельно реализовав полный код пространственной визуализации на базе Tianditu: интеграция национальной подложки Tianditu, размещение камер и устройств оповещения, представление распределения на карте, поиск мест и пакетный импорт координат, автоматическое отображение тревожных событий на карте, отслеживание людей и транспортных средств и воспроизведение траекторий мобильных устройств — переведя возможность «пространственной визуализации Tianditu и анализа на карте» от проектирования к готовому к промышленной эксплуатации решению.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>雨落流殇</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Внёс вклад в развитие EasyAIoT в направлении сверхкрупномасштабной доставки потокового мультимедиа, предложив подходы к развёртыванию и планированию гетерогенных стриминговых кластеров: координация пулов узлов, разделение стримингового слоя и бизнес-слоя, регистрация и планирование узлов — заложив важную архитектурную основу для одновременного подключения десятков тысяч камер со стабильной доставкой и эластичным масштабированием.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>常康</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Внёс вклад в развитие EasyAIoT в направлении интеллектуального транспорта и управления транспортными средствами, самостоятельно реализовав алгоритм распознавания автомобильных номеров и полный программный код: локализация и распознавание номера, определение цвета, склейка двухрядных номеров и коррекция наклона/перспективы, управление базами номеров и последовательное сопоставление по нескольким базам, интеграция с алгоритмическими задачами в один клик и асинхронное сравнение — с поддержкой синих, жёлтых, зелёных, белых и номеров для новых энергетических ТС — переведя возможность «распознавания номеров и управления базами» от планирования к промышленному замкнутому применению.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>Li</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Внёс вклад в развитие EasyAIoT в направлении молодёжного сообщества разработчиков и экосистемы совместной работы, проявив выдающееся организационное лидерство и способность вдохновлять: возглавил участие студентов всего кампуса в совместном развитии проекта, объединил молодые таланты и командный потенциал, придав EasyAIoT неиссякаемый и устойчивый импульс роста; также внёс решающий, незаменимый вклад в продвижение проекта, практическую реализацию и формирование следующего поколения участников.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>陈家林</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Внёс вклад в развитие EasyAIoT в направлении взаимодействия IoT-устройств, доступа к промышленным протоколам и воздушно-наземной видеоконвергенции: обеспечил замкнутый контур команд и данных состояния, чтобы платформа действительно могла «спускать команды, видеть состояние и удерживать управление»; системно внёс возможности доступа Modbus-TCP, Modbus-RTU и OPC UA — единый сбор по Ethernet- и последовательным промышленным устройствам и узлам OPC UA, чтение/запись регистров/точек и маппинг вещной модели, чтобы данные счётчиков, датчиков, ПЛК, контроллеров могли единообразно агрегироваться, мониториться и связываться, дополнив ключевой фрагмент «видеть площадку и слышать устройства»; также внёс возможности подключения доков и видеопотоков дронов DJI, включив воздушной осмотр в единую систему видео и оповещений и существенно расширив практическую ценность для промышленного сбора данных, интеллектуального управления линией, широкомасштабного патрулирования, аварийной разведки и совместного небо–земля восприятия.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>空空</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Внёс вклад в развитие EasyAIoT в направлении прямого подключения камер — от «можно обнаружить» к «можно внедрять на объекте»: закрыл критические пробелы в аутентификации, синхронизации каналов, изменении конфигурации и многобрендовой выдаче потоков, сделав платформу готовой к поставке на реальных NVR / мультибрендовых площадках; обеспечил надёжную цепочку учётных данных входа, чтобы устройства прямого подключения действительно «входили в систему и управлялись»; улучшил модель получения потока после синхронизации каналов NVR, чтобы пакетно синхронизированные потоки воспроизводились и масштабировались; обеспечил устойчивое редактирование параметров доступа; создал библиотеку правил RTSP URL для распространённых отечественных брендов видеонаблюдения и открыл пользовательские правила брендов, позволяя разнородным устройствам собирать потоки в один клик — продвинув прямое подключение от «устройства находятся сканированием» к производственно пригодной форме «вход работает, синхронизация точна, конфигурацию можно менять, многобрендовые потоки идут», заложив прочную основу для последующего PTZ и зума.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>狗娃</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Внёс вклад в развитие EasyAIoT в направлении «IoT-данные можно вывести на экран», опережающе предложив продуктовую концепцию модуля Board (drag-and-drop панели): традиционные большие экраны часто требуют отдельных запросов для каждого экрана и компонента — медленная поставка, любое изменение затрагивает всё, бизнес-пользователи почти не могут делать экраны сами. Решение Board передаёт диаграммы, показатели и компоновку в drag-and-drop холст и напрямую связывает переменные компонентов с IoT-точками модели вещи — текущие и исторические значения берутся с устройств в один клик, без отдельных запросов для каждой панели; экраны ситуации кампуса, KPI линии, эксплуатации оборудования переходят от «разработчик пишет запросы» к «выбрать точку, перетащить компонент» — заметно сокращая цикл визуальной поставки и превращая IoT «данные в бэкенде» в управляемую способность «экран на фронте». Ранее также внёс прогноз float-данных датчиков, настройку верхних/нижних порогов атрибутов рабочего состояния, пороговые оповещения и правила со связкой, а также отображение рабочего состояния связанных подчинённых центрального устройства на одном экране — замкнув контур «прогноз — границы — оповещение — правила — управление на одном экране», чтобы сторона устройств могла «видеть цифры, держать границы, поднимать тревогу и видеть картину целиком».</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>大老刘</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Внёс вклад в развитие EasyAIoT в направлении внешней коммуникации и представления решений, подготовив иллюстрированные материалы «Платформа AI-анализа видеонаблюдения»: системно изложил полный спектр возможностей платформы и ценность внедрения в сценариях AI-анализа видеонаблюдения, чтобы пользователи, интеграторы и партнёры быстрее понимали позиционирование и ключевые преимущества — заметно повысив эффективность внешней презентации и делового общения.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>刘兆中ᯤ⁵ᴳ</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Внёс вклад в развитие EasyAIoT в направлении однокнопочного развёртывания на macOS: первым предложил часть скриптов однокнопочного развёртывания для Mac и в основном проложил магистральный путь — загрузку образов, оркестрацию контейнеров и предварительные проверки среды, — так что дальнейшая доработка свелась к «последней миле». Его исследования помогли команде прояснить ключевые узлы и риски цепочки развёртывания на Mac, заметно сократив путь к инженерному завершению; это незаменимый фундамент на пути macOS-развёртывания от нуля к рабочему состоянию.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>添旺</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Внося вклад в развитие EasyAIoT в направлении облачно-периферийного совместного видеодоступа и ИИ-аналитики, самостоятельно реализовал несколько ключевых возможностей, прямо отвечающих главным болям реальных периферийных внедрений — «камеры не подключить, планирование мимо, реально работает лишь один канал, к прошлому не вернуться»: первым поддержал периферийное подключение камер с аффинитетом алгоритмических узлов — IPC/NVR могут назначать онлайн-узел периферии «узлом доступа», при этом обнаружение устройств, сканирование подсетей, ONVIF-проба и перечисление каналов NVR выполняются локально на этом узле, а исходные потоки возвращаются в медиасервис управляющей плоскости для единого распределения и воспроизведения; камеры филиалов и межсетевых/приватных сегментов больше не требуют прямой доступности центральной платформы для подключения и выдачи потока, а алгоритмические задачи автоматически закрепляются за узлом доступа своих камер, что исключает на уровне планирования отправку задач на узлы, неспособные получить исходный поток, и позволяет вычислительным мощностям выстраиваться вплотную к камерам. Далее диагностировал и исправил критический дефект, при котором несколько задач или многомодельных конвейеров на одной камере оставляли действенным лишь один канал — благодаря изоляции цепочек вывода потоковыми идентификаторами уровня задачи, переиспользованию общего декодирования параллельными задачами через отдельный сервис камерных источников и сквозной передаче идентификатора задачи в оповещения и статусы выполнения одна камера теперь стабильно несёт несколько алгоритмических задач и многомодельное обнаружение (лицо + транспорт в одном кадре) параллельно, под долгосрочной защитой выделенного сервиса источников и регрессионных тестов. Также реализовал многоуровневое хранение записей на периферии с единым воспроизведением событий — записи сохраняются на месте по уровням, события оповещений и видеоулики доступны для поиска и повторного просмотра через единый облачно-периферийный вход, замыкая доказательный контур от «событие зафиксировано» до «улика в руках». Эти работы заметно повысили предсказуемость внедрения платформы в сложных реальных сетевых средах и достоверность результатов её ИИ-аналитики.</td>
</tr>
</tbody>
</table>

<p style="font-size: 14px; line-height: 1.8; color: #2c3e50; font-weight: 500; margin: 20px 0; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #3498db; border-radius: 4px;">
<strong>Особая благодарность</strong>: Перечисленные участники способствовали развитию EasyAIoT в разных направлениях — документация и сценарии кроссплатформенного развёртывания, закладка основ и исследование цепочки однокнопочного развёртывания на macOS, видеовозможности по национальному стандарту и интеграционное тестирование с ИИ, многокарточное обучение и возобновление с контрольной точки, прямое обнаружение многобрендовых камер и массовое подключение, пространственная визуализация Tianditu, развёртывание и планирование гетерогенных стриминговых кластеров, алгоритм распознавания номеров и полная реализация кода, сквозная интеграция EasyAIoT-Edge на периферии, организация кампусного сообщества разработчиков и экосистема молодёжного сотрудничества, замкнутый контур IoT-устройств и интеграция воздушного обзора DJI, доступ Modbus-TCP / Modbus-RTU / OPC UA к промышленным протоколам, замкнутый контур прямого подключения камер от обнаружения до входа/синхронизации/конфигурации/многобрендовой выдачи потока, концепция drag-and-drop панели (Board) с прямой интеграцией текущих/исторических значений IoT-точек, прогноз float-данных датчиков с пороговыми оповещениями и отображение рабочего состояния связанных подустройств центральных устройств на одном экране, а также иллюстрированные материалы о платформе AI-анализа видеонаблюдения, периферийный доступ камер с аффинитетом алгоритмических узлов, исправление изоляции многозадачного/многомодельного вывода на одной камере и многоуровневое хранение записей на периферии с единым воспроизведением событий. Их профессионализм и самоотверженная преданность достойны нашего изучения и уважения. Ещё раз выражаем нашу самую искреннюю благодарность этим выдающимся участникам! 🙏
</p>

## 💝 Хранители open source

Поддержание open-source проекта — это не только код и документация. В дни, когда вычислительные ресурсы EasyAIoT были на пределе, а проект был на грани остановки, перечисленные ниже люди пришли на помощь с реальной финансовой поддержкой, дав проекту необходимый импульс для продолжения работы. Возможно, вы ни разу не отправляли ни строчки кода, но каждый акт доверия и поддержки помог EasyAIoT преодолеть самые трудные препятствия и продолжать развиваться. Пока проектом пользуются и его поддерживают, open-source экосистема заслуживает идти дальше; того, чего EasyAIoT достиг сегодня, было бы невозможно без этих товарищей, протянувших руку помощи в критический момент. Мы выражаем глубочайшее уважение и благодарность каждому, кто протянул руку помощи! Рейтинг ниже не имеет определённого порядка:

<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/lysss.jpg" width="80px;" alt="lysss"/><br /><sub><b>lysss</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Sean-宋阳.jpg" width="80px;" alt="Sean-宋阳"/><br /><sub><b>Sean-宋阳</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/XYZ.jpg" width="80px;" alt="XYZ"/><br /><sub><b>XYZ</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/大虚子民🎼.jpg" width="80px;" alt="大虚子民🎼"/><br /><sub><b>大虚子民🎼</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/哈兰葱.jpg" width="80px;" alt="哈兰葱"/><br /><sub><b>哈兰葱</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/曲超.jpg" width="80px;" alt="曲超"/><br /><sub><b>曲超</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/李雪汉.jpg" width="80px;" alt="李雪汉"/><br /><sub><b>李雪汉</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/梦影·清之韵.jpg" width="80px;" alt="梦影·清之韵"/><br /><sub><b>梦影·清之韵</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/dasic.png" width="80px;" alt="dasic"/><br /><sub><b>dasic</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/战刀.jpg" width="80px;" alt="战刀"/><br /><sub><b>战刀</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/禾一虫.jpg" width="80px;" alt="禾一虫"/><br /><sub><b>禾一虫</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/钟意月月🍹.jpg" width="80px;" alt="钟意月月🍹"/><br /><sub><b>钟意月月🍹</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/山人.jpg" width="80px;" alt="山人"/><br /><sub><b>山人</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/林大侠.jpg" width="80px;" alt="林大侠"/><br /><sub><b>林大侠</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/core.jpg" width="80px;" alt="core"/><br /><sub><b>core</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/王亚鹏.jpg" width="80px;" alt="王亚鹏"/><br /><sub><b>王亚鹏</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/今早好大雾.jpg" width="80px;" alt="今早好大雾"/><br /><sub><b>今早好大雾</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/头像飞鱼.jpg" width="80px;" alt="头像飞鱼"/><br /><sub><b>头像飞鱼</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/simon.jpg" width="80px;" alt="simon"/><br /><sub><b>simon</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/万博览.jpg" width="80px;" alt="万博览"/><br /><sub><b>万博览</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/董永乐.jpg" width="80px;" alt="董永乐"/><br /><sub><b>董永乐</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/℡夏别.jpg" width="80px;" alt="℡夏别"/><br /><sub><b>℡夏别</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/wangqiqi" target="_blank"><img src="./.image/open-source-guardian/周金旺.jpg" width="80px;" alt="周金旺"/><br /><sub><b>周金旺</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/无忧.jpg" width="80px;" alt="无忧"/><br /><sub><b>无忧</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/许多.jpg" width="80px;" alt="许多"/><br /><sub><b>许多</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/王军.jpg" width="80px;" alt="王军"/><br /><sub><b>王军</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/子非鱼.png" width="80px;" alt="子非鱼"/><br /><sub><b>子非鱼</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/苏州小朱.jpg" width="80px;" alt="苏州小朱"/><br /><sub><b>苏州小朱</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/空白.jpg" width="80px;" alt=""/><br /><sub><b></b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/HuaZy.jpg" width="80px;" alt="HuaZy"/><br /><sub><b>HuaZy</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/越南打印机网络监控电脑门禁何工.jpg" width="80px;" alt="越南打印机网络监控电脑门禁何工"/><br /><sub><b>越南打印机网络监控电脑门禁何工</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/熊勇辉.jpg" width="80px;" alt="熊勇辉"/><br /><sub><b>熊勇辉</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/旭.jpg" width="80px;" alt="旭"/><br /><sub><b>旭</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/心远.jpg" width="80px;" alt="心远"/><br /><sub><b>心远</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Mr.Peng.jpg" width="80px;" alt="Mr.Peng"/><br /><sub><b>Mr.Peng</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/舒韩春💭成都云速广告💭.jpg" width="80px;" alt="舒韩春💭成都云速广告💭"/><br /><sub><b>舒韩春💭成都云速广告💭</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/前进!.png" width="80px;" alt="前进!"/><br /><sub><b>前进!</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/永恒.png" width="80px;" alt="永恒"/><br /><sub><b>永恒</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Catwings.png" width="80px;" alt="Catwings"/><br /><sub><b>Catwings</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/刘振达.png" width="80px;" alt="刘振达"/><br /><sub><b>刘振达</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/雷沛奇.png" width="80px;" alt="雷沛奇"/><br /><sub><b>雷沛奇</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/CSL.png" width="80px;" alt="CSL"/><br /><sub><b>CSL</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/自胜.png" width="80px;" alt="自胜"/><br /><sub><b>自胜</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/朱江山.png" width="80px;" alt="朱江山"/><br /><sub><b>朱江山</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/安.png" width="80px;" alt="安"/><br /><sub><b>安</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/简单.png" width="80px;" alt="简单"/><br /><sub><b>简单</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/郝艳军.png" width="80px;" alt="郝艳军"/><br /><sub><b>郝艳军</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Star&Li.png" width="80px;" alt="Star&Li"/><br /><sub><b>Star&Li</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/工体东路.png" width="80px;" alt="工体东路"/><br /><sub><b>工体东路</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Sunder..png" width="80px;" alt="Sunder."/><br /><sub><b>Sunder.</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/程亮🌟.png" width="80px;" alt="程亮🌟"/><br /><sub><b>程亮🌟</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/should.png" width="80px;" alt="should"/><br /><sub><b>should</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/黄国洪.png" width="80px;" alt="黄国洪"/><br /><sub><b>黄国洪</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Holmesian.png" width="80px;" alt="Holmesian"/><br /><sub><b>Holmesian</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Issac.png" width="80px;" alt="Issac"/><br /><sub><b>Issac</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/习惯.png" width="80px;" alt="习惯"/><br /><sub><b>习惯</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/黄杰.png" width="80px;" alt="黄杰"/><br /><sub><b>黄杰</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/唐智灵.png" width="80px;" alt="唐智灵"/><br /><sub><b>唐智灵</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/巴波儿奔🇨🇳.png" width="80px;" alt="巴波儿奔🇨🇳"/><br /><sub><b>巴波儿奔🇨🇳</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/冯振华.png" width="80px;" alt="冯振华"/><br /><sub><b>冯振华</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/风清扬.png" width="80px;" alt="风清扬"/><br /><sub><b>风清扬</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/take your time or.png" width="80px;" alt="take your time or"/><br /><sub><b>take your time or</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Rising徐.png" width="80px;" alt="Rising徐"/><br /><sub><b>Rising徐</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Mr.G.png" width="80px;" alt="Mr.G"/><br /><sub><b>Mr.G</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/吴翕然.png" width="80px;" alt="吴翕然"/><br /><sub><b>吴翕然</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/蓝天白云.png" width="80px;" alt="蓝天白云"/><br /><sub><b>蓝天白云</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Charlie.png" width="80px;" alt="Charlie"/><br /><sub><b>Charlie</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/胖哥.png" width="80px;" alt="胖哥"/><br /><sub><b>胖哥</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/王宪芳.png" width="80px;" alt="王宪芳"/><br /><sub><b>王宪芳</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/lk.png" width="80px;" alt="lk"/><br /><sub><b>lk</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/阿旺.png" width="80px;" alt="阿旺*"/><br /><sub><b>阿旺*</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/🍃一笑奈何🍃.png" width="80px;" alt="🍃一笑奈何🍃"/><br /><sub><b>🍃一笑奈何🍃</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/刘召.png" width="80px;" alt="刘召"/><br /><sub><b>刘召</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/🍻Jamie.png" width="80px;" alt="🍻Jamie"/><br /><sub><b>🍻Jamie</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/薛磊.png" width="80px;" alt="薛磊"/><br /><sub><b>薛磊</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Jack.png" width="80px;" alt="Jack"/><br /><sub><b>Jack</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/啊这.png" width="80px;" alt="啊这"/><br /><sub><b>啊这</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/在希望德田野上.png" width="80px;" alt="在希望德田野上"/><br /><sub><b>在希望德田野上</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/莫建民.png" width="80px;" alt="莫建民"/><br /><sub><b>莫建民</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/马景祥.png" width="80px;" alt="马景祥"/><br /><sub><b>马景祥</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/谭远彪.png" width="80px;" alt="谭远彪"/><br /><sub><b>谭远彪</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/一杯陈豆浆🥲🥲.png" width="80px;" alt="一杯陈豆浆🥲🥲"/><br /><sub><b>一杯陈豆浆🥲🥲</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/chen.png" width="80px;" alt="chen"/><br /><sub><b>chen</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/xingzhedu2030.png" width="80px;" alt="xingzhedu2030"/><br /><sub><b>xingzhedu2030</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/machh.png" width="80px;" alt="machh"/><br /><sub><b>machh</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/开炫🍊🍊🍊.png" width="80px;" alt="开炫🍊🍊🍊"/><br /><sub><b>开炫🍊🍊🍊</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Dark.png" width="80px;" alt="Dark"/><br /><sub><b>Dark</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/A-Tree.png" width="80px;" alt="A-Tree"/><br /><sub><b>A-Tree</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/陈.png" width="80px;" alt="陈"/><br /><sub><b>陈</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/月半.png" width="80px;" alt="月半"/><br /><sub><b>月半</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/吴军.png" width="80px;" alt="吴军"/><br /><sub><b>吴军</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/青衫.png" width="80px;" alt="青衫"/><br /><sub><b>青衫</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/梓淇東來.png" width="80px;" alt="梓淇東來"/><br /><sub><b>梓淇東來</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/潇潇.png" width="80px;" alt="潇潇"/><br /><sub><b>潇潇</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/依依.png" width="80px;" alt="依依"/><br /><sub><b>依依</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/金·郁金香.png" width="80px;" alt="金·郁金香"/><br /><sub><b>金·郁金香</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/David.png" width="80px;" alt="David"/><br /><sub><b>David</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/榕德天锐-邱国城.png" width="80px;" alt="榕德天锐-邱国城"/><br /><sub><b>榕德天锐-邱国城</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Wzs.png" width="80px;" alt="Wzs"/><br /><sub><b>Wzs</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/张军伟.png" width="80px;" alt="张军伟"/><br /><sub><b>张军伟</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/菜rainbow狗.png" width="80px;" alt="菜rainbow狗"/><br /><sub><b>菜rainbow狗</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/闻达.png" width="80px;" alt="闻达"/><br /><sub><b>闻达</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/银之匙.png" width="80px;" alt="银之匙"/><br /><sub><b>银之匙</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/命中注定.png" width="80px;" alt="命中注定"/><br /><sub><b>命中注定</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/..png" width="80px;" alt="..."/><br /><sub><b>...</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/爱吃小柚子.png" width="80px;" alt="爱吃小柚子"/><br /><sub><b>爱吃小柚子</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/草原雄鹰.png" width="80px;" alt="草原雄鹰"/><br /><sub><b>草原雄鹰</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/顺流致远.png" width="80px;" alt="顺流致远"/><br /><sub><b>顺流致远</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/香草口味.png" width="80px;" alt="香草口味"/><br /><sub><b>香草口味</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/雨落流殇.png" width="80px;" alt="雨落流殇"/><br /><sub><b>雨落流殇</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/弱电安防.png" width="80px;" alt="弱电安防"/><br /><sub><b>弱电安防</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/山里人.png" width="80px;" alt="山里人"/><br /><sub><b>山里人</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/诗如画.png" width="80px;" alt="诗如画"/><br /><sub><b>诗如画</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/星空🌃.png" width="80px;" alt="星空🌃"/><br /><sub><b>星空🌃</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/楠哥.png" width="80px;" alt="楠哥"/><br /><sub><b>楠哥</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/蜗牛.png" width="80px;" alt="蜗牛"/><br /><sub><b>蜗牛</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/大周.png" width="80px;" alt="大周"/><br /><sub><b>大周</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/歌德de花烛.png" width="80px;" alt="歌德de花烛"/><br /><sub><b>歌德de花烛</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/noname.png" width="80px;" alt="noname"/><br /><sub><b>noname</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/兔子.png" width="80px;" alt="兔子"/><br /><sub><b>兔子</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/ThinkInStack.png" width="80px;" alt="ThinkInStack"/><br /><sub><b>ThinkInStack</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Louis.png" width="80px;" alt="Louis"/><br /><sub><b>Louis</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/胡首凡 梯控门禁五方对讲.png" width="80px;" alt="胡首凡 梯控门禁五方对讲"/><br /><sub><b>胡首凡 梯控门禁五方对讲</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/袁建华.png" width="80px;" alt="袁建华"/><br /><sub><b>袁建华</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/空空.png" width="80px;" alt="空空"/><br /><sub><b>空空</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/阿涛.png" width="80px;" alt="阿涛"/><br /><sub><b>阿涛</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/NULL.png" width="80px;" alt="NULL"/><br /><sub><b>NULL</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/一片天.png" width="80px;" alt="一片天"/><br /><sub><b>一片天</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/小满藏舟.png" width="80px;" alt="小满藏舟"/><br /><sub><b>小满藏舟</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/M.png" width="80px;" alt="M"/><br /><sub><b>M</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/舍得.png" width="80px;" alt="舍得"/><br /><sub><b>舍得</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/默者.png" width="80px;" alt="默者"/><br /><sub><b>默者</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/火车叨位去、.png" width="80px;" alt="火车叨位去、"/><br /><sub><b>火车叨位去、</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/payne.png" width="80px;" alt="payne"/><br /><sub><b>payne</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/滕虎.png" width="80px;" alt="滕虎"/><br /><sub><b>滕虎</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/天天.png" width="80px;" alt="天天"/><br /><sub><b>天天</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/王超.png" width="80px;" alt="王超"/><br /><sub><b>王超</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/南北.png" width="80px;" alt="南北"/><br /><sub><b>南北</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/最后的轻语.png" width="80px;" alt="最后的轻语"/><br /><sub><b>最后的轻语</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/西乡一粒沙.png" width="80px;" alt="西乡一粒沙"/><br /><sub><b>西乡一粒沙</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/yang.png" width="80px;" alt="yang"/><br /><sub><b>yang</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/何行者.png" width="80px;" alt="何行者"/><br /><sub><b>何行者</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/在路上.png" width="80px;" alt="在路上"/><br /><sub><b>在路上</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/ANDY.png" width="80px;" alt="ANDY"/><br /><sub><b>ANDY</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/冯.png" width="80px;" alt="冯"/><br /><sub><b>冯</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/忘记时间.png" width="80px;" alt="忘记时间"/><br /><sub><b>忘记时间</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/A许庆.png" width="80px;" alt="A许庆"/><br /><sub><b>A许庆</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/刘兆中📶⁵ᴳ.png" width="80px;" alt="刘兆中📶⁵ᴳ"/><br /><sub><b>刘兆中📶⁵ᴳ</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/莫斯克.png" width="80px;" alt="莫斯克"/><br /><sub><b>莫斯克</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/赵欢.png" width="80px;" alt="赵欢"/><br /><sub><b>赵欢</b></sub></a></td>
    </tr>
  </tbody>
</table>

## 🏆 Лучшие практики внедрения

Они — пионеры, которые переводят EasyAIoT из состояния «можно использовать» в «удобно использовать и использовать хорошо». Перечисленные ниже участники завершили развёртывание проекта EasyAIoT или внедрение в бизнес-сценариях. Их опыт и результаты задают воспроизводимые ориентиры для сообщества. Мы выражаем им высочайшее уважение и искренние поздравления! Следующий список в произвольном порядке:

<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/best-practitioner/℡夏别.jpg" width="80px;" alt="℡夏别"/><br /><sub><b>℡夏别</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/best-practitioner/YiYaYiYaho.jpg" width="80px;" alt="YiYaYiYaho"/><br /><sub><b>YiYaYiYaho</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/best-practitioner/冯.jpg" width="80px;" alt="冯"/><br /><sub><b>冯</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/best-practitioner/在希望德田野上.jpg" width="80px;" alt="在希望德田野上"/><br /><sub><b>在希望德田野上</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/best-practitioner/漠然.png" width="80px;" alt="漠然"/><br /><sub><b>漠然</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/best-practitioner/爱吃小柚子.jpg" width="80px;" alt="爱吃小柚子"/><br /><sub><b>爱吃小柚子</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/best-practitioner/Wzs.jpg" width="80px;" alt="Wzs"/><br /><sub><b>Wzs</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/best-practitioner/Dark.jpg" width="80px;" alt="Dark"/><br /><sub><b>Dark</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/best-practitioner/刘延波.jpg" width="80px;" alt="刘延波"/><br /><sub><b>刘延波</b></sub></a></td>
    </tr>
  </tbody>
</table>

## 🙏 Благодарности

Благодарим следующих людей за поддержку данного проекта, включая, помимо прочего, вклад в код, обратную связь по проблемам, финансовые пожертвования и другие способы! Следующий список в произвольном порядке:
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/默者.png" width="80px;" alt="默者"/><br /><sub><b>默者</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/小满藏舟.png" width="80px;" alt="小满藏舟"/><br /><sub><b>小满藏舟</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/空空.png" width="80px;" alt="空空"/><br /><sub><b>空空</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/chen_jialin123" target="_blank"><img src="./.image/sponsor/陈家林.png" width="80px;" alt="陈家林"/><br /><sub><b>陈家林</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/NULL.png" width="80px;" alt="NULL"/><br /><sub><b>NULL</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/陈勇至.jpg" width="80px;" alt="陈勇至"/><br /><sub><b>陈勇至</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Dark.jpg" width="80px;" alt="Dark"/><br /><sub><b>Dark</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/machh" target="_blank"><img src="./.image/sponsor/machh.jpg" width="80px;" alt="machh"/><br /><sub><b>machh</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/三块两毛四.jpg" width="80px;" alt="三块两毛四"/><br /><sub><b>三块两毛四</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/物语晨水²⁰²⁶.jpg" width="80px;" alt="物语晨水²⁰²⁶"/><br /><sub><b>物语晨水²⁰²⁶</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/L_Z_M" target="_blank"><img src=".image/sponsor/玖零。.jpg" width="80px;" alt="玖零。"/><br /><sub><b>玖零。</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/36436022" target="_blank"><img src=".image/sponsor/金鸿伟.jpg" width="80px;" alt="金鸿伟"/><br /><sub><b>金鸿伟</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/cnlijf" target="_blank"><img src="./.image/sponsor/李江峰.jpg" width="80px;" alt="李江峰"/><br /><sub><b>李江峰</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src=".image/sponsor/Best%20Yao.jpg" width="80px;" alt="Best Yao"/><br /><sub><b>Best Yao</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/weiloser" target="_blank"><img src=".image/sponsor/无为而治.jpg" width="80px;" alt="无为而治"/><br /><sub><b>无为而治</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/shup092_admin" target="_blank"><img src="./.image/sponsor/shup.jpg" width="80px;" alt="shup"/><br /><sub><b>shup</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/gampa" target="_blank"><img src="./.image/sponsor/也许.jpg" width="80px;" alt="也许"/><br /><sub><b>也许</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/leishaozhuanshudi" target="_blank"><img src="./.image/sponsor/⁰ʚᦔrꫀꪖꪑ⁰ɞ%20..jpg" width="80px;" alt="⁰ʚᦔrꫀꪖꪑ⁰ɞ ."/><br /><sub><b>⁰ʚᦔrꫀꪖꪑ⁰ɞ .</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/fateson" target="_blank"><img src="./.image/sponsor/逆.jpg" width="80px;" alt="逆"/><br /><sub><b>逆</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/dongGezzz_admin" target="_blank"><img src="./.image/sponsor/廖东旺.jpg" width="80px;" alt="廖东旺"/><br /><sub><b>廖东旺</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/huangzhen1993" target="_blank"><img src="./.image/sponsor/黄振.jpg" width="80px;" alt="黄振"/><br /><sub><b>黄振</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/fengchunshen" target="_blank"><img src="./.image/sponsor/春生.jpg" width="80px;" alt="春生"/><br /><sub><b>春生</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/mrfox_wang" target="_blank"><img src="./.image/sponsor/贵阳王老板.jpg" width="80px;" alt="贵阳王老板"/><br /><sub><b>贵阳王老板</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/haobaby" target="_blank"><img src="./.image/sponsor/hao_chen.jpg" width="80px;" alt="hao_chen"/><br /><sub><b>hao_chen</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/finalice" target="_blank"><img src="./.image/sponsor/尽千.jpg" width="80px;" alt="尽千"/><br /><sub><b>尽千</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/yuer629" target="_blank"><img src="./.image/sponsor/yuer629.jpg" width="80px;" alt="yuer629"/><br /><sub><b>yuer629</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/cai-peikai/ai-project" target="_blank"><img src="./.image/sponsor/kong.jpg" width="80px;" alt="kong"/><br /><sub><b>kong</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/HB1731276584" target="_blank"><img src="./.image/sponsor/岁月静好.jpg" width="80px;" alt="岁月静好"/><br /><sub><b>岁月静好</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/hy5128" target="_blank"><img src="./.image/sponsor/Kunkka.jpg" width="80px;" alt="Kunkka"/><br /><sub><b>Kunkka</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/guo-dida" target="_blank"><img src="./.image/sponsor/灬.jpg" width="80px;" alt="灬"/><br /><sub><b>灬</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/XyhBill" target="_blank"><img src="./.image/sponsor/Mr.LuCkY.jpg" width="80px;" alt="Mr.LuCkY"/><br /><sub><b>Mr.LuCkY</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/timeforeverz" target="_blank"><img src="./.image/sponsor/泓.jpg" width="80px;" alt="泓"/><br /><sub><b>泓</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/mySia" target="_blank"><img src="./.image/sponsor/i.jpg" width="80px;" alt="i"/><br /><sub><b>i</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/依依.jpg" width="80px;" alt="依依"/><br /><sub><b>依依</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/sunbirder" target="_blank"><img src="./.image/sponsor/小菜鸟先飞.jpg" width="80px;" alt="小菜鸟先飞"/><br /><sub><b>小菜鸟先飞</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/mmy0" target="_blank"><img src="./.image/sponsor/追溯未来-_-.jpg" width="80px;" alt="追溯未来"/><br /><sub><b>追溯未来</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/ccqingshan" target="_blank"><img src="./.image/sponsor/青衫.jpg" width="80px;" alt="青衫"/><br /><sub><b>青衫</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/jiangchunJava" target="_blank"><img src="./.image/sponsor/Fae.jpg" width="80px;" alt="Fae"/><br /><sub><b>Fae</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/huang-xiangtai" target="_blank"><img src="./.image/sponsor/憨憨.jpg" width="80px;" alt="憨憨"/><br /><sub><b>憨憨</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/gu-beichen-starlight" target="_blank"><img src="./.image/sponsor/文艺小青年.jpg" width="80px;" alt="文艺小青年"/><br /><sub><b>文艺小青年</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/zhangnanchao" target="_blank"><img src="./.image/sponsor/lion.jpg" width="80px;" alt="lion"/><br /><sub><b>lion</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/yupccc" target="_blank"><img src="./.image/sponsor/汪汪队立大功.jpg" width="80px;" alt="汪汪队立大功"/><br /><sub><b>汪汪队立大功</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/wcjjjjjjj" target="_blank"><img src="./.image/sponsor/wcj.jpg" width="80px;" alt="wcj"/><br /><sub><b>wcj</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/hufanglei" target="_blank"><img src="./.image/sponsor/🌹怒放de生命😋.jpg" width="80px;" alt="怒放de生命"/><br /><sub><b>怒放de生命</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/juyunsuan" target="_blank"><img src="./.image/sponsor/蓝速传媒.jpg" width="80px;" alt="蓝速传媒"/><br /><sub><b>蓝速传媒</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/achieve275" target="_blank"><img src="./.image/sponsor/Achieve_Xu.jpg" width="80px;" alt="Achieve_Xu"/><br /><sub><b>Achieve_Xu</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/nicholasld" target="_blank"><img src="./.image/sponsor/NicholasLD.jpg" width="80px;" alt="NicholasLD"/><br /><sub><b>NicholasLD</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/ADVISORYZ" target="_blank"><img src=".image/sponsor/ADVISORYZ.jpg" width="80px;" alt="ADVISORYZ"/><br /><sub><b>ADVISORYZ</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/dongxinji" target="_blank"><img src="./.image/sponsor/take%20your%20time%20or.jpg" width="80px;" alt="take your time or"/><br /><sub><b>take your time or</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/xu756" target="_blank"><img src="./.image/sponsor/碎碎念..jpg" width="80px;" alt="碎碎念."/><br /><sub><b>碎碎念.</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/lwisme" target="_blank"><img src="./.image/sponsor/北街.jpg" width="80px;" alt="北街"/><br /><sub><b>北街</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/yu-xinyan71" target="_blank"><img src="./.image/sponsor/Dorky%20TAT.jpg" width="80px;" alt="Dorky TAT"/><br /><sub><b>Dorky TAT</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/chenxiaohong" target="_blank"><img src=".image/sponsor/右耳向西.jpg" width="80px;" alt="右耳向西"/><br /><sub><b>右耳向西</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/派大星" target="_blank"><img src="./.image/sponsor/派大星.jpg" width="80px;" alt="派大星"/><br /><sub><b>派大星</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/wz_vue_gitee_181" target="_blank"><img src="./.image/sponsor/棒槌🧿🍹🍹🧿.jpg" width="80px;" alt="棒槌🧿🍹🍹🧿"/><br /><sub><b>棒槌</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/nctwo" target="_blank"><img src=".image/sponsor/信微输传助手.jpg" width="80px;" alt="信微输传助手"/><br /><sub><b>信微输传助手</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/l9999_admin" target="_blank"><img src=".image/sponsor/一往无前.jpg" width="80px;" alt="一往无前"/><br /><sub><benen>一往无前</benen></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/stenin" target="_blank"><img src="./.image/sponsor/Charon.jpg" width="80px;" alt="Charon"/><br /><sub><b>Charon</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/zhao-yihuiwifi" target="_blank"><img src="./.image/sponsor/赵WIFI..jpg" width="80px;" alt="赵WIFI."/><br /><sub><b>赵WIFI.</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/Yang619" target="_blank"><img src="./.image/sponsor/Chao..jpg" width="80px;" alt="Chao."/><br /><sub><b>Chao.</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/lcrsd123" target="_blank"><img src=".image/sponsor/城市稻草人.jpg" width="80px;" alt="城市稻草人"/><br /><sub><b>城市稻草人</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/Mo_bai1016" target="_blank"><img src=".image/sponsor/Bug写手墨白.jpg" width="80px;" alt="Bug写手墨白"/><br /><sub><b>Bug写手墨白</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/kevinosc_admin" target="_blank"><img src=".image/sponsor/kevin.jpg" width="80px;" alt="kevin"/><br /><sub><b>kevin</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/lhyicn" target="_blank"><img src=".image/sponsor/童年.jpg" width="80px;" alt="童年"/><br /><sub><b>童年</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/dubai100" target="_blank"><img src="./.image/sponsor/sherry金.jpg" width="80px;" alt="sherry金"/><br /><sub><b>sherry金</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/℡夏别.jpg" width="80px;" alt="℡夏别"/><br /><sub><b>℡夏别</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/翠翠草原.jpg" width="80px;" alt="翠翠草原"/><br /><sub><b>翠翠草原</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/慕容曦.jpg" width="80px;" alt="慕容曦"/><br /><sub><b>慕容曦</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Tyrion.jpg" width="80px;" alt="Tyrion"/><br /><sub><b>Tyrion</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/大漠孤烟.jpg" width="80px;" alt="大漠孤烟"/><br /><sub><b>大漠孤烟</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Return.jpg" width="80px;" alt="Return"/><br /><sub><b>Return</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/一杯拿铁.jpg" width="80px;" alt="一杯拿铁"/><br /><sub><b>一杯拿铁</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Thuri.jpg" width="80px;" alt="Thuri"/><br /><sub><b>Thuri</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Liu.jpg" width="80px;" alt="Liu"/><br /><sub><b>Liu</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/三金.jpg" width="80px;" alt="三金"/><br /><sub><b>三金</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/ZPort.jpg" width="80px;" alt="ZPort"/><br /><sub><b>ZPort</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Li.jpg" width="80px;" alt="Li"/><br /><sub><b>Li</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/嘉树.jpg" width="80px;" alt="嘉树"/><br /><sub><b>嘉树</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/俊采星驰.jpg" width="80px;" alt="俊采星驰"/><br /><sub><b>俊采星驰</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/oi.jpg" width="80px;" alt="oi"/><br /><sub><b>oi</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/ZhangY_000.jpg" width="80px;" alt="ZhangY_000"/><br /><sub><b>ZhangY_000</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/℡夏别.jpg" width="80px;" alt="℡夏别"/><br /><sub><b>℡夏别</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/张瑞麟.jpg" width="80px;" alt="张瑞麟"/><br /><sub><b>张瑞麟</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Lion King.jpg" width="80px;" alt="Lion King"/><br /><sub><b>Lion King</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Frank.jpg" width="80px;" alt="Frank"/><br /><sub><b>Frank</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/徐梦阳.jpg" width="80px;" alt="徐梦阳"/><br /><sub><b>徐梦阳</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/九月.jpg" width="80px;" alt="九月"/><br /><sub><b>九月</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/tangl伟.jpg" width="80px;" alt="tangl伟"/><br /><sub><b>tangl伟</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/冯瑞伦.jpg" width="80px;" alt="冯瑞伦"/><br /><sub><b>冯瑞伦</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/杨林.jpg" width="80px;" alt="杨林"/><br /><sub><b>杨林</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/梧桐有语。.jpg" width="80px;" alt="梧桐有语。"/><br /><sub><b>梧桐有语。</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/歌德de花烛.jpg" width="80px;" alt="歌德de花烛"/><br /><sub><b>歌德de花烛</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/泥嚎.jpg" width="80px;" alt="泥嚎"/><br /><sub><b>泥嚎</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/翠翠草原.jpg" width="80px;" alt="翠翠草原"/><br /><sub><b>翠翠草原</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/胡泽龙.jpg" width="80px;" alt="胡泽龙"/><br /><sub><b>胡泽龙</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/苏叶.jpg" width="80px;" alt="苏叶"/><br /><sub><b>苏叶</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/裴先生.jpg" width="80px;" alt="裴先生"/><br /><sub><b>裴先生</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/谭远彪.jpg" width="80px;" alt="谭远彪"/><br /><sub><b>谭远彪</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/陈祺.jpg" width="80px;" alt="陈祺"/><br /><sub><b>陈祺</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/零点就睡.jpg" width="80px;" alt="零点就睡"/><br /><sub><b>零点就睡</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/风之羽.jpg" width="80px;" alt="风之羽"/><br /><sub><b>风之羽</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/fufeng1908" target="_blank"><img src="./.image/sponsor/王守仁.jpg" width="80px;" alt="王守仁"/><br /><sub><b>王守仁</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/kaigejava" target="_blank"><img src="./.image/sponsor/狼ྂ图ྂ腾ྂ.jpg" width="80px;" alt="狼图腾"/><br /><sub><b>狼图腾</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/马到成功.jpg" width="80px;" alt="马到成功"/><br /><sub><b>马到成功</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/做生活的高手.jpg" width="80px;" alt="做生活的高手"/><br /><sub><b>做生活的高手</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/清欢之恋.jpg" width="80px;" alt="清欢之恋"/><br /><sub><b>清欢之恋</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/绝域时空.jpg" width="80px;" alt="绝域时空"/><br /><sub><b>绝域时空</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/风雨.jpg" width="80px;" alt="风雨"/><br /><sub><b>风雨</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Nicola.jpg" width="80px;" alt="Nicola"/><br /><sub><b>Nicola</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/云住.jpg" width="80px;" alt="云住"/><br /><sub><b>云住</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Mr.Zhang.jpg" width="80px;" alt="Mr.Zhang"/><br /><sub><b>Mr.Zhang</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/剑.jpg" width="80px;" alt="剑"/><br /><sub><b>剑</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/shen.jpg" width="80px;" alt="shen"/><br /><sub><b>shen</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/嗯.jpg" width="80px;" alt="嗯"/><br /><sub><b>嗯</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/周华.jpg" width="80px;" alt="周华"/><br /><sub><b>周华</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/太阳鸟.jpg" width="80px;" alt="太阳鸟"/><br /><sub><b>太阳鸟</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/了了.jpg" width="80px;" alt="了了"/><br /><sub><b>了了</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/第七次日落.jpg" width="80px;" alt="第七次日落"/><br /><sub><b>第七次日落</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/npc.jpg" width="80px;" alt="npc"/><br /><sub><b>npc</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/承担不一样的天空.jpg" width="80px;" alt="承担不一样的天空"/><br /><sub><b>承担不一样的天空</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/铁木.jpg" width="80px;" alt="铁木"/><br /><sub><b>铁木</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Orion.jpg" width="80px;" alt="Orion"/><br /><sub><b>Orion</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/森源-金福洪.jpg" width="80px;" alt="森源-金福洪"/><br /><sub><b>森源-金福洪</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/薛继超.jpg" width="80px;" alt="薛继超"/><br /><sub><b>薛继超</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/虎虎虎.jpg" width="80px;" alt="虎虎虎"/><br /><sub><b>虎虎虎</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Everyman.jpg" width="80px;" alt="Everyman"/><br /><sub><b>Everyman</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/NXL.jpg" width="80px;" alt="NXL"/><br /><sub><b>NXL</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/孙涛.jpg" width="80px;" alt="孙涛"/><br /><sub><b>孙涛</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/bcake" target="_blank"><img src=".image/sponsor/大饼.jpg" width="80px;" alt="大饼"/><br /><sub><b>大饼</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/hrsjw1.jpg" width="80px;" alt="hrsjw1"/><br /><sub><b>hrsjw1</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/linguanghuan.jpg" width="80px;" alt="linguanghuan"/><br /><sub><b>linguanghuan</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/YiYaYiYaho.jpg" width="80px;" alt="YiYaYiYaho"/><br /><sub><b>YiYaYiYaho</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/慢慢慢.jpg" width="80px;" alt="慢慢慢"/><br /><sub><b>慢慢慢</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/lilOne.jpg" width="80px;" alt="lilOne"/><br /><sub><b>lilOne</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src=".image/sponsor/icon.jpg" width="80px;" alt="icon"/><br /><sub><b>icon</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/jiang4yu" target="_blank"><img src=".image/sponsor/山寒.jpg" width="80px;" alt="山寒"/><br /><sub><b>山寒</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/baobaomo" target="_blank"><img src="./.image/sponsor/放学丶别走.jpg" width="80px;" alt="放学丶别走"/><br /><sub><b>放学丶别走</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/wagger" target="_blank"><img src="./.image/sponsor/春和.jpg" width="80px;" alt="春和"/><br /><sub><b>春和</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/longbinwu" target="_blank"><img src="./.image/sponsor/章鱼小丸子.jpg" width="80px;" alt="章鱼小丸子"/><br /><sub><b>章鱼小丸子</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Catwings.jpg" width="80px;" alt="Catwings"/><br /><sub><b>Catwings</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/小工头.jpg" width="80px;" alt="小工头"/><br /><sub><b>小工头</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/西乡一粒沙.jpg" width="80px;" alt="西乡一粒沙"/><br /><sub><b>西乡一粒沙</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/爱吃小柚子.jpg" width="80px;" alt="爱吃小柚子"/><br /><sub><b>爱吃小柚子</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/阿龙.jpg" width="80px;" alt="阿龙"/><br /><sub><b>阿龙</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/雨落流殇.jpg" width="80px;" alt="雨落流殇"/><br /><sub><b>雨落流殇</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/遗忘的星空.jpg" width="80px;" alt="遗忘的星空"/><br /><sub><b>遗忘的星空</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/常康.jpg" width="80px;" alt="常康"/><br /><sub><b>常康</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/嘎嗝.jpg" width="80px;" alt="嘎嗝"/><br /><sub><b>嘎嗝</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/曹.jpg" width="80px;" alt="曹"/><br /><sub><b>曹</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/滔滔.jpg" width="80px;" alt="滔滔"/><br /><sub><b>滔滔</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/狗娃.jpg" width="80px;" alt="狗娃"/><br /><sub><b>狗娃</b></sub></a></td>
    </tr>
  </tbody>
</table>

## 💡 Пожелания

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Добро пожаловать с предложениями по улучшению, которые помогут усовершенствовать easyaiot.
</p>

## 📄 Авторские права

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
翱翔的雄库鲁/easyaiot использует лицензию с открытым исходным кодом <a href="https://gitee.com/soaring-xiongkulu/easyaiot/blob/main/LICENSE" style="color: #3498db; text-decoration: none; font-weight: 600;">MIT LICENSE</a>. Мы стремимся способствовать популяризации и развитию технологий ИИ, позволяя большему количеству людей свободно использовать и получать выгоду от этой технологии.
</p>

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
<strong>Лицензия на использование</strong>: Физические лица и предприятия могут использовать его на 100% бесплатно, без необходимости сохранять информацию об авторе или авторских правах. Мы верим, что ценность технологии заключается в её широком использовании и непрерывном инновационном развитии, а не в ограничениях авторского права. Мы надеемся, что вы сможете свободно использовать, изменять и распространять этот проект, делая технологии ИИ действительно полезными для каждого.
</p>

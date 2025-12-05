# EasyAIoT プラットフォーム デプロイメントドキュメント

## 📋 目次

- [概要](#概要)
- [環境要件](#環境要件)
- [クイックスタート](#クイックスタート)
- [スクリプト使用説明](#スクリプト使用説明)
- [モジュール説明](#モジュール説明)
- [サービスポート](#サービスポート)
- [よくある質問](#よくある質問)
- [ログ管理](#ログ管理)

## 概要

EasyAIoT は、クラウド・エッジ統合型のインテリジェントアルゴリズムアプリケーションプラットフォームであり、統一インストールスクリプトを使用したワンクリックデプロイを採用しています。このプラットフォームは Docker コンテナ化デプロイをサポートし、すべてのサービスモジュールを迅速にインストールおよび起動できます。

### プラットフォームアーキテクチャ

EasyAIoT プラットフォームは、以下のコアモジュールで構成されています：

- **基本サービス** (`.scripts/docker`): Nacos、PostgreSQL、Redis、TDEngine、Kafka、MinIO などのミドルウェアを含みます
- **DEVICE サービス**: デバイス管理およびゲートウェイサービス (Java ベース)
- **AI サービス**: 人工知能処理サービス (Python ベース)
- **VIDEO サービス**: 動画処理サービス (Python ベース)
- **WEB サービス**: Web フロントエンドサービス (Vue ベース)

## 環境要件

### システム要件

- **オペレーティングシステム**:
    - Linux (推奨: Ubuntu 20.04+ または CentOS 7+)
    - macOS (推奨: macOS 10.15+)
    - Windows (推奨: Windows 10/11、PowerShell 5.1+ が必要)
- **メモリ**: 8GB 以上を推奨
- **ディスク**: 利用可能な空き容量 50GB 以上を推奨
- **CPU**: 4 コア以上を推奨

### ソフトウェア依存関係

デプロイメントスクリプトを実行する前に、以下のソフトウェアがインストールされていることを確認してください：

1. **Docker** (必須バージョン v29.0.0+)
    - インストールガイド: https://docs.docker.com/get-docker/
    - インストール確認: `docker --version`
    - **注意**: Docker のバージョンは v29.0.0 以上である必要があります。これより低いバージョンでは正常に動作しません

2. **Docker Compose** (必須バージョン v2.35.0+)
    - インストールガイド: https://docs.docker.com/compose/install/
    - インストール確認: `docker compose version`
    - **注意**: Docker Compose のバージョンは v2.35.0 以上である必要があります。これより低いバージョンでは正常に動作しません

3. **その他の依存関係**:
    - **Linux/macOS**: `curl` (ヘルスチェック用、通常はシステムにプリインストールされています)
    - **Windows**: PowerShell 5.1+ (通常はシステムにプリインストールされています)

### Docker 権限設定

#### Linux

現在のユーザーが Docker デーモンにアクセスする権限を持っていることを確認してください：

```bash
# 方法1: ユーザーを docker グループに追加 (推奨)
sudo usermod -aG docker $USER
# その後、再ログインまたは次のコマンドを実行
newgrp docker

# 方法2: sudo を使用してスクリプトを実行 (非推奨)
sudo ./install_linux.sh [コマンド]
```

Docker 権限を確認：

```bash
docker ps
```

#### macOS

macOS では通常、特別な権限設定は必要ありません。Docker Desktop が自動的に権限を処理します。

#### Windows

Windows では Docker Desktop が自動的に権限を処理します。必要に応じて管理者権限で PowerShell を実行していることを確認してください。

## クイックスタート

### Linux デプロイメント

#### 1. プロジェクトコードの取得

```bash
# プロジェクトをクローン (まだ行っていない場合)
git clone <リポジトリURL>
cd easyaiot
```

#### 2. スクリプトディレクトリへ移動

```bash
cd .scripts/docker
```

#### 3. スクリプトに実行権限を付与

```bash
chmod +x install_linux.sh
```

#### 4. すべてのサービスのワンクリックインストール

```bash
./install_linux.sh install
```

このコマンドは以下の処理を行います：
- Docker と Docker Compose 環境をチェック
- 統一ネットワーク `easyaiot-network` を作成
- 依存関係順にすべてのモジュールをインストール
- すべてのサービスコンテナを起動

#### 5. サービスステータスの確認

```bash
./install_linux.sh verify
```

すべてのサービスが正常に動作している場合、サービスアクセスアドレスが表示されます。

### macOS デプロイメント

#### 1. プロジェクトコードの取得

```bash
# プロジェクトをクローン (まだ行っていない場合)
git clone <リポジトリURL>
cd easyaiot
```

#### 2. スクリプトディレクトリへ移動

```bash
cd .scripts/docker
```

#### 3. スクリプトに実行権限を付与

```bash
chmod +x install_mac.sh
```

#### 4. すべてのサービスのワンクリックインストール

```bash
./install_mac.sh install
```

このコマンドは以下の処理を行います：
- Docker と Docker Compose 環境をチェック
- 統一ネットワーク `easyaiot-network` を作成
- 依存関係順にすべてのモジュールをインストール
- すべてのサービスコンテナを起動

#### 5. サービスステータスの確認

```bash
./install_mac.sh verify
```

すべてのサービスが正常に動作している場合、サービスアクセスアドレスが表示されます。

### Windows デプロイメント

#### 1. プロジェクトコードの取得

```powershell
# プロジェクトをクローン (まだ行っていない場合)
git clone <リポジトリURL>
cd easyaiot
```

#### 2. スクリプトディレクトリへ移動

```powershell
cd .scripts\docker
```

#### 3. 実行ポリシーの設定 (必要な場合)

PowerShell スクリプトを初めて実行する場合、実行ポリシーの設定が必要な場合があります：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 4. すべてのサービスのワンクリックインストール

```powershell
.\install_win.ps1 install
```

このコマンドは以下の処理を行います：
- Docker と Docker Compose 環境をチェック
- 統一ネットワーク `easyaiot-network` を作成
- 依存関係順にすべてのモジュールをインストール
- すべてのサービスコンテナを起動

#### 5. サービスステータスの確認

```powershell
.\install_win.ps1 verify
```

すべてのサービスが正常に動作している場合、サービスアクセスアドレスが表示されます。

## スクリプト使用説明

### スクリプトの場所

統一インストールスクリプトは、プロジェクトルートディレクトリの `.scripts/docker/` ディレクトリにあります：

- **Linux**: `install_linux.sh`
- **macOS**: `install_mac.sh`
- **Windows**: `install_win.ps1`

### 利用可能なコマンド

すべてのオペレーティングシステムで同じコマンドがサポートされていますが、スクリプト名は異なります：

| コマンド | 説明 | Linux 例 | macOS 例 | Windows 例 |
|------|------|-----------|-----------|-------------|
| `install` | すべてのサービスをインストールおよび起動 (初回実行) | `./install_linux.sh install` | `./install_mac.sh install` | `.\install_win.ps1 install` |
| `start` | すべてのサービスを起動 | `./install_linux.sh start` | `./install_mac.sh start` | `.\install_win.ps1 start` |
| `stop` | すべてのサービスを停止 | `./install_linux.sh stop` | `./install_mac.sh stop` | `.\install_win.ps1 stop` |
| `restart` | すべてのサービスを再起動 | `./install_linux.sh restart` | `./install_mac.sh restart` | `.\install_win.ps1 restart` |
| `status` | すべてのサービスのステータスを表示 | `./install_linux.sh status` | `./install_mac.sh status` | `.\install_win.ps1 status` |
| `logs` | すべてのサービスのログを表示 | `./install_linux.sh logs` | `./install_mac.sh logs` | `.\install_win.ps1 logs` |
| `build` | すべてのイメージを再構築 | `./install_linux.sh build` | `./install_mac.sh build` | `.\install_win.ps1 build` |
| `clean` | すべてのコンテナとイメージをクリーンアップ (危険な操作) | `./install_linux.sh clean` | `./install_mac.sh clean` | `.\install_win.ps1 clean` |
| `update` | すべてのサービスを更新および再起動 | `./install_linux.sh update` | `./install_mac.sh update` | `.\install_win.ps1 update` |
| `verify` | すべてのサービスの起動成功を確認 | `./install_linux.sh verify` | `./install_mac.sh verify` | `.\install_win.ps1 verify` |

### コマンド詳細説明

#### install - サービスをインストール

初回デプロイ時に使用します。すべてのサービスモジュールをインストールおよび起動します：

**Linux/macOS**:
```bash
./install_linux.sh install    # Linux
./install_mac.sh install      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 install
```

**実行フロー**:
1. Docker および Docker Compose 環境をチェック
2. Docker ネットワーク `easyaiot-network` を作成
3. 依存関係順に各モジュールをインストール：
    - 基本サービス (Nacos、PostgreSQL、Redis など)
    - DEVICE サービス
    - AI サービス
    - VIDEO サービス
    - WEB サービス
4. インストール結果の統計を表示

#### start - サービスを起動

インストール済みのすべてのサービスを起動します：

**Linux/macOS**:
```bash
./install_linux.sh start    # Linux
./install_mac.sh start      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 start
```

#### stop - サービスを停止

実行中のすべてのサービスを停止します (逆順で停止)：

**Linux/macOS**:
```bash
./install_linux.sh stop    # Linux
./install_mac.sh stop      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 stop
```

#### restart - サービスを再起動

すべてのサービスを再起動します：

**Linux/macOS**:
```bash
./install_linux.sh restart    # Linux
./install_mac.sh restart      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 restart
```

#### status - ステータスを表示

すべてのサービスの実行ステータスを表示します：

**Linux/macOS**:
```bash
./install_linux.sh status    # Linux
./install_mac.sh status      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 status
```

#### logs - ログを表示

すべてのサービスのログを表示します (直近 100 行)：

**Linux/macOS**:
```bash
./install_linux.sh logs    # Linux
./install_mac.sh logs      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 logs
```

#### build - イメージを構築

すべてのサービスの Docker イメージを再構築します (`--no-cache` オプションを使用)：

**Linux/macOS**:
```bash
./install_linux.sh build    # Linux
./install_mac.sh build      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 build
```

**注意**: 構築プロセスには時間がかかる場合があります。しばらくお待ちください。

#### clean - サービスをクリーンアップ

**⚠️ 危険な操作**: すべてのコンテナ、イメージ、データボリュームを削除します

**Linux/macOS**:
```bash
./install_linux.sh clean    # Linux
./install_mac.sh clean      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 clean
```

実行前に確認が求められます。`y` または `Y` を入力すると続行し、他の入力では操作がキャンセルされます。

**クリーンアップ内容**:
- すべてのサービスコンテナ
- すべてのサービスイメージ
- すべてのデータボリューム
- Docker ネットワーク `easyaiot-network`

#### update - サービスを更新

最新のイメージをプルし、すべてのサービスを再起動します：

**Linux/macOS**:
```bash
./install_linux.sh update    # Linux
./install_mac.sh update      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 update
```

**実行フロー**:
1. 各モジュールの最新イメージをプル
2. すべてのサービスを再起動して新しいイメージを使用

#### verify - サービスを確認

すべてのサービスが正常に起動され、アクセス可能であることを確認します：

**Linux/macOS**:
```bash
./install_linux.sh verify    # Linux
./install_mac.sh verify      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 verify
```

**確認内容**:
- サービスポートがアクセス可能かチェック
- ヘルスチェックエンドポイントが正常に応答するかチェック
- サービスアクセスアドレスを表示

**成功出力例**:
```
[SUCCESS] すべてのサービスが正常に実行されています！

サービスアクセスアドレス:
  基本サービス (Nacos):     http://localhost:8848/nacos
  基本サービス (MinIO):     http://localhost:9000 (API), http://localhost:9001 (Console)
  Deviceサービス (Gateway):  http://localhost:48080
  AIサービス:                http://localhost:5000
  Videoサービス:             http://localhost:6000
  Webフロントエンド:         http://localhost:8888
```

## モジュール説明

### 基本サービス (`.scripts/docker`)

**説明**: プラットフォームの実行に必要なすべてのミドルウェアサービスを含みます

**含まれるサービス**:
- **Nacos**: サービス登録および構成センター
- **PostgreSQL**: リレーショナルデータベース
- **Redis**: キャッシュデータベース
- **TDEngine**: 時系列データベース
- **Kafka**: メッセージキュー
- **MinIO**: オブジェクトストレージサービス

**デプロイメント方法**:
- **Linux**: `install_middleware_linux.sh` スクリプトを使用
- **macOS**: `install_middleware_mac.sh` スクリプトを使用
- **Windows**: `install_middleware_win.ps1` スクリプトを使用

### DEVICE サービス

**説明**: デバイス管理およびゲートウェイサービス。デバイス接続、製品管理、データアノテーション、ルールエンジンなどの機能を提供します

**技術スタック**: Java (Spring Cloud)

**デプロイメント方法**:
- **Linux**: `install_linux.sh` スクリプトを使用
- **macOS**: `install_mac.sh` スクリプトを使用
- **Windows**: `install_win.ps1` スクリプトを使用

**主な機能**:
- デバイス管理
- 製品管理
- データアノテーション
- ルールエンジン
- アルゴリズムストア
- システム管理

### AI サービス

**説明**: 人工知能処理サービス。動画分析と AI アルゴリズムの実行を担当します

**技術スタック**: Python

**デプロイメント方法**:
- **Linux**: `install_linux.sh` スクリプトを使用
- **macOS**: `install_mac.sh` スクリプトを使用
- **Windows**: `install_win.ps1` スクリプトを使用

**主な機能**:
- 動画分析
- AI アルゴリズム実行
- モデル推論

### VIDEO サービス

**説明**: 動画処理サービス。動画ストリーム処理および転送を担当します

**技術スタック**: Python

**デプロイメント方法**:
- **Linux**: `install_linux.sh` スクリプトを使用
- **macOS**: `install_mac.sh` スクリプトを使用
- **Windows**: `install_win.ps1` スクリプトを使用

**主な機能**:
- 動画ストリーム処理
- 動画転送
- ストリーミングサービス

### WEB サービス

**説明**: Web フロントエンドサービス。ユーザーインターフェースを提供します

**技術スタック**: Vue.js

**デプロイメント方法**:
- **Linux**: `install_linux.sh` スクリプトを使用
- **macOS**: `install_mac.sh` スクリプトを使用
- **Windows**: `install_win.ps1` スクリプトを使用

**主な機能**:
- ユーザーインターフェース
- データ可視化
- システム管理インターフェース

## サービスポート

| サービスモジュール | ポート | 説明 | アクセスアドレス |
|---------|------|------|----------|
| Nacos | 8848 | サービス登録および構成センター | http://localhost:8848/nacos |
| MinIO API | 9000 | オブジェクトストレージ API | http://localhost:9000 |
| MinIO Console | 9001 | オブジェクトストレージコンソール | http://localhost:9001 |
| DEVICE Gateway | 48080 | デバイスサービスゲートウェイ | http://localhost:48080 |
| AI サービス | 5000 | AI 処理サービス | http://localhost:5000 |
| VIDEO サービス | 6000 | 動画処理サービス | http://localhost:6000 |
| WEB フロントエンド | 8888 | Web フロントエンドインターフェース | http://localhost:8888 |

### ヘルスチェックエンドポイント

各サービスのヘルスチェックエンドポイント：

| サービスモジュール | ヘルスチェックエンドポイント |
|---------|-------------|
| 基本サービス (Nacos) | `/nacos/actuator/health` |
| DEVICE サービス | `/actuator/health` |
| AI サービス | `/actuator/health` |
| VIDEO サービス | `/actuator/health` |
| WEB サービス | `/health` |

## よくある質問

### 1. Docker 権限の問題

**問題**: スクリプト実行時に「Docker デーモンにアクセスする権限がありません」と表示される

**解決策**:

**Linux**:
```bash
# ユーザーを docker グループに追加
sudo usermod -aG docker $USER

# 再ログインまたは次のコマンドを実行
newgrp docker

# 権限を確認
docker ps
```

**macOS**:
macOS では通常、特別な設定は必要ありません。Docker Desktop が実行されていることを確認してください。

**Windows**:
Windows では Docker Desktop が自動的に権限を処理します。Docker Desktop が実行されていることを確認してください。

### 2. ポートが使用中

**問題**: サービス起動時にポートが既に使用中であると表示される

**解決策**:

**Linux**:
```bash
# ポート使用状況を確認
sudo netstat -tulpn | grep <ポート番号>
# または
sudo lsof -i :<ポート番号>

# ポートを使用しているプロセスを停止するか、サービス構成のポートを変更
```

**macOS**:
```bash
# ポート使用状況を確認
lsof -i :<ポート番号>

# ポートを使用しているプロセスを停止するか、サービス構成のポートを変更
```

**Windows**:
```powershell
# ポート使用状況を確認
netstat -ano | findstr :<ポート番号>

# ポートを使用しているプロセスを停止するか、サービス構成のポートを変更
```

### 3. サービス起動失敗

**問題**: 特定のサービスモジュールの起動に失敗

**解決策**:

**Linux/macOS**:
```bash
# 1. サービスログを確認
./install_linux.sh logs    # Linux
./install_mac.sh logs      # macOS

# 2. 特定モジュールの詳細ログを確認
cd <モジュールディレクトリ>
docker-compose logs

# 3. Docker リソースを確認
docker ps -a
docker images

# 4. ネットワークを確認
docker network ls
docker network inspect easyaiot-network
```

**Windows**:
```powershell
# 1. サービスログを確認
.\install_win.ps1 logs

# 2. 特定モジュールの詳細ログを確認
cd <モジュールディレクトリ>
docker-compose logs

# 3. Docker リソースを確認
docker ps -a
docker images

# 4. ネットワークを確認
docker network ls
docker network inspect easyaiot-network
```

### 4. イメージ構築失敗

**問題**: イメージ構築中に失敗

**解決策**:

**Linux/macOS**:
```bash
# 1. Docker ディスク容量を確認
docker system df

# 2. 未使用リソースをクリーンアップ
docker system prune -a

# 3. ネットワーク接続を確認 (ベースイメージのプルが必要な場合)
ping registry-1.docker.io

# 4. 失敗モジュールのイメージを個別に構築
cd <モジュールディレクトリ>
docker-compose build --no-cache
```

**Windows**:
```powershell
# 1. Docker ディスク容量を確認
docker system df

# 2. 未使用リソースをクリーンアップ
docker system prune -a

# 3. ネットワーク接続を確認 (ベースイメージのプルが必要な場合)
Test-NetConnection registry-1.docker.io -Port 443

# 4. 失敗モジュールのイメージを個別に構築
cd <モジュールディレクトリ>
docker-compose build --no-cache
```

### 5. サービスにアクセスできない

**問題**: サービスは起動しているが、ブラウザからアクセスできない

**解決策**:

**Linux**:
```bash
# 1. サービスが正常に実行されていることを確認
./install_linux.sh verify

# 2. ファイアウォール設定を確認
sudo ufw status
# ポートを開放する場合
sudo ufw allow <ポート番号>

# 3. サービスログを確認
./install_linux.sh logs

# 4. コンテナステータスを確認
docker ps
```

**macOS**:
```bash
# 1. サービスが正常に実行されていることを確認
./install_mac.sh verify

# 2. ファイアウォール設定を確認 (システム環境設定 > セキュリティとプライバシー > ファイアウォール)

# 3. サービスログを確認
./install_mac.sh logs

# 4. コンテナステータスを確認
docker ps
```

**Windows**:
```powershell
# 1. サービスが正常に実行されていることを確認
.\install_win.ps1 verify

# 2. ファイアウォール設定を確認 (Windows ファイアウォール設定)

# 3. サービスログを確認
.\install_win.ps1 logs

# 4. コンテナステータスを確認
docker ps
```

### 6. データ損失問題

**問題**: サービスをクリーンアップした後にデータが失われる

**説明**: `clean` コマンドはすべてのデータボリュームを削除するため、データ損失が発生します。これは期待される動作です。

**予防措置**:
- `clean` を実行する前に重要なデータをバックアップ
- 本番環境では `clean` コマンドの使用に注意
- データボリュームのバックアップツールの使用を推奨

## ログ管理

### ログファイルの場所

スクリプト実行ログは `.scripts/docker/logs/` ディレクトリに保存されます：

- **Linux**: `install_linux_YYYYMMDD_HHMMSS.log`
- **macOS**: `install_mac_YYYYMMDD_HHMMSS.log`
- **Windows**: `install_win_YYYYMMDD_HHMMSS.log`

ログファイル名にはタイムスタンプが含まれており、異なる実行記録を区別しやすくなっています。

### ログの表示

#### スクリプト実行ログの表示

**Linux/macOS**:
```bash
# 最新のログファイルを表示
ls -lt .scripts/docker/logs/ | head -5

# 特定のログファイルを表示
tail -f .scripts/docker/logs/install_linux_20240101_120000.log    # Linux
tail -f .scripts/docker/logs/install_mac_20240101_120000.log      # macOS
```

**Windows**:
```powershell
# 最新のログファイルを表示
Get-ChildItem .scripts\docker\logs\ | Sort-Object LastWriteTime -Descending | Select-Object -First 5

# 特定のログファイルを表示
Get-Content .scripts\docker\logs\install_win_20240101_120000.log -Wait
```

#### サービスコンテナログの表示

**Linux/macOS**:
```bash
# すべてのサービスログを表示
./install_linux.sh logs    # Linux
./install_mac.sh logs      # macOS

# 特定サービスのログを表示 (対応するモジュールディレクトリに移動する必要があります)
cd DEVICE
docker-compose logs -f
```

**Windows**:
```powershell
# すべてのサービスログを表示
.\install_win.ps1 logs

# 特定サービスのログを表示 (対応するモジュールディレクトリに移動する必要があります)
cd DEVICE
docker-compose logs -f
```

### ログの内容

スクリプトログには以下が含まれます：
- 実行タイムスタンプ
- 実行されたコマンド
- 各モジュールの実行結果
- エラーメッセージと警告
- サービスステータス情報

## デプロイメントプロセス推奨事項

### 初回デプロイメント

#### Linux

1. **環境準備**
   ```bash
   # システム要件を確認
   uname -a
   free -h
   df -h

   # Docker および Docker Compose をインストール
   # 参考: https://docs.docker.com/get-docker/
   ```

2. **コード取得**
   ```bash
   git clone <リポジトリURL>
   cd easyaiot
   ```

3. **インストール実行**
   ```bash
   cd .scripts/docker
   chmod +x install_linux.sh
   ./install_linux.sh install
   ```

4. **デプロイメント確認**
   ```bash
   ./install_linux.sh verify
   ```

5. **サービスへのアクセス**
    - ブラウザを開き、各サービスアドレスにアクセス
    - サービスが正常に動作していることを確認

#### macOS

1. **環境準備**
   ```bash
   # システム要件を確認
   uname -a
   system_profiler SPHardwareDataType | grep Memory
   df -h

   # Docker Desktop for Mac をインストール
   # 参考: https://docs.docker.com/desktop/install/mac-install/
   ```
2. **コード取得**
   ```bash
   git clone <リポジトリURL>
   cd easyaiot
   ```

3. **インストール実行**
   ```bash
   cd .scripts/docker
   chmod +x install_mac.sh
   ./install_mac.sh install
   ```

4. **デプロイメント確認**
   ```bash
   ./install_mac.sh verify
   ```

5. **サービスへのアクセス**
    - ブラウザを開き、各サービスアドレスにアクセス
    - サービスが正常に動作していることを確認

#### Windows

1. **環境準備**
   ```powershell
   # システム要件を確認
   systeminfo | findstr /C:"OS Name" /C:"Total Physical Memory"

   # Docker Desktop for Windows をインストール
   # 参考: https://docs.docker.com/desktop/install/windows-install/
   ```

2. **コード取得**
   ```powershell
   git clone <リポジトリURL>
   cd easyaiot
   ```

3. **インストール実行**
   ```powershell
   cd .scripts\docker
   .\install_win.ps1 install
   ```

4. **デプロイメント確認**
   ```powershell
   .\install_win.ps1 verify
   ```

5. **サービスへのアクセス**
    - ブラウザを開き、各サービスアドレスにアクセス
    - サービスが正常に動作していることを確認

### 日常的な運用管理

#### Linux/macOS

1. **サービス起動**
   ```bash
   ./install_linux.sh start    # Linux
   ./install_mac.sh start      # macOS
   ```

2. **サービス停止**
   ```bash
   ./install_linux.sh stop    # Linux
   ./install_mac.sh stop      # macOS
   ```

3. **サービス再起動**
   ```bash
   ./install_linux.sh restart    # Linux
   ./install_mac.sh restart      # macOS
   ```

4. **ステータス表示**
   ```bash
   ./install_linux.sh status    # Linux
   ./install_mac.sh status      # macOS
   ```

5. **ログ表示**
   ```bash
   ./install_linux.sh logs    # Linux
   ./install_mac.sh logs      # macOS
   ```

#### Windows

1. **サービス起動**
   ```powershell
   .\install_win.ps1 start
   ```

2. **サービス停止**
   ```powershell
   .\install_win.ps1 stop
   ```

3. **サービス再起動**
   ```powershell
   .\install_win.ps1 restart
   ```

4. **ステータス表示**
   ```powershell
   .\install_win.ps1 status
   ```

5. **ログ表示**
   ```powershell
   .\install_win.ps1 logs
   ```

### デプロイメントの更新

#### Linux/macOS

1. **最新コードのプル**
   ```bash
   git pull
   ```

2. **サービスの更新**
   ```bash
   cd .scripts/docker
   ./install_linux.sh update    # Linux
   ./install_mac.sh update      # macOS
   ```

3. **更新の確認**
   ```bash
   ./install_linux.sh verify    # Linux
   ./install_mac.sh verify      # macOS
   ```

#### Windows

1. **最新コードのプル**
   ```powershell
   git pull
   ```

2. **サービスの更新**
   ```powershell
   cd .scripts\docker
   .\install_win.ps1 update
   ```

3. **更新の確認**
   ```powershell
   .\install_win.ps1 verify
   ```

## 注意事項

1. **バージョン要件**: **必須**で Docker v29.0.0+ および Docker Compose v2.35.0+ をインストールしてください。これより低いバージョンでは正常に動作しません
2. **ネットワーク要件**: サーバーが Docker Hub または設定されたイメージレジストリにアクセスできることを確認してください
3. **リソース要件**: サーバーに十分な CPU、メモリ、およびディスク容量があることを確認してください
4. **ポート競合**: 必要なポートが他のサービスによって使用されていないことを確認してください
5. **データバックアップ**: 本番環境へのデプロイ前にデータをバックアップしてください
6. **セキュリティ設定**: 本番環境では、ファイアウォールとセキュリティグループルールを設定してください
7. **ログ管理**: 古いログファイルを定期的にクリーンアップし、ディスク容量不足を防いでください

## テクニカルサポート

問題が発生した場合は、以下を確認してください：

1. このドキュメントの [よくある質問](#よくある質問) セクションを参照
2. サービスログを確認: `./install_all.sh logs`
3. Docker ステータスを確認: `docker ps -a`
4. プロジェクトリポジトリに Issue を投稿

---

**ドキュメントバージョン**: 1.0
**最終更新日**: 2024-01-01
**スクリプトの場所**: `.scripts/docker/install_all.sh`
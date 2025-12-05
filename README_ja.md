# EasyAIoT（クラウド・エッジ・デバイス統合インテリジェントアルゴリズムアプリケーションプラットフォーム）

[![Gitee star](https://gitee.com/volara/easyaiot/badge/star.svg?theme=gvp)](https://gitee.com/soaring-xiongkulu/easyaiot/stargazers)
[![Gitee fork](https://gitee.com/volara/easyaiot/badge/fork.svg?theme=gvp)](https://gitee.com/soaring-xiongkulu/easyaiot/members)

<p style="font-size: 16px; line-height: 1.8; color: #555; font-weight: 400; margin: 20px 0;">
このシステムが世界中で使われ、AIの真のゼロ障壁を実現し、AIの恩恵を誰もが体験できるようになることを願っています。それはほんの一握りの人々の手にあるだけのものではありません。
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
  <a href="./README_ja.md">日本語</a>
  <span style="display: flex; align-items: center; color: #666; font-weight: bold;">|</span>
  <a href="./README_ko.md">한국어</a>
</h4>

## 🌟 プロジェクトについての考え

### 📍 プロジェクトの位置付け

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoTは、クラウド・エッジ・デバイス統合のインテリジェントIoTプラットフォームで、AIとIoTの深い融合に焦点を当てています。プラットフォームは、アルゴリズムタスク管理、リアルタイムストリーム分析、モデルサービスクラスター推論などの中核機能を通じて、デバイス接続からデータ収集、AI分析、インテリジェント意思決定までの全プロセスを閉じたループで実現し、真の万物接続と万物知能制御を実現します。
</p>

#### 🧠 AI機能

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>カメラリアルタイム映像のAI分析</strong>：カメラリアルタイム映像のAIインテリジェント分析をサポートし、リアルタイムビデオストリームに対して物体検出、行動分析、異常識別などのAIアルゴリズム処理を行い、ミリ秒応答のリアルタイム分析結果を提供し、複数ビデオの同時分析をサポートします。</li>
  <li><strong>クラウド・エッジ・デバイス統合アルゴリズム警告監視ダッシュボード</strong>：統一されたクラウド・エッジ・デバイス統合アルゴリズム警告監視ダッシュボードを提供し、デバイス状態、アルゴリズムタスク実行状況、警告イベント統計、ビデオストリーム分析結果などの重要情報をリアルタイムに表示します。多次元データ可視化表示をサポートし、クラウド、エッジ、デバイスの統一監視と管理を実現し、意思決定者にグローバル視点のインテリジェント監視指揮センターを提供します。</li>
  <li><strong>大規模カメラ管理</strong>：数百台規模のカメラ接続をサポートし、収集、ラベル付け、トレーニング、推論、エクスポート、分析、警告、録画、保存、デプロイなどの全プロセスサービスを提供します。</li>
  <li><strong>アルゴリズムタスク管理</strong>：2種類のアルゴリズムタスクの作成と管理をサポートし、各アルゴリズムタスクはフレーム抽出器とソーターを柔軟にバインドして、正確なビデオフレーム抽出と結果のソートを実現します。
    <ul style="margin: 5px 0; padding-left: 20px;">
      <li><strong>リアルタイムアルゴリズムタスク</strong>：リアルタイム映像分析に使用され、RTSP/RTMPストリームのリアルタイム処理をサポートし、ミリ秒応答能力を提供し、監視、セキュリティなどのリアルタイムシナリオに適しています。</li>
      <li><strong>撮影アルゴリズムタスク</strong>：撮影画像分析に使用され、撮影画像のインテリジェント認識と分析を行い、イベントバックトラッキング、画像検索などのシナリオに適しています。</li>
    </ul>
  </li>
  <li><strong>モデルサービスクラスター推論</strong>：分散型モデル推論サービスクラスターをサポートし、インテリジェント負荷分散、自動フェイルオーバー、高可用性保証を実現し、推論スループットとシステム安定性を大幅に向上させます。</li>
  <li><strong>警戒時間帯管理</strong>：全警戒モードと半警戒モードの2つの警戒戦略をサポートし、異なる時間帯の警戒ルールを柔軟に設定し、正確な時間帯別インテリジェント監視と警告を実現します。</li>
  <li><strong>OCRと音声認識</strong>：PaddleOCRベースの高精度文字認識を実装し、音声からテキストへの変換機能をサポートし、多言語認識能力を提供します。</li>
  <li><strong>マルチモーダル視覚大規模モデル</strong>：物体認識、文字認識など様々な視覚タスクをサポートし、強力な画像理解とシーン分析能力を提供します。</li>
  <li><strong>LLM大規模言語モデル</strong>：RTSPストリーム、ビデオ、画像、音声、テキストなど様々な入力形式のインテリジェント分析と理解をサポートし、マルチモーダルコンテンツ理解を実現します。</li>
  <li><strong>モデルデプロイとバージョン管理</strong>：AIモデルの迅速なデプロイとバージョン管理をサポートし、モデルのワンクリック公開、バージョンロールバック、段階的公開を実現します。</li>
  <li><strong>マルチインスタンス管理</strong>：複数のモデルインスタンスの同時実行とリソーススケジューリングをサポートし、システム利用率とリソース利用効率を向上させます。</li>
  <li><strong>カメラ撮影</strong>：カメラリアルタイム撮影機能をサポートし、撮影ルールとトリガー条件を設定でき、インテリジェントな撮影とイベント記録を実現します。</li>
  <li><strong>撮画保存領域管理</strong>：撮画画像の保存領域管理を提供し、領域割り当てとクリーンアップポリシーをサポートし、ストレージリソースの適切な利用を確保します。</li>
  <li><strong>録画領域管理</strong>：録画ファイルの保存領域管理を提供し、自動クリーンアップとアーカイブをサポートし、ストレージリソースのインテリジェント管理を実現します。</li>
  <li><strong>撮画画像管理</strong>：撮画画像の表示、検索、ダウンロード、削除などのライフサイクル管理をサポートし、便利な画像管理機能を提供します。</li>
  <li><strong>デバイスディレクトリ管理</strong>：デバイスのツリーディレクトリ管理を提供し、デバイスグループ化、階層管理、権限制御をサポートし、デバイスの秩序ある組織化と詳細な管理を実現します。</li>
  <li><strong>警告録画</strong>：警告イベント自動トリガー録画機能をサポートし、異常イベントを検出すると関連ビデオクリップを自動録画し、完全な警告証拠連鎖を提供し、警告録画の表示、ダウンロード、管理をサポートします。</li>
  <li><strong>警告イベント</strong>：完全な警告イベント管理機能を提供し、警告イベントのリアルタイムプッシュ、履歴照会、統計分析、イベント処理、状態追跡をサポートし、警告の全ライフサイクル管理を実現します。</li>
  <li><strong>録画再生</strong>：履歴録画の高速検索と再生機能をサポートし、タイムライン位置指定、倍速再生、キーフレームジャンプなどの便利な操作を提供し、複数ビデオの同期再生をサポートし、イベントバックトラッキングと分析のニーズを満たします。</li>
</ul>

#### 🌐 IoT機能

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>デバイス接続と管理</strong>：デバイス登録、認証、状態監視、ライフサイクル管理</li>
  <li><strong>製品と物モデル管理</strong>：製品定義、物モデル設定、製品管理</li>
  <li><strong>マルチプロトコルサポート</strong>：MQTT、TCP、HTTPなどの様々なIoTプロトコル</li>
  <li><strong>デバイス認証と動的登録</strong>：安全な接続、身元認証、動的デバイス登録</li>
  <li><strong>ルールエンジン</strong>：データ転送ルール、メッセージルーティング、データ変換</li>
  <li><strong>データ収集と保存</strong>：デバイスデータ収集、保存、照会、分析</li>
  <li><strong>デバイス状態監視と警告管理</strong>：リアルタイム監視、異常警告、インテリジェント意思決定</li>
</ul>

### 💡 技術理念

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
私たちは、すべてのことにおいて優れたプログラミング言語は存在しないと考えていますが、3つのプログラミング言語の深い融合を通じて、EasyAIoTはそれぞれの利点を生かし、強力な技術エコシステムを構築します。
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Javaは安定した信頼性の高いプラットフォームアーキテクチャの構築に優れていますが、ネットワークプログラミングやAIプログラミングには適していません。PythonはネットワークプログラミングやAIアルゴリズム開発に優れていますが、高性能タスク実行にはボトルネックがあります。C++は高性能タスク実行に優れていますが、プラットフォーム開発やAIプログラミングでは前者に劣ります。EasyAIoTは3言語混合アーキテクチャを採用し、各言語の利点を十分に発揮させ、実装はかなり挑戦的ですが、使用は非常に便利なAIoTプラットフォームを構築します。
</p>

![EasyAIoTプラットフォームアーキテクチャ.jpg](.image/iframe2.jpg)

### 🔄 モジュールデータフロー

<img src=".image/iframe3.jpg" alt="EasyAIoTプラットフォームアーキテクチャ" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

### 🤖 ゼロショットラベル付け技術

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
革新的に大規模モデルに基づくゼロショットラベル付け技術システムを構築し（理想的には人工ラベル付けプロセスを完全に除去し、ラベル付けプロセスの自動化を実現）、この技術は大規模モデルが初期データを生成し、プロンプト技術を活用して自動ラベル付けを完了し、人間と機械の協同検証を経てデータ品質を確保し（オプション）、さらに初期の小型モデルをトレーニングします。この小型モデルは継続的な反復と自己最適化を通じて、ラベル付け効率とモデル精度の協調的進化を実現し、最終的にシステム性能を絶えず向上させます。
</p>

<img src=".image/iframe4.jpg" alt="EasyAIoTプラットフォームアーキテクチャ" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

### 🏗️ プロジェクトアーキテクチャの特徴

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
EasyAIoTは実は1つのプロジェクトではなく、5つのプロジェクトです。
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
利点は何でしょうか？例えば、制約のあるデバイス（RK3588など）では、その中の特定のプロジェクトだけを取り出して独立してデプロイできるため、このプロジェクトはクラウドプラットフォームに見えますが、実際にはエッジプラットフォームにもなり得ます。
</p>

<div style="margin: 30px 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;">

<p style="font-size: 16px; line-height: 1.8; margin: 0; font-weight: 500;">
🌟 真のオープンソースは容易ではありません。このプロジェクトがお役に立ちましたら、Starを点灯してから離れることをお願いします。これが私への最大のサポートとなります！<br>
<small style="font-size: 14px; opacity: 0.9;">（偽のオープンソースが横行するこの時代に、このプロジェクトは異質な存在であり、純粋に愛によって発電しています）</small>
</p>

</div>

### 🌍 ローカライズサポート

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoTはローカライズ戦略に積極的に応え、ローカルハードウェアとオペレーティングシステムを全面的にサポートし、ユーザーに安全で制御可能なAIoTソリューションを提供します：
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🖥️ サーバー側サポート</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>ハイゴン（Hygon）x86アーキテクチャプロセッサとの完全互換性</li>
  <li>ローカライズされたサーバーハードウェアプラットフォームのサポート</li>
  <li>ターゲットを絞った性能最適化ソリューションの提供</li>
  <li>エンタープライズアプリケーションの安定稼働の確保</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">📱 エッジ側サポート</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>ロックチップ（Rockchip）ARMアーキテクチャチップの全面サポート</li>
  <li>RK3588などの主流エッジコンピューティングプラットフォームとの完全互換性</li>
  <li>エッジシナリオ向けの深い最適化</li>
  <li>エッジインテリジェンスの軽量デプロイの実現</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🖱️ オペレーティングシステムサポート</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>麒麟（Kylin）オペレーティングシステムとの互換性</li>
  <li>方徳（Founder）などのローカライズされたLinuxディストリビューションのサポート</li>
  <li>統信UOSなどの主流ローカライズオペレーティングシステムへの対応</li>
  <li>完全なローカライズデプロイソリューションの提供</li>
</ul>
</div>

</div>

## 🎯 適用シナリオ

<img src=".image/適用场景.png" alt="適用シナリオ" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

## 🧩 プロジェクト構造

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoTは5つのコアプロジェクトで構成されています：
</p>

<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50; width: 20%;">モジュール</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50;">説明</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>WEBモジュール</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">Vueベースのフロントエンド管理インターフェースで、統一されたユーザーインタラクション体験を提供します。</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>DEVICEモジュール</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>技術的利点</strong>：JDK21ベースで、より良いパフォーマンスと現代的特性を提供します。</li>
    <li><strong>デバイス管理</strong>：デバイス登録、認証、状態監視、ライフサイクル管理</li>
    <li><strong>製品管理</strong>：製品定義、物モデル管理、製品設定</li>
    <li><strong>プロトコルサポート</strong>：MQTT、TCP、HTTPなどの様々なIoTプロトコル</li>
    <li><strong>デバイス認証</strong>：デバイス動的登録、身元認証、安全な接続</li>
    <li><strong>ルールエンジン</strong>：データ転送ルール、メッセージルーティング、データ変換</li>
    <li><strong>データ収集</strong>：デバイスデータ収集、保存、照会、分析</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>VIDEOモジュール</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>ストリーミングメディア処理</strong>：RTSP/RTMPストリームのリアルタイム処理と転送をサポート</li>
    <li><strong>アルゴリズムタスク管理</strong>：リアルタイムアルゴリズムタスクと撮影アルゴリズムタスクの2種類をサポートし、それぞれリアルタイム映像分析と撮影画像分析に使用されます。</li>
    <li><strong>フレーム抽出器とソーター</strong>：柔軟なフレーム抽出戦略と結果ソートメカニズムをサポートし、各アルゴリズムタスクは独立したフレーム抽出器とソーターをバインドできます。</li>
    <li><strong>警戒時間帯</strong>：全警戒モードと半警戒モードの時間帯別設定をサポート</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>AIモジュール</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>インテリジェント分析</strong>：ビデオ分析とAIアルゴリズム実行を担当します。</li>
    <li><strong>モデルサービスクラスター</strong>：分散型モデル推論サービスをサポートし、負荷分散と高可用性を実現します。</li>
    <li><strong>リアルタイム推論</strong>：ミリ秒応答のリアルタイムインテリジェント分析能力を提供します。</li>
    <li><strong>モデル管理</strong>：モデルデプロイ、バージョン管理、マルチインスタンススケジューリングをサポートします。</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>TASKモジュール</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">C++ベースの高性能タスク処理モジュールで、計算集約型タスクの実行を担当します。</td>
</tr>
</table>

## 🖥️ クロスプラットフォームデプロイの利点

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoTはLinux、Mac、Windowsの3つの主流オペレーティングシステムでのデプロイをサポートし、異なる環境下のユーザーに柔軟で便利なデプロイソリューションを提供します：
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🐧 Linuxデプロイの利点</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>本番環境に適し、安定性が高く、リソース消費が少ない</li>
  <li>Dockerコンテナ化デプロイをサポートし、すべてのサービスをワンクリックで起動</li>
  <li>サーバー、エッジコンピューティングデバイス（RK3588などのARMアーキテクチャデバイス）との完全互換性</li>
  <li>完全な自動インストールスクリプトを提供し、デプロイプロセスを簡素化</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🍎 Macデプロイの利点</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>開発テスト環境に適し、macOSシステムとの深い統合</li>
  <li>ローカル開発とデバッグをサポートし、機能の迅速な検証</li>
  <li>便利なインストールスクリプトを提供し、Homebrewなどのパッケージマネージャーをサポート</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🪟 Windowsデプロイの利点</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Windowsサーバー環境に適し、学習コストを低減</li>
  <li>PowerShell自動化スクリプトをサポートし、デプロイ操作を簡素化</li>
  <li>Windows Serverとデスクトップ版Windowsシステムとの互換性</li>
  <li>グラフィカルインストールウィザードを提供し、ユーザーフレンドリー</li>
</ul>
</div>

</div>

<p style="font-size: 14px; line-height: 1.8; color: #e74c3c; font-weight: 500; margin: 20px 0; padding: 15px; background-color: #fee; border-left: 4px solid #e74c3c; border-radius: 4px;">
<strong>⚠️ Windowsデプロイに関する説明</strong>：Windowsワンクリックデプロイスクリプトは現在まだ問題があり、短期的には関連問題は解決されません。Windowsユーザーはデプロイドキュメントを参照して手動デプロイを行うか、Linux/Mac環境を使用してデプロイすることをお勧めします。
</p>

<p style="font-size: 14px; line-height: 1.8; color: #2c3e50; font-weight: 500; margin: 20px 0; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #3498db; border-radius: 4px;">
<strong>統一された体験</strong>：どのオペレーティングシステムを選択しても、EasyAIoTは一貫したインストールスクリプトとデプロイドキュメントを提供し、クロスプラットフォームデプロイ体験の一貫性を確保します。
</p>

## ☁️ EasyAIoT = AI + IoT = クラウド・エッジ・デバイス統合ソリューション

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
何千もの垂直シナリオをサポートし、AIモデルのカスタマイズとAIアルゴリズムのカスタマイズ開発をサポートし、深く融合します。
</p>

<div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3498db;">
<h3 style="color: #2c3e50; margin-top: 0;">万物知能視覚化を実現：EasyAIoT</h3>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
IoTデバイス（特に膨大な数のカメラ）の効率的な接続と管理ネットワークを構築しました。私たちはストリーミングメディアリアルタイム伝送技術と最先端人工知能（AI）を深く融合させ、統合サービスのコアを構築しています。このソリューションは異種デバイスの相互接続を実現するだけでなく、高画質ビデオストリームと強力なAI解析エンジンを深く統合し、監視システムに「知能の目」を与えます——正確な顔認識、異常行動分析、リスク要員管理、境界侵入検出を実現します。
</p>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
プラットフォームは2種類のアルゴリズムタスクをサポートします：リアルタイムアルゴリズムタスクはRTSP/RTMPストリームのリアルタイム映像分析に使用され、ミリ秒応答能力を提供します。撮影アルゴリズムタスクは撮影画像のインテリジェント分析に使用され、イベントバックトラッキングと画像検索をサポートします。アルゴリズムタスク管理を通じて柔軟なフレーム抽出とソート戦略を実現し、各タスクは独立したフレーム抽出器とソーターをバインドでき、モデルサービスクラスター推論能力と組み合わせて、ミリ秒応答と高可用性保証を確保します。同時に、全警戒モードと半警戒モードの2つの警戒戦略を提供し、異なる時間帯に応じて柔軟に監視ルールを設定し、正確な時間帯別インテリジェント監視と警告を実現します。
</p>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
IoTデバイス管理において、EasyAIoTは完全なデバイスライフサイクル管理能力を提供し、様々なIoTプロトコル（MQTT、TCP、HTTP）をサポートし、デバイスの迅速な接続、安全な認証、リアルタイム監視、インテリジェント制御を実現します。ルールエンジンを通じてデバイスデータのインテリジェントな転送と処理を実現し、AI機能と組み合わせてデバイスデータを深く分析し、デバイス接続、データ収集、インテリジェント分析から意思決定実行までの全プロセスの自動化を実現し、真の万物接続と万物知能制御を実現します。
</p>
</div>

<img src=".image/iframe1.jpg" alt="EasyAIoTプラットフォームアーキテクチャ" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">

## ⚠️ 免責事項

EasyAIoTはオープンソース学習プロジェクトであり、商業行為とは関係ありません。ユーザーはこのプロジェクトを使用する際、法律規制を遵守し、違法行為を行ってはなりません。EasyAIoTがユーザーに違法行為があることを発見した場合、関連機関の調査に協力し、政府部門に報告します。ユーザーの違法行為によるいかなる法的責任もユーザー自身が負うものとし、ユーザーの使用により第三者に損害が生じた場合、ユーザーは法律に基づいて賠償するものとします。EasyAIoTのすべての関連リソースの使用はユーザー自身の責任で行うものとします。

## 📚 デプロイドキュメント

- [プラットフォームデプロイドキュメント](.doc/部署文档/平台部署文档_ja.md)

## 🎮 デモ環境

- デモアドレス：http://36.111.47.113:8888/
- アカウント：admin
- パスワード：admin123

## ⚙️ プロジェクトアドレス

- Gitee: https://gitee.com/soaring-xiongkulu/easyaiot
- Github: https://github.com/soaring-xiongkulu/easyaiot

## 📸 スクリーンショット
<div>
  <img src=".image/banner/banner-video1000.gif" alt="Screenshot 1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner-video1001.gif" alt="Screenshot 1" width="49%">
</div>
<div>
  <img src=".image/banner/banner1001.png" alt="Screenshot 1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1076.jpg" alt="Screenshot 1" width="49%">
</div>
<div>
  <img src=".image/banner/banner1074.jpg" alt="Screenshot 1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1075.jpg" alt="Screenshot 1" width="49%">
</div>
<div>
  <img src=".image/banner/banner1078.jpg" alt="Screenshot 1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1077.jpg" alt="Screenshot 1" width="49%">
</div>
<div>
  <img src=".image/banner/banner1006.jpg" alt="Screenshot 3" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1009.jpg" alt="Screenshot 1" width="49%">
</div>
<div>
  <img src=".image/banner/banner1051.jpg" alt="Screenshot 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1053.jpg" alt="Screenshot 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1062.jpg" alt="Screenshot 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1063.png" alt="Screenshot 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1064.jpg" alt="Screenshot 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1065.jpg" alt="Screenshot 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1066.jpg" alt="Screenshot 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1067.jpg" alt="Screenshot 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1052.jpg" alt="Screenshot 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1054.jpg" alt="Screenshot 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1055.jpg" alt="Screenshot 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1056.jpg" alt="Screenshot 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1057.jpg" alt="Screenshot 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1058.jpg" alt="Screenshot 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1068.jpg" alt="Screenshot 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1069.jpg" alt="Screenshot 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1026.jpg" alt="Screenshot 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1028.jpg" alt="Screenshot 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1029.jpg" alt="Screenshot 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1030.jpg" alt="Screenshot 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1072.jpg" alt="Screenshot 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1031.jpg" alt="Screenshot 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1070.jpg" alt="Screenshot 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1071.jpg" alt="Screenshot 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1033.jpg" alt="Screenshot 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1035.jpg" alt="Screenshot 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1034.jpg" alt="Screenshot 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1036.jpg" alt="Screenshot 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1037.jpg" alt="Screenshot 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1038.jpg" alt="Screenshot 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1015.png" alt="Screenshot 5" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1010.jpg" alt="Screenshot 3" width="49%">
</div>
<div>
  <img src=".image/banner/banner1027.png" alt="Screenshot 2" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1016.jpg" alt="Screenshot 6" width="49%">
</div>
<div>
  <img src=".image/banner/banner1059.jpg" alt="Screenshot 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1060.jpg" alt="Screenshot 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1007.jpg" alt="Screenshot 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1008.jpg" alt="Screenshot 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1019.jpg" alt="Screenshot 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1020.jpg" alt="Screenshot 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1023.jpg" alt="Screenshot 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1024.jpg" alt="Screenshot 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1017.jpg" alt="Screenshot 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1018.jpg" alt="Screenshot 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1039.jpg" alt="Screenshot 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1061.jpg" alt="Screenshot 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1040.jpg" alt="Screenshot 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1042.jpg" alt="Screenshot 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1043.jpg" alt="Screenshot 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1044.jpg" alt="Screenshot 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1021.jpg" alt="Screenshot 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1022.jpg" alt="Screenshot 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1045.jpg" alt="Screenshot 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1046.jpg" alt="Screenshot 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1047.jpg" alt="Screenshot 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1048.jpg" alt="Screenshot 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1049.jpg" alt="Screenshot 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1050.jpg" alt="Screenshot 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1013.jpg" alt="Screenshot 9" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1014.png" alt="Screenshot 10" width="49%">
</div>
<div>
  <img src=".image/banner/banner1003.png" alt="Screenshot 13" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1004.png" alt="Screenshot 14" width="49%">
</div>
<div>
  <img src=".image/banner/banner1005.png" alt="Screenshot 15" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1002.png" alt="Screenshot 16" width="49%">
</div>

## 🛠️ サービスサポート

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoTプラットフォームとコードを深く理解していただくための様々なサービス方法を提供しています。製品ドキュメント、技術交流グループ、有料トレーニングなどを通じて、以下のサービスを受けることができます：
</p>

<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
<thead>
<tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
<th style="padding: 15px; text-align: left; font-weight: 600;">サービス項目</th>
<th style="padding: 15px; text-align: left; font-weight: 600;">サービス内容</th>
<th style="padding: 15px; text-align: center; font-weight: 600;">サービス料金</th>
<th style="padding: 15px; text-align: left; font-weight: 600;">サービス方法</th>
</tr>
</thead>
<tbody>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50;">システムデプロイ</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">お客様が指定したネットワークとハードウェア環境でEasyAIoTデプロイを完了します。</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; text-align: center; color: #e74c3c; font-weight: 600;">500元</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">オンラインデプロイサポート</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50;">技術サポート</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">様々なデプロイ、機能使用中に発生する問題の回答を提供します。</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; text-align: center; color: #e74c3c; font-weight: 600;">200元</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">30分以内 オンラインリモートサポート</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50;">その他サービス</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">垂直領域ソリューションのカスタマイズ開発；カスタマイズ期間、機能サービスなど</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; text-align: center; color: #e74c3c; font-weight: 600;">要相談</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">要相談</td>
</tr>
</tbody>
</table>

## 📞 連絡先（WeChat追加後、公式アカウントをフォローし、技術交流グループに招待）

<div>
  <img src=".image/联系方式.jpg" alt="連絡先" width="30%">
</div>

## 👥 公式アカウント

<div>
  <img src=".image/公众号.jpg" alt="公式アカウント" width="30%">
</div>

## 🪐 ナレッジプラネット：

<p>
  <img src=".image/知识星球.jpg" alt="ナレッジプラネット" width="30%">
</p>

## 💰 寄付・スポンサー

<div>
    <img src=".image/微信支付.jpg" alt="WeChat Pay" width="30%" height="30%">
    <img src=".image/支付宝支付.jpg" alt="Alipay" width="30%" height="10%">
</div>

## 🙏 謝辞

以下の皆様の、コード貢献、問題フィードバック、資金寄付など様々な方法での本プロジェクトへのサポートに感謝いたします！以下は順不同です：
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/bcake" target="_blank"><img src=".image/sponsor/大饼.jpg" width="80px;" alt="大饼"/><br /><sub><b>大饼</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/jiang4yu" target="_blank"><img src=".image/sponsor/山寒.jpg" width="80px;" alt="山寒"/><br /><sub><b>山寒</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/baobaomo" target="_blank"><img src="./.image/sponsor/放学丶别走.jpg" width="80px;" alt="放学丶别走"/><br /><sub><b>放学丶别走</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/wagger" target="_blank"><img src="./.image/sponsor/春和.jpg" width="80px;" alt="春和"/><br /><sub><b>春和</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/longbinwu" target="_blank"><img src="./.image/sponsor/章鱼小丸子.jpg" width="80px;" alt="章鱼小丸子"/><br /><sub><b>章鱼小丸子</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Catwings.jpg" width="80px;" alt="Catwings"/><br /><sub><b>Catwings</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/小工头.jpg" width="80px;" alt="小工头"/><br /><sub><b>小工头</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/西乡一粒沙.jpg" width="80px;" alt="西乡一粒沙"/><br /><sub><b>西乡一粒沙</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/L_Z_M" target="_blank"><img src=".image/sponsor/玖零。.jpg" width="80px;" alt="玖零。"/><br /><sub><b>玖零。</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/36436022" target="_blank"><img src=".image/sponsor/金鸿伟.jpg" width="80px;" alt="金鸿伟"/><br /><sub><b>金鸿伟</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/cnlijf" target="_blank"><img src="./.image/sponsor/李江峰.jpg" width="80px;" alt="李江峰"/><br /><sub><b>李江峰</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src=".image/sponsor/Best%20Yao.jpg" width="80px;" alt="Best Yao"/><br /><sub><b>Best Yao</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/weiloser" target="_blank"><img src=".image/sponsor/无为而治.jpg" width="80px;" alt="无为而治"/><br /><sub><b>无为而治</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/shup092_admin" target="_blank"><img src="./.image/sponsor/shup.jpg" width="80px;" alt="shup"/><br /><sub><b>shup</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/gampa" target="_blank"><img src="./.image/sponsor/也许.jpg" width="80px;" alt="也许"/><br /><sub><b>也许</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/leishaozhuanshudi" target="_blank"><img src="./.image/sponsor/⁰ʚᦔrꫀꪖꪑ⁰ɞ%20..jpg" width="80px;" alt="⁰ʚᦔrꫀꪖꪑ⁰ɞ ."/><br /><sub><b>⁰ʚᦔrꫀꪖꪑ⁰ɞ .</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/fateson" target="_blank"><img src="./.image/sponsor/逆.jpg" width="80px;" alt="逆"/><br /><sub><b>逆</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/dongGezzz_admin" target="_blank"><img src="./.image/sponsor/廖东旺.jpg" width="80px;" alt="廖东旺"/><br /><sub><b>廖东旺</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/huangzhen1993" target="_blank"><img src="./.image/sponsor/黄振.jpg" width="80px;" alt="黄振"/><br /><sub><b>黄振</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/fengchunshen" target="_blank"><img src="./.image/sponsor/春生.jpg" width="80px;" alt="春生"/><br /><sub><b>春生</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/mrfox_wang" target="_blank"><img src="./.image/sponsor/贵阳王老板.jpg" width="80px;" alt="贵阳王老板"/><br /><sub><b>贵阳王老板</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/haobaby" target="_blank"><img src="./.image/sponsor/hao_chen.jpg" width="80px;" alt="hao_chen"/><br /><sub><b>hao_chen</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/finalice" target="_blank"><img src="./.image/sponsor/尽千.jpg" width="80px;" alt="尽千"/><br /><sub><b>尽千</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/yuer629" target="_blank"><img src="./.image/sponsor/yuer629.jpg" width="80px;" alt="yuer629"/><br /><sub><b>yuer629</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/cai-peikai/ai-project" target="_blank"><img src="./.image/sponsor/kong.jpg" width="80px;" alt="kong"/><br /><sub><b>kong</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/HB1731276584" target="_blank"><img src="./.image/sponsor/岁月静好.jpg" width="80px;" alt="岁月静好"/><br /><sub><b>岁月静好</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/hy5128" target="_blank"><img src="./.image/sponsor/Kunkka.jpg" width="80px;" alt="Kunkka"/><br /><sub><b>Kunkka</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/guo-dida" target="_blank"><img src="./.image/sponsor/灬.jpg" width="80px;" alt="灬"/><br /><sub><b>灬</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/XyhBill" target="_blank"><img src="./.image/sponsor/Mr.LuCkY.jpg" width="80px;" alt="Mr.LuCkY"/><br /><sub><b>Mr.LuCkY</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/timeforeverz" target="_blank"><img src="./.image/sponsor/泓.jpg" width="80px;" alt="泓"/><br /><sub><b>泓</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/mySia" target="_blank"><img src="./.image/sponsor/i.jpg" width="80px;" alt="i"/><br /><sub><b>i</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/依依.jpg" width="80px;" alt="依依"/><br /><sub><b>依依</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/sunbirder" target="_blank"><img src="./.image/sponsor/小菜鸟先飞.jpg" width="80px;" alt="小菜鳥先飛"/><br /><sub><b>小菜鳥先飛</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/mmy0" target="_blank"><img src="./.image/sponsor/追溯未来-_-.jpg" width="80px;" alt="追溯未来"/><br /><sub><b>追溯未来</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/ccqingshan" target="_blank"><img src="./.image/sponsor/青衫.jpg" width="80px;" alt="青衫"/><br /><sub><b>青衫</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/jiangchunJava" target="_blank"><img src="./.image/sponsor/Fae.jpg" width="80px;" alt="Fae"/><br /><sub><b>Fae</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/huang-xiangtai" target="_blank"><img src="./.image/sponsor/憨憨.jpg" width="80px;" alt="憨憨"/><br /><sub><b>憨憨</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/gu-beichen-starlight" target="_blank"><img src="./.image/sponsor/文艺小青年.jpg" width="80px;" alt="文藝小青年"/><br /><sub><b>文藝小青年</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/zhangnanchao" target="_blank"><img src="./.image/sponsor/lion.jpg" width="80px;" alt="lion"/><br /><sub><b>lion</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/yupccc" target="_blank"><img src="./.image/sponsor/汪汪队立大功.jpg" width="80px;" alt="汪汪隊立大功"/><br /><sub><b>汪汪隊立大功</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/wcjjjjjjj" target="_blank"><img src="./.image/sponsor/wcj.jpg" width="80px;" alt="wcj"/><br /><sub><b>wcj</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/hufanglei" target="_blank"><img src="./.image/sponsor/🌹怒放de生命😋.jpg" width="80px;" alt="怒放de生命"/><br /><sub><b>怒放de生命</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/juyunsuan" target="_blank"><img src="./.image/sponsor/蓝速传媒.jpg" width="80px;" alt="藍速傳媒"/><br /><sub><b>藍速傳媒</b></sub></a></td>
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
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/nctwo" target="_blank"><img src=".image/sponsor/信微输传助手.jpg" width="80px;" alt="信微輸傳助手"/><br /><sub><b>信微輸傳助手</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/l9999_admin" target="_blank"><img src=".image/sponsor/一往无前.jpg" width="80px;" alt="一往无前"/><br /><sub><b>一往无前</b></sub></a></td>
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
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/hrsjw1.jpg" width="80px;" alt="hrsjw1"/><br /><sub><b>hrsjw1</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/linguanghuan.jpg" width="80px;" alt="linguanghuan"/><br /><sub><b>linguanghuan</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/YiYaYiYaho.jpg" width="80px;" alt="YiYaYiYaho"/><br /><sub><b>YiYaYiYaho</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/慢慢慢.jpg" width="80px;" alt="慢慢慢"/><br /><sub><b>慢慢慢</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/lilOne.jpg" width="80px;" alt="lilOne"/><br /><sub><b>lilOne</b></sub></a></td>
    </tr>
  </tbody>
</table>

## 💡 期待

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
より良いご意見を歓迎し、easyaiotの改善にご協力ください。
</p>

## 📄 著作権

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
翱翔的雄库鲁/easyaiot は <a href="https://gitee.com/soaring-xiongkulu/easyaiot/blob/main/LICENSE" style="color: #3498db; text-decoration: none; font-weight: 600;">APACHE LICENSE 2.0</a> オープンソースライセンスを採用しています。使用過程で以下の点に注意してください：
</p>

<ol style="font-size: 14px; line-height: 1.8; color: #444; margin: 15px 0; padding-left: 25px;">
  <li>製品関連コードのソースファイルヘッダコメントと出所を変更してはなりません。</li>
  <li>国家安全、名誉、利益を害する行為に適用したり、いかなる形式でも違法目的に使用してはなりません。</li>
</ol>

## 🌟 Star増加トレンド図

[![Stargazers over time](https://starchart.cc/soaring-xiongkulu/easyaiot.svg?variant=adaptive)](https://starchart.cc/soaring-xiongkulu/easyaiot)
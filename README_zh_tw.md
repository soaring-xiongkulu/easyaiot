# EasyAIoT（雲邊端一體化智能算法應用平臺）

[![Gitee star](https://gitee.com/volara/easyaiot/badge/star.svg?theme=gvp)](https://gitee.com/soaring-xiongkulu/easyaiot/stargazers)
[![Gitee fork](https://gitee.com/volara/easyaiot/badge/fork.svg?theme=gvp)](https://gitee.com/soaring-xiongkulu/easyaiot/members)

<p style="font-size: 16px; line-height: 1.8; color: #555; font-weight: 400; margin: 20px 0;">
我希望全世界都能使用這個系統，實現AI的真正0門檻，人人都能體驗到AI帶來的好處，而並不只是掌握在少數人手裡。
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

## 📖 項目介紹

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
<strong>EasyAIoT</strong>（Easy AI Internet of Things）是一款<strong>雲邊端一體化的智能算法應用平臺</strong>，專注於將人工智能與物聯網深度融合，讓攝像頭、傳感器與邊緣算力在現場即可協同運轉——從設備接入、數據採集，到即時視覺分析、智能研判與告警聯動，全鏈路在一套軟體中貫通完成。
</p>

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
許多智能物聯網項目落地時面臨同一困境：視頻系統、設備平臺、算法服務各自爲政，集成成本高、運維割裂、擴容困難。<strong>EasyAIoT 用一套平臺化解這一矛盾</strong>——同一套軟體既可部署在 4 GB 邊緣盒子上實現單點智能，也可搭載於 AI 一體攝像頭完成樓面級覆蓋，還能裝進企業級全棧一體機，一箱配齊 IoT 納管、海量視頻接入與 AI 分析研判，不必維護多套版本、不必反覆對接異構系統。
</p>

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
平臺由 <strong>WEB、APP、DEVICE、NODE、VIDEO、AI、TASK、EDGE、VISUALIZE、TRANSFORM、PANEL</strong> 十一個核心模組組成，並以 <strong>COMPILE</strong> 承接多平臺打包交付。在能力側，平臺覆蓋 GB28181 / ONVIF 多協議攝像頭接入、<strong>大疆機場與無人機空中視角接入</strong>、即時與抓拍算法任務、YOLO 目標檢測與 SAM 零樣本自動標註、人臉/車牌識別、可編排業務後處理、聯邦算力集羣調度，以及 <strong>無限聯邦邊緣集羣模式</strong>（普通開發板可即開即用、現場智能就地決策、告警與證據自動匯聚上雲，算力隨業務任意鋪開），還有 MQTT / TCP / HTTP / Modbus-TCP / Modbus-RTU / OPC UA 物聯網設備全生命週期管理，以及<strong>可視化大屏與 Web 工藝組態</strong>，讓設備數據既能展成指揮態勢、也能落回工藝畫面；並新增 <strong>TRANSFORM 多向數據流轉引擎</strong>，把平臺側業務事件按約定投遞到 MES / ERP / CRM / WMS 等外部系統，多方對接可配、可追、可複用；配套 <strong>PANEL 交付與值守入口</strong>，讓一體機到場當天可裝可驗，值守與排障不必事事等開發遠程敲命令。在體驗側，Web 管控臺與移動 App / 小程序能力對齊，讓指揮中心與現場巡檢同一套業務邏輯、隨時隨地處置。
</p>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 16px 0 8px 0;">
<strong>一句話概括：</strong>EasyAIoT = AI + IoT，讓萬物互聯的同時實現萬物智視、萬物智控。
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
📄 如需更完整的圖文介紹，請參閱 <a href=".doc/项目介绍/EasyAIoT项目介绍 V2.0.pptx" style="color: #3498db; text-decoration: none; font-weight: 600;">EasyAIoT項目介紹 V2.0（PPT）</a>。
</p>

## 🌟 關於項目的一些思考

### 📍 項目定位

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT是一個雲邊端一體化的智能物聯網平臺，專注於AI與IoT的深度融合。平臺通過算法任務管理、即時流分析、模型服務集羣推理等核心能力，實現從設備接入到數據採集、AI分析、智能決策的全鏈路閉環，真正實現萬物互聯、萬物智控。
</p>

### 🎛️ PANEL：一體機到場當天可裝可驗，值守不必等開發遠程

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
智能物聯網項目最容易卡在「最後一公里」：機器到了現場，卻<strong>裝不起來、驗不出去、出了故障只能等開發遠程敲命令</strong>，駐場成本與驗收週期都被人拖住。PANEL 是面向集成商與現場運維的<strong>獨立交付與值守入口</strong>——按檔位一鍵裝機、看清整機健康與依賴、啓停服務與查日誌當場辦完；<strong>業務管控臺尚未就緒時，也能先把整機拉起來、守住、交出去</strong>，把「機器到場 → 平臺可用 → 可驗收」從等人變成當天可閉環。
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>縮短驗收週期</strong>：到場按 mini / standard / full 選一檔即可裝機，進度與結果當場可見，少因命令記不全、步驟漏一步導致「裝一半不知卡在哪」，PoC 與正式交付都能更快過驗收</li>
  <li><strong>降低駐場與遠程成本</strong>：容器是否在跑、資源是否吃緊、日誌卡在哪一目了然，重啓、清緩存、拉鏡像不必先翻文檔再等開發支援，值守人員可自助處置常見故障</li>
  <li><strong>多項目一套口徑</strong>：同一套裝機與運維入口可複用到多臺一體機、多處機房，交付、值守、交接口徑一致，避免「每臺現場各一套口口相傳」</li>
</ul>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0 8px 0;">
📦 <strong>安裝包下載</strong>：Ubuntu / Debian、CentOS / RHEL、Windows、macOS 及 ARM / 麒麟等目標安裝包見 <a href="https://gitee.com/volara/easyaiot/releases" style="color: #3498db; text-decoration: none; font-weight: 600;">Gitee Releases</a>。
</p>

| | | |
|:---:|:---:|:---:|
| ![系統概覽](.image/banner/panel/panel_1000.png) | ![容器管理](.image/banner/panel/panel_1001.png) | ![容器日誌](.image/banner/panel/panel_1002.png) |
| ![一鍵部署](.image/banner/panel/panel_1003.png) | ![鏡像就緒](.image/banner/panel/panel_1004.png) | ![鏡像拉取](.image/banner/panel/panel_1005.png) |
| ![系統診斷](.image/banner/panel/panel_1006.png) | ![系統維護](.image/banner/panel/panel_1007.png) | ![服務拓撲](.image/banner/panel/panel_1008.png) |

### 🎯 三檔硬體，一套平臺

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
很多智能物聯網項目走到落地時都會卡住：<strong>功能做全了，小機器裝不下；爲了裝得下，又得砍能力、拆版本、維護多套部署包。</strong> EasyAIoT 用同一套平臺化解這一矛盾——<strong>邊緣盒子點上智能、AI 一體攝像頭上牆即分析、AIoT 智能全棧一體機一箱配齊全鏈路</strong>，三類最常見的現場硬體各選一檔即可，同一套軟體貫穿從單點試點到樓面覆蓋再到全棧交付，不必拆版本。
</p>

| 選型 | 典型硬體（舉例） | 推薦記憶體 | 你能做到什麼 | 實測驗證 |
| :-- | :-- | :--: | :-- | :--: |
| **mini** 邊緣精簡版 | <strong>邊緣盒子</strong>（4 GB 工控機、門店安防一體機、工地現場網關） | ≥ 4 GB | <strong>一個點位裝上就有智能</strong>：攝像頭接入、即時分析、智能告警、模型推理，最低成本落地視覺能力 | 僅需約 2 GB，餘量充足 |
| **standard** 標準版 | <strong>AI 一體攝像頭</strong>（智能攝像終端、帶算力 AI 監控攝像頭、多目 AI 分析一體機） | ≥ 16 GB | <strong>每路攝像頭即智能節點</strong>：多路攝像頭上牆即可樓面/園區級覆蓋，設備、規則、算力統一編排，多場景並行運營 | 約 10 GB，運行平穩有餘量 |
| **full** 完整版（預設） | <strong>AIoT 智能全棧一體機</strong>（企業級全棧智控一體機、行業物聯網全棧主機、雲邊端一體智能平臺一體機） | ≥ 20 GB | <strong>一箱配齊 IoT + 視頻 + AI</strong>：設備納管、海量接入、智能分析、指揮研判一體化，全量能力長期穩跑 | 約 14 GB，全能力開啓仍留足餘量 |

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 16px 0 8px 0;">
<strong>安裝選型與資源符合性（實測）：</strong>
</p>

| | | |
|:---:|:---:|:---:|
| ![邊緣盒子 mini](.image/deploy-profile-mini.png) | ![AI 一體攝像頭 standard](.image/deploy-profile-standard.png) | ![全棧一體機 full](.image/deploy-profile-full.png) |

#### 🧠 AI能力

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>平臺名稱與 Logo 全觸點自定義</strong>：同一套 EasyAIoT 部署到現場後，用戶看到的應是「自己的平臺」，而不是通用產品名。監控大屏內置可視化「平臺標識設置」，管理員在界面中即可完成品牌替換——管理後臺可改平臺名稱與 Logo（同步側邊欄、瀏覽器標題）；監控大屏可獨立設置指揮標題；登入頁可自定義名稱、Logo、表單標題及淺色/深色背景圖，三處視覺統一、即時生效，並支持保存與一鍵重置。
    <ul style="margin: 5px 0; padding-left: 20px;">
      <li><strong>對系統集成商與方案商</strong>：省去前端改膚、二次開發與發版成本；PoC 演示與正式交付可快速切換爲客戶品牌，同一套代碼支撐多客戶項目，縮短回款週期、提高方案複用率</li>
      <li><strong>對政府、園區、醫院等行業終端用戶</strong>：登入頁、指揮大屏與日常管理後臺均呈現本單位名稱與標識，領導視察與對內推廣更有歸屬感與公信力，符合機關、事業單位及大型企業的資訊化品牌展示要求</li>
      <li><strong>對私有化部署與運維團隊</strong>：現場安裝後當場配置即可驗收，無需等待開發排期；多客戶演示或階段性試點結束後可一鍵恢復初始設置，降低運維切換與重複部署成本</li>
    </ul>
  </li>
  <li><strong>YOLO26 新一代目標檢測能力</strong>：平臺內置最新一代目標檢測能力，開箱即可用於即時畫面分析與抓拍識別，在相同硬體條件下可接入更多路攝像頭、響應更快、誤報更少。支持從數據採集、標註、訓練到上線推理的完整閉環，幫助用戶以更低成本持續迭代專屬檢測模型，快速覆蓋安全帽佩戴、人員闖入、煙火隱患等各類常見安防與工業場景，讓「看得準、算得快、擴得動」成爲預設可用能力</li>
  <li><strong>YOLO26 人體姿態分析</strong>：在目標檢測能力之上新增人體關鍵點與骨架姿態分析，開箱即用，支持圖片、視頻與攝像頭即時流三種輸入方式。圖片模式可同步輸出骨架標註與人數統計；視頻模式支持進度跟蹤與結果下載；攝像頭模式可對接 RTSP/RTMP 即時取流，將姿態識別結果疊加推流回顯，便於遠程盯防與行爲研判。模型推理頁提供「姿態分析」與「目標檢測」一鍵切換，適用於工地作業規範、健身動作評估、人羣聚集態勢感知等需要「看清人體結構與動作形態」的場景，讓平臺從「框出目標」進一步走向「理解姿態」</li>
  <li><strong>多協議攝像頭接入支持</strong>：全面支持 GB28181 和 ONVIF 兩大主流視頻監控協議，實現標準化設備接入與管理。GB28181 作爲中國國家標準，完美適配國內主流監控設備；ONVIF 作爲國際通用標準，廣泛兼容全球主流品牌攝像頭。通過雙協議支持，平臺能夠無縫對接現有監控系統，實現設備的即插即用、自動發現與統一管理，大幅降低設備接入門檻，提升系統兼容性與擴展性，爲大規模攝像頭部署提供堅實的技術基礎。此外，新增 NVR 同網段/跨網段批量掃描、註冊與統一管控能力，覆蓋海康、大華、華爲、螢石、小米等主流品牌，支持基於設備原生協議的網段發現、一鍵登記及通道批量導入，進一步降低大規模監控設備的接入與運維成本</li>
  <li><strong>大疆機場 / 無人機空中視角接入</strong>：突破固定攝像頭「只能看地面、難覆蓋廣域」的布控侷限，將大疆司空體系下的機場與無人機高空畫面納入平臺統一視頻與 AI 研判閉環。流媒體模組提供「接入大疆直播」能力：支持<strong>司空 API 開啓直播</strong>與<strong>手動直播源</strong>兩種接入方式——API 模式一鍵拉起廠家直播流並自動登記設備；手動模式則支持直接填入 RTSP / RTMP / HTTP-FLV / HLS 等直播源。接入後空中畫面可與國標/ONVIF 固定點位同屏共管，管理者可像管理固定攝像頭一樣調閱機場與飛行器實況，並進一步掛接即時 AI 分析、告警聯動與證據留存，快速覆蓋廣域巡查、應急勘察、周界補盲等傳統固定點位難以觸及的場景，顯著縮短「發現異常—鎖定現場—聯動處置」的響應鏈條，讓智慧安防從平面布控升級到天地一體協同感知</li>
  <li><strong>即時對講與雲臺遠控</strong>：打破「只能看、不能管」的傳統監控侷限，值守人員在即時預覽同屏即可完成語音喊話與雲臺操控——無需切換系統、不必親臨現場，即可遠程溝通、引導疏散或制止違規行爲，把響應從「派人到場」壓縮到「開口即達」。雲臺操控讓攝像頭隨心轉向、變焦聚焦，突發情況可迅速對準事發區域、放大細節，形成「看得清、指得準、喊得到」的一體化現場處置閉環。全面兼容 GB28181 與 ONVIF 設備，利舊現有監控資產，無需額外購置對講主機或第三方軟體，讓存量攝像頭即刻具備遠程溝通與靈活調度能力，顯著降低系統孤島與值守成本</li>
  <li><strong>可編排算法後處理</strong>：突破「只能檢出、難以研判」的能力瓶頸，在目標檢測之上增設獨立的業務研判層，將畫面感知結果轉化爲可運營、可追責、可統計的業務事件。支持按任務靈活定義人數統計、越線通行、停留超時、區域滯留、多條件複合告警等場景規則，無需反覆調整模型即可快速適配工地安監、園區安防、交通管控等差異化需求，把通用視覺能力鍛造成貼近現場的管理抓手。後處理與即時分析彼此獨立、並行運轉——監控畫面持續流暢研判，業務邏輯按需彈性擴展，研判結果自動沉澱存檔並驅動精準告警，顯著降低誤報漏報與人工複覈成本。業務人員專注規則表達，平臺負責分發執行與規模承載，讓「看得見」真正走向「判得清、管得住、用得起來」</li>
  <li><strong>多中心節點 × 多工作節點聯邦集羣</strong>：面向跨區域、多機房與雲邊協同部署，平臺採用「N 箇中心節點 + N 個工作節點」聯邦架構——中心節點統一編排，工作節點承載算力與媒體執行，可橫向擴展。每個中心節點納管本域工作節點，支持流媒體、音視頻轉碼、視頻分析、模型推理與訓練等能力的遠程分發與一鍵部署；多中心可互聯同步，集羣泳道視圖直觀呈現「中心—工作」拓撲與資源水位。算法任務、自動標註流水線、推流轉發等工作負載按節點角色與 GPU 能力智能調度，讓海量路數接入、高併發推理與分佈式訓練在同一集羣中協同運轉，真正做到「納得進、分得清、擴得開、管得全」</li>
  <li><strong>SAM 零啓動自動標註編排流水線</strong>：面向「尚無標註樣本、尚無可用檢測模型」的冷啓動場景，平臺集成 SAM 開放詞彙分割能力，提供一鍵無人值守標註流水線。系統按策略自動串聯攝像頭抽幀採集、文本提示首批標註、達標後自動觸發 YOLO 微調訓練、量產階段以 YOLO 高速推理爲主並對漏檢樣本智能切換 SAM 回補、按進度週期性迭代訓練及數據集自動打包導出，完整貫通「採—標—訓—導」閉環。支持任務暫停恢復與本地/集羣算力彈性調度，配合可視化策略配置與運行日誌，幫助用戶從零樣本、零模型起步快速沉澱專屬檢測能力，讓「開口定義類別、坐等模型成型」成爲數據集建設的預設可用路徑</li>
  <li><strong>萬級彈性算力集羣與橫向擴容池</strong>：面向超大規模 AI 與視頻業務，構建雲邊端一體的分佈式算力底座，將算法任務、推流轉發、算法服務、模型訓練與推理統一納入橫向負載均衡與彈性伸縮體系。新增伺服器一鍵納管入網即可成爲可調度算力單元，調度中樞按資源水位與業務壓力自動分發任務、平衡負載，實現從百路到萬路攝像頭、從單機到萬級節點的線性擴容——無需重複部署與手工調參，讓海量路數接入、高併發推理與分佈式訓練在同一算力池中協同運行，真正做到「擴得動、跑得穩、管得住」</li>
  <li><strong>無限聯邦邊緣集羣模式</strong>：面向廣域布點、弱網現場與分階段擴容場景，讓智能分析能力貼着業務就地部署——普通開發板與邊緣算力節點也可成爲隨時上線的值守單元。中心統一下發任務與策略，現場就近完成感知研判，告警與證據自動回傳匯聚，無需再爲每個網點堆疊重型伺服器與複雜運維體系。業務擴張時按需增配節點即可線性延展覆蓋半徑，做到「加一點，多一片；加一路，多一分保障」，真正實現算力隨場景生長、智能隨業務鋪開</li>
  <li><strong>天地圖空間可視化與以圖研判</strong>：接入國家天地圖，將攝像頭、告警與人車識別能力匯聚到一張地圖，讓監控從「看畫面」升級爲「看全局」。流媒體與告警模組均提供「地圖分佈」視圖，配合設備目錄樹按區域聚焦，一眼掌握卡口布局與在線狀態；支持地圖點選、地點搜索與批量導入座標，國標通道、NVR 通道與直連攝像頭均可快速完成布點，讓每路畫面都有清晰的空間歸屬。告警事件自動關聯攝像頭座標上圖展示，可按時間、事件類型、任務與業務標籤篩選，選中即可查看抓拍與錄像，幫助值守人員從「哪裏出事」快速切入處置。結合人臉庫與車牌庫識別能力，可將同一目標在多個點位上的命中記錄串聯成空間脈絡——<strong>以人尋跡</strong>，還原重點人員在布控範圍內的出現路線與活動範圍；<strong>以車尋跡</strong>，串聯過車記錄，快速定位車輛行經路徑與停留區域，爲尋人找車、巡防布控與事後覆盤提供直觀線索。移動類設備還支持軌跡回放，按時間軸重現巡邏與行進路線；矢量地圖與衛星影像隨心切換，自動適應視野，讓管理者以地圖爲綱、以圖爲媒，更快發現異常、鎖定目標、指揮調度</li>
  <li><strong>Qwen / DeepSeek 多卡部署</strong>：支持將 Qwen、DeepSeek 等大語言模型以多卡並行方式部署上線，可按集羣靈活調度 GPU 算力，實現模型實例的彈性擴縮與負載均衡，滿足高併發推理與長上下文場景下的穩定服務能力</li>
  <li><strong>視覺大模型智能理解</strong>：集成QwenVL3視覺大模型，支持對即時視頻畫面進行深度視覺推理與語義理解，能夠對畫面內容進行智能分析與場景理解，提供更豐富的視覺認知能力，實現從像素級感知到語義級理解的跨越</li>
  <li><strong>攝像頭即時畫面 AI 分析</strong>：面向 RTSP/RTMP 即時視頻流提供從拉流、抽幀、模型推理到結構化出數與告警聯動的全鏈路分析能力，以毫秒級響應將畫面變化即時轉化爲可檢索、可研判的結構化檢測事件。觀看與算法鏈路相互獨立，兼顧預覽清晰度與高路數併發吞吐；分析結果可無縫銜接檢測區域、佈防時段、人臉/車牌識別及可編排後處理規則，將傳統「人盯屏、事後翻」的值守模式升級爲「機器全時盯、異常秒推送、證據自動留」，讓即時視頻從被動觀看真正變爲主動感知與智能研判的基礎設施</li>
  <li><strong>攝像頭智能巡檢</strong>：面向路數多、值守人力有限的監控場景，提供分屏巡檢與設備目錄批量巡檢能力，對大規模攝像頭進行輪巡式 AI 分析。支持輪詢、連接池、混合三種調度模式——可按設定間隔自動抓拍、運行檢測模型並聯動告警與人臉/車牌識別；混合模式下焦點路常駐盯防、背景路輪巡，兼顧重點布控與全域覆蓋。巡檢進度即時可見，抓拍自動留存，支持從分屏畫面或設備目錄一鍵拉起數百路巡檢，以「少連接、廣覆蓋、快發現」的方式，將傳統人工逐屏翻看的值守模式升級爲智能化自動巡檢</li>
  <li><strong>雲邊端一體算法預警監控大屏</strong>：提供統一的雲邊端一體化算法預警監控大屏，即時展示設備狀態、算法任務運行情況、告警事件統計、視頻流分析結果等關鍵資訊，支持多維度數據可視化展示，實現雲端、邊緣端、設備端的統一監控與管理，爲決策者提供全局視角的智能監控指揮中心</li>
  <li><strong>人臉識別與人臉庫管理能力</strong>：支持在攝像頭任務中靈活開啓人臉識別能力，提供人臉庫與人臉特徵管理體系，支持樣本/特徵的新增、查詢、更新、刪除與高效檢索。支持對抓拍畫面進行人臉比對與身份檢索，完整記錄匹配結果、抓拍圖片、攝像頭位置資訊與設備上下文，便於後續人員軌跡追溯、安防取證與多維度統計分析</li>
  <li><strong>車牌識別與車牌庫管理能力</strong>：支持在監控任務中一鍵啓用車牌識別，自動從過車畫面中識別車牌資訊，並與自建車牌庫即時比對。可靈活維護白名單、黑名單及業務標籤，車輛命中規則時即時告警聯動，幫助實現出入口通行管控、重點車輛布控、訪客與固定車輛分類管理等需求。支持自動收錄新出現車牌、完整留存抓拍與匹配記錄，便於事後查車、軌跡覈對與證據留存；識別過程與原有視頻分析並行運行，不影響監控與告警主流程的穩定性和即時性</li>
  <li><strong>設備檢測區域繪製</strong>：提供可視化的設備檢測區域繪製工具，支持在設備抓拍圖片上繪製四邊形和多邊形檢測區域，支持區域與算法模型靈活關聯配置，支持區域的可視化管理、編輯、刪除等操作，支持快捷鍵操作提升繪製效率，實現精準的區域檢測配置，爲算法任務提供精確的檢測範圍定義</li>
  <li><strong>智能聯動告警機制</strong>：支持檢測區域、佈防時段和事件告警的三重聯動機制，系統會智能判斷檢測到的事件是否同時滿足指定的檢測區域範圍、處於佈防時段內且匹配告警事件類型，只有同時滿足這三個條件時纔會觸發告警，實現精準的時空條件過濾，大幅降低誤報率，提升告警系統的準確性和實用性</li>
  <li><strong>大規模攝像頭管理</strong>：支持百級攝像頭接入，提供採集、標註、訓練、推理、導出、分析、告警、錄像、存儲、部署等全流程服務</li>
  <li><strong>算法任務管理</strong>：支持創建和管理兩種類型的算法任務，每個算法任務可靈活綁定抽幀器和排序器，實現精準的視頻幀提取與結果排序
    <ul style="margin: 5px 0; padding-left: 20px;">
      <li><strong>即時算法任務</strong>：用於即時畫面分析，支持RTSP/RTMP流即時處理，提供毫秒級響應能力，適用於監控、安防等即時場景</li>
      <li><strong>抓拍算法任務</strong>：用於抓拍圖像分析，對抓拍圖片進行智能識別與分析，適用於事件回溯、圖像檢索等場景</li>
    </ul>
  </li>
  <li><strong>數據集標註與多格式數據集管理</strong>：內置可視化圖像標註工作臺，支持矩形框、多邊形等標註形態，以及標註類別管理與進度跟蹤；全面兼容 YOLO、COCO、ImageFolder 等主流數據集格式的靈活導入與導出，並打通雲平臺數據集通道，支持雲端數據集的一鍵導入與同步導出，貫通「數據採集—人工標註—模型訓練—部署推理」全流程閉環</li>
  <li><strong>多卡訓練、斷點續訓與節點側部署</strong>：突破「有卡用不上、任務控不住、中斷成果丟」的訓練瓶頸，打通多卡算力利用、任務可控調度與節點側部署，讓現場 GPU 真正用得上、訓練任務真正控得住。平臺可自動識別並調度伺服器全部 GPU，用戶可在訓練頁按需選擇單卡或多卡；兼容多種常見數據集格式，支持大容量本地數據集上傳，訓練失敗後仍可保留原始數據快速重試。訓練進度全程可見，任務可停可續，本地與遠程訓練失敗時也能及時回退並給出清晰反饋，讓「訓練—發佈—使用」閉環更順暢可靠</li>
  <li><strong>推流轉發</strong>：支持在無需啓用AI分析功能的情況下，直接觀看攝像頭即時畫面。通過創建推流轉發任務，可將多路攝像頭進行批量推送，實現多路視頻流的同步觀看，滿足純視頻監控場景需求</li>
  <li><strong>GPU 探測、負載分配與多卡協同</strong>：平臺具備 GPU 資源探測與智能分配能力，可自動識別可用 GPU 數量，並依據各卡即時負載將視頻編解碼與算法推理任務動態調度到多卡並行執行，在保障穩定性的前提下提升多路流處理吞吐與算力利用率，實現多卡場景下的畫面編解碼與模型推理協同</li>
  <li><strong>智能傳輸協議與拉流高可靠</strong>：在 RTSP 等拉流鏈路上，系統可按場景自動選擇合適的傳輸方式以兼顧時延與穩定性。當出現灰屏、解碼異常或畫面停滯時，自動觸發重連與鏈路恢復，降低長時間花屏、卡死對業務的影響</li>
  <li><strong>觀看鏈路與算法鏈路分離及分級碼率</strong>：將「即時預覽/大屏觀看」與「算法分析抽幀」相互解耦、獨立調度。觀看側優先保障畫清晰、少卡頓；算法側在檢測精度與算力/帶寬佔用之間取得平衡，避免分析任務與觀看任務爭搶同一通道，保障「看得清、不卡斷」與「算得動、可擴展」兼顧</li>
  <li><strong>模型服務集羣推理</strong>：支持分佈式模型推理服務集羣，實現智能負載均衡、故障自動切換與高可用保障，大幅提升推理吞吐量與系統穩定性</li>
  <li><strong>佈防時段管理</strong>：支持全防模式和半防模式兩種佈防策略，可靈活配置不同時段的佈防規則，實現精準的時段化智能監控與告警</li>
  <li><strong>OCR與語音識別</strong>：提供高精度文字識別與語音轉文本能力，支持多語言識別</li>
  <li><strong>多模態視覺大模型</strong>：支持物體識別、文字識別等多種視覺任務，提供強大的圖像理解與場景分析能力</li>
  <li><strong>LLM大語言模型</strong>：支持RTSP流、視頻、圖像、語音、文本等多種輸入格式的智能分析與理解，實現多模態內容理解</li>
  <li><strong>模型部署與版本管理</strong>：支持AI模型的快速部署與版本管理，實現模型一鍵上線、版本回滾與灰度發佈</li>
  <li><strong>多實例管理</strong>：支持多個模型實例的併發運行與資源調度，提高系統利用率與資源利用效率</li>
  <li><strong>攝像頭抓拍</strong>：支持攝像頭即時抓拍功能，可配置抓拍規則與觸發條件，實現智能抓拍與事件記錄</li>
  <li><strong>抓拍空間管理</strong>：提供抓拍圖片的存儲空間管理，支持空間配額與清理策略，確保存儲資源合理利用</li>
  <li><strong>錄像空間管理</strong>：提供錄像文件的存儲空間管理，支持自動清理與歸檔，實現存儲資源的智能管理</li>
  <li><strong>抓拍圖片管理</strong>：支持抓拍圖片的查看、檢索、下載、刪除等全生命週期管理，提供便捷的圖片管理功能</li>
  <li><strong>設備目錄管理</strong>：提供設備樹形目錄管理，支持設備分組、層級管理與權限控制，實現設備的有序組織與精細化管理</li>
  <li><strong>告警錄像</strong>：支持告警事件自動觸發錄像功能，當檢測到異常事件時自動錄製相關視頻片段，提供完整的告警證據鏈，支持告警錄像的查看、下載和管理</li>
  <li><strong>告警事件</strong>：提供完整的告警事件管理功能，支持告警事件的即時推送、歷史查詢、統計分析、事件處理與狀態跟蹤，實現告警全生命週期管理</li>
  <li><strong>錄像回放</strong>：支持歷史錄像的快速檢索與回放功能，提供時間軸定位、倍速播放、關鍵幀跳轉等便捷操作，支持多路視頻同步回放，滿足事件回溯與分析需求</li>
</ul>

#### 🌐 IoT能力

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0 8px 0;">
許多項目把 IoT 做成「設備臺賬 + 報文中轉」，結果是：能連上，卻管不住；能上報，卻推不動；能告警，卻看不清現場；有數了，卻展不成屏、對不上工藝。EasyAIoT 把 IoT 定位爲<strong>感知—理解—決策—執行</strong>閉環裏的執行神經：傳感器與執行器提供「數」，攝像頭與 AI 提供「圖」，可視化大屏與工藝組態把「數」變成可指揮的態勢，規則與影子把兩者擰成可運營的業務動作——讓平臺不只「看得見」，更能「展得成屏、看得懂工藝、管得住、控得準、擴得開」。
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>可視化管理</strong>：設備測點、告警與業務指標若只停在列表與報文裏，領導看不全、值班看不清、彙報還得另做 PPT——數據價值卡在「能採不能展」。平臺將可視化項目、模板中心、素材庫、數據源與服務部署收攏爲一套能力：把物聯網數據拖拽拼成園區態勢、產線 KPI、設備運行等可運營大屏，草稿可改、成熟可發、發佈可投——讓 IoT 從「後臺有數」升級爲「前臺有屏」，指揮研判與對外展示不必再外掛一套大屏工具</li>
  <li><strong>可視化項目全生命週期</strong>：大屏工程若散落在個人電腦與臨時連結裏，交接必亂、版本必丟、上線必扯皮。平臺統一管理大屏項目的創建、編輯、預覽、發佈與下線，表格/卡片雙視圖隨手盤點，已發佈與未發佈一眼可分——誰在做、做到哪、能不能投屏，項目狀態可盤、可交、可驗收，把「做一張屏」變成可運營的交付資產</li>
  <li><strong>可視化模板中心</strong>：每個項目都從空白畫布重做，交付週期必然被設計與聯調拖長。成熟的園區總覽、工廠態勢、設備看板等模板可沉澱複用，新建項目一鍵套用再微調——同類場景少從零畫起，PoC 與多項目複製更快、口徑更統一，把「會做一次」沉澱成「能交付多次」</li>
  <li><strong>可視化素材與數據源治理</strong>：圖標、背景、視頻素材各項目私藏一份，數據接口各屏各寫一套，後期必出現風格打架、字段對不上。素材庫集中歸檔可複用視覺資產，數據源統一掛接設備與業務接口——同一套素材風格、同一套數據口徑服務多張大屏，改一處多處受益，少重複建設、少口徑扯皮</li>
  <li><strong>可視化發佈與服務部署</strong>：大屏做好卻投不出去，等於白做。項目確認發佈後可關聯服務部署，按場景投放到指揮中心、值班室或對外展示入口，預覽與正式投放同一套工程——從「編輯態」到「值班態」有明確出口，驗收與日常值守不再靠臨時連結與口頭約定</li>
  <li><strong>組態管理</strong>：工業與樓宇現場最怕「錶盤一堆、工藝看不懂」——電錶、閥門、罐體液位有讀數，值班卻對不上管線與工序，異常只能口頭對圖、靠經驗猜。平臺提供 Web 組態能力，將設備測點綁定到水廠工藝總貌、產線運行看板、廠區管網拓撲、配電室電力監視等工藝畫面，編輯與預覽同入口、發佈即可值班——讓「數」落回「圖」，工藝狀態一目瞭然，值守從翻表猜事變爲對着工藝圖研判與處置</li>
  <li><strong>組態畫面即時監視與有限控制</strong>：純列表監控「看得見點位卻看不見流程」，異常定位慢、跨班交接難、現場培訓靠師傅帶。組態運行態把關鍵測點動畫到罐體、閥組、電機與開關上，趨勢與狀態同屏刷新，必要時可在畫面側完成啓停、復位等有限操作——新人也能對着圖上手，班組交接看同一套畫面，異常從「找點位」壓縮到「看工藝」，把工控現場真正納入可值守、可交代、可擴展的日常運營</li>
  <li><strong>產品模型管理</strong>：物聯網落地最貴的往往不是買設備，而是每接一類設備就重配一遍檔案。平臺以產品爲同類設備模板，支持創建、啓停、檢索與表格/卡片雙視圖，應用場景、廠商、型號一次配好——後續擴容直接套用產品模板，不用再逐臺從零填寫，同類設備一次建檔、多臺複用，把「設備接入成本」從線性增長壓成可複製資產</li>
  <li><strong>多類型產品建模</strong>：現場同時存在直連終端、邊緣網關、網關子設備與視頻設備時，若用同一套接入路徑硬套，拓撲必亂、協議必錯。平臺按直連、網關、網關子設備、視頻四類形態分開建產品，邊緣匯聚、直連終端與視頻設備各走各的接入路徑——拓撲不會混、協議不會配錯，爲後續規模化納管打好正確的產品骨架</li>
  <li><strong>產品接入協議與認證配置</strong>：每臺設備單獨約定協議與鑑權，是聯調返工的重災區。平臺在產品級一次定稿接入協議（MQTT / TCP / HTTP / Modbus-TCP / Modbus-RTU / OPC UA）、數據格式、認證方式與加解密策略，下屬設備自動繼承同一套規範——聯調時不再逐臺約定鑑權與報文格式，接入規範從「人口口相傳」變成「產品級可繼承契約」</li>
  <li><strong>Modbus-TCP 工業以太網接入</strong>：面向電錶、PLC、變頻器等以太網側工控設備，平臺內置 Modbus-TCP 主站採集能力，按產品/設備配置接入參數與測點即可上線——讀數自動匯入設備影子與在線狀態，寫值與屬性下發貫通，讓工業測點與物聯網物模型、規則引擎、告警聯動同一套閉環，不必再外掛獨立數採軟體</li>
  <li><strong>Modbus-RTU 串口現場接入</strong>：大量現場儀表仍掛在 RS-485 總線，若只能走 TCP 網關轉換，接入成本與故障點都會翻倍。平臺支持 Modbus-RTU 串口主站採集，適配虛擬串口與真實串口場景——總線側設備同樣納入統一納管與上下行控制，補齊「以太網進不了、串口又管不住」的現場空白</li>
  <li><strong>OPC UA 工業互聯接入</strong>：面向現代化工控與上位系統互聯場景，平臺支持 OPC UA 客戶端接入，完成訂閱/讀寫配置——複雜設備模型可映射爲平臺物模型屬性，上行採集與下行寫點與現有設備影子、規則鏈、消息推送無縫銜接，讓 OPC UA 現場資產真正進入「看得見、控得住、可聯動」的 AIoT 運營體系</li>
  <li><strong>物模型屬性定義</strong>：大屏、規則、告警若各寫一套測點名，後期必然互相聽不懂。平臺先把設備能上報、能讀寫的測點定清楚，支持標準模板與自定義，草稿改完再發布——大屏、規則、告警從此認同一套字段，「能看哪些量」有統一語義，測點名各說各話的返工從根上被掐掉</li>
  <li><strong>物模型服務定義</strong>：遠程啓停、復位若每做一個動作就寫一次性接口，控制面必然碎片化。平臺把設備可被遠程調用的服務及入參出參寫成契約，草稿編輯、發佈後生效——「能遠程做什麼」按契約填參即可，不必再爲每個動作堆一次性接口，控制能力可複用、可審計</li>
  <li><strong>物模型事件定義</strong>：設備會上報哪些業務事件若不事先約定，告警口徑必然前後打架。平臺先約定事件類型，草稿發佈後統一生效——事件日誌與規則觸發共用同一語義，「會發生哪些事」有統一口徑，告警不會各說各話</li>
  <li><strong>物模型發佈管控</strong>：模型改動若直接打到在線設備，一次誤操作就可能衝擊整批終端。平臺讓模型改動先落草稿，確認發佈才推到設備側——改模型有緩衝，未驗證改動不會直接打中現場在線設備，顯著降低誤操作風險</li>
  <li><strong>協議腳本適配</strong>：現場最難啃的不是標準 MQTT，而是各廠傢俬有報文與「只能本地工具調試」的黑盒設備。標準報文開箱即用；遇私有協議，可在平臺編寫上下行編解碼，支持模板套用、校驗、即時調試與保存熱加載——對接從「改設備固件、等廠家排期」變爲「配腳本、熱生效」，異廠家存量設備不用改固件就能納入統一物模型</li>
  <li><strong>產品接入指引</strong>：新人聯調若全靠駐場專家口頭傳，交付節奏必然卡在人身上。產品詳情內置聯調參數、鑑權、報文與驗收說明，按頁操作即可把設備驗過——按產品交付時自帶標準聯調手冊，少依賴駐場專家口述，PoC 與驗收節奏更快、更穩</li>
  <li><strong>產品關聯設備一覽</strong>：運維與驗收常因「這批設備到底覆蓋了多少、在線率怎樣」扯皮。打開產品即可看到旗下設備清單與在線狀態——在線率、覆蓋規模一眼盤清，運維與驗收各管一段、責任邊界清楚</li>
  <li><strong>設備檔案納管</strong>：散落在表格、聊天記錄與現場記憶裏的設備，盤點與移交必然失控。平臺提供設備增刪改查、按產品/標識/在線狀態檢索，表格與卡片雙視圖隨手切換——散落終端收成可檢索臺賬，盤點、移交、擴容都從一個入口進</li>
  <li><strong>設備在線與激活狀態</strong>：問題機埋在「全部設備」裏，值班只能盲翻。列表與詳情直接亮出連接狀態、激活狀態、激活時間與最後上線時間——離線機、未激活機優先浮出，運維精力先打在真正異常的設備上</li>
  <li><strong>按產品登記設備</strong>：擴容時每臺重選協議、重填鑑權，是規模化上線最大的摩擦。新建設備時綁定所屬產品，協議與場景一併繼承——登記即掛上正確產品模板，擴容複製產品即可，少了反覆選協議、填鑑權的步驟</li>
  <li><strong>工業採集接入配置</strong>：電錶、傳感等測點若還要另開數採工具配置，現場必然雙系統並行。登記工業採集類設備時可順帶配好主機、測點與採集週期——現場測點一次落檔，不必再切到別的數採工具，工業採集與平臺納管一體完成</li>
  <li><strong>設備基礎資訊檔案</strong>：換機、追責、對賬時若靠口頭確認「這是誰」，責任鏈必然斷。名稱、標識、SN、產品、版本、IP 等一機一檔沉下來——打開檔案即可確認設備身份，減少口頭確認與現場翻找</li>
  <li><strong>設備接入指引</strong>：現場聯調若仍靠翻厚文件、問專家，上線週期必然被拉長。按設備類型給出推薦命令、聯調參數、鑑權、報文與驗收說明，參數改完命令可直接複製——聯調從翻文件變成抄命令驗收，上線與 PoC 節奏更緊</li>
  <li><strong>運行狀態即時查看</strong>：值班若每次都要登設備、啃原始報文才能判斷測點是否正常，值守成本必然居高不下。按物模型把當前屬性實況攤開，表格/卡片可切換、可刷新——不登設備、不看原始報文，也能一眼判斷關鍵測點此刻正不正常</li>
  <li><strong>傳感器浮點數據預測</strong>：關鍵測點若只能事後翻歷史曲線，異常往往等「已經越界」才被看見。平臺對傳感器浮點屬性提供趨勢預測，把歷史讀數推演爲可前瞻的走勢——運維從「事後看數」升級爲「事前洞察」，爲處置爭取窗口</li>
  <li><strong>運行狀態屬性閾值配置</strong>：健康邊界若寫死在代碼或口頭約定裏，換型號、換場景就要返工。可按物模型爲運行狀態屬性配置上下閾值，邊界可定義、可複用、可精細化——設備「正常區間」成爲可治理資產，而不是散落各處的經驗值</li>
  <li><strong>閾值告警與閾值規則</strong>：超限若無人知、知了卻無法聯動，閾值配置只是擺設。測點越界自動告警，並可納入規則聯動處置——「越界即知、知則能管」，把健康邊界真正落到可運營閉環</li>
  <li><strong>中心設備關聯子設備一屏掌控</strong>：下屬設備健康態勢若要逐臺翻看，巡檢與異常響應必然慢半拍。中心設備視角一屏縱覽關聯子設備運行狀態——不用逐臺切換，現場巡檢與異常定位效率顯著提升，讓設備側真正具備「看得見數、管得住界、告得出警、看得清全局」的能力閉環</li>
  <li><strong>設備影子對照</strong>：傳統排障最痛苦的是分不清「想讓它怎樣」和「實際怎樣」。上報態、期望態與差異同屏對照，完整 JSON 可留底——排障從猜測變成對照，期望與實況是否一致一目瞭然</li>
  <li><strong>屬性期望下發</strong>：爲改一個參數專程出車，是規模化運維的典型浪費。可寫屬性批量改期望值後一鍵下發，處理中/成功/失敗全程可跟——遠程調參有回執，不必再爲改參數派人到場，少無效出車</li>
  <li><strong>物模型服務調用</strong>：啓停、復位若下達後無法確認是否執行到位，處置只能靠口頭對賬。按已發佈服務填參發起調用，指令回執可跟蹤——動作下達後能確認是否執行到位，處置過程可審計，把「口頭說控過了」升級爲「有回執的閉環」</li>
  <li><strong>離線指令排隊</strong>：弱網或短暫離線時指令直接丟，回來還得重做一遍。設備暫時離線時，指令先寫入期望影子，上線後按協議自動拉取或接收——弱網抖動不丟控制意圖，回來即補齊，少做一遍重複操作</li>
  <li><strong>子設備網關代理控制</strong>：邊緣大量終端若都要求直連平臺，接入複雜度與證書管理成本會指數上升。子設備控制經所屬網關代理下發——邊緣終端不必直連平臺也能被統一遙控，降低終端接入複雜度，讓網關真正成爲可運營的匯聚面</li>
  <li><strong>關聯攝像頭</strong>：傳感器告警若看不到現場，值守只能「聽數猜事」。物聯設備可綁定設備目錄中的攝像頭，測點與畫面點位掛上對應關係——異常一出就知道該翻哪路視頻，把「報個數」升級爲「找得到畫面」</li>
  <li><strong>分屏監控與 AI 聯動</strong>：這是 EasyAIoT 相對純 IoT 平臺的關鍵差異——純物聯「看得見數卻看不見場」，純視頻「看得見場卻控不住設備」。功能調用頁可切 1/4/9 分屏預覽關聯攝像頭，並可順手拉起 AI 分析——改參數、下指令的同時盯着現場，「數」與「圖」在同一屏裏覈實與處置，少切系統、少漏判，真正體現 AI + IoT 融合價值</li>
  <li><strong>事件日誌</strong>：告警彈窗一閃而過，事後覆盤只能靠記憶與扯皮。設備上報的資訊/警告/錯誤事件集中匯聚，可按類型、名稱、時間篩選——覆盤翻的是原始事件流，回答「現場發生過什麼」有據可依，不只靠瞬時彈窗</li>
  <li><strong>指令日誌</strong>：聯調排障最怕雙方各執一詞：指令到底下沒下到、設備認沒認。屬性設置與服務調用的處理中/成功/失敗全程留痕——聯調與排障告別口頭對賬，指令鏈路可覈對、可追責</li>
  <li><strong>設備日誌</strong>：定位固件與業務異常若還要登設備翻本地文件，排障效率必然被現場網路與權限卡住。設備側多級別日誌匯到雲端，關鍵字與時間可檢索——雲端即可定位異常，不必再登設備翻本地日誌</li>
  <li><strong>網關子設備綁定</strong>：工業與樓宇現場常見「一臺網關掛幾十上百子設備」，拓撲若靠口口相傳，擴點與故障隔離必然失控。網關可批量綁定/解綁子設備——誰掛誰一清二楚，擴點、換網關、故障隔離時責任邊界不會糊</li>
  <li><strong>Topic 能力清單</strong>：研發與集成若各拿一份通道約定，聯調必因不一致返工。按設備列出配置、影子、屬性、服務、事件、OTA、時鐘同步等上下行通道說明——對着同一份目錄對接，通道約定不一致的返工少了</li>
  <li><strong>OTA 升級包管理</strong>：補丁與固件若靠 U 盤逐臺拷貝，規模化升級幾乎不可能。軟體包/固件包統一上傳歸檔，版本號、下載、編輯、刪除與雙視圖齊全——補丁與固件放在一處可複用，不用再逐臺拷貝介質，固件成爲可管控的交付資產</li>
  <li><strong>OTA 升級策略</strong>：漏升有安全漏洞，亂升有兼容風險，是規模化設備運維的兩難。關鍵版本可打標記，升級方式可選強制或非強制——緊急修復能推到位，日常版本也不亂升，漏升與兼容風險可控</li>
  <li><strong>規則鏈管理</strong>：業務聯動規則散落各處、無法集中啓停，誤觸發與閒置鏈路必然增多。規則新增、啓停、批量刪除與列表/卡片管理齊全——業務聯動鏈路集中開關，閒置規則隨時關掉，誤觸發少一截</li>
  <li><strong>規則鏈可視化編排</strong>：現場業務天天在變——閾值要調、聯動要加——若每次都等開發寫死，響應永遠慢半拍。鏈式畫布上按意圖串聯數據流轉、條件判斷與下游動作——場景改動拖拽即可落地，不必再等開發排期，把「設備數據進來之後怎麼辦」交給業務人員配置</li>
  <li><strong>規則導入導出</strong>：成熟規則若不能帶走，每個項目都要從零重寫。規則支持導入導出——跨環境遷移、多項目複用直接帶走，成熟規則沉澱爲可複製的交付資產</li>
  <li><strong>消息配置</strong>：換通知通道、改帳號若還要動業務代碼，運維必然被開發卡住。通知通道與消息基礎設置集中維護——換通道、改帳號只動配置，不動業務代碼</li>
  <li><strong>消息模板</strong>：告警話術臨時拼寫，既易出錯也難統一口徑。郵件、短信、企業微信、釘釘、飛書、Webhook 等渠道各自維護模板——文案一次定稿多處複用，告警話術統一，少臨時拼文案出錯</li>
  <li><strong>消息推送</strong>：再準的檢測、再完整的設備事件，若堵在系統裏等人翻，價值等於零。按渠道創建推送任務，可先測試再正式啓動——告警與業務事件直接落到責任人日常辦公入口，不堵在系統裏</li>
  <li><strong>推送歷史</strong>：通知是否發出、是否觸達若無記錄，審計與優化只能靠猜。各渠道推送記錄可回看——發出沒有、觸達沒有有據可查，審計與觸達策略優化都有底</li>
  <li><strong>通知用戶與分組</strong>：關鍵告警全員刷屏會造成告警疲勞，該到的人收不到又會漏報。維護通知用戶與分組，按角色、班次精準觸達——該到的人收得到，全員刷屏的告警疲勞也少了，讓「感知—研判—通知—處置」真正閉環到人</li>
  <li><strong>TRANSFORM 多向業務流轉</strong>：平臺側告警、設備事件與業務結果若只能停在 EasyAIoT 內部，對接 MES / ERP / CRM / WMS 等系統仍要按項目定制接口，交付週期與返工成本都會被放大。TRANSFORM 把「轉給誰、按什麼規則轉、字段怎麼對上、投沒投到」收成可配置能力：數據目的、轉發規則與映射模板一次配好即可複用，投遞過程可監控、可回看——多方系統對接從「每家寫一次定制接口」變成「按約定配通、按軌跡驗收」，讓平臺數據真正進入客戶既有業務閉環</li>
</ul>

#### 📱 移動端APP

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>跨端覆蓋</strong>：手機、小程序與 App 多端可用，運維與管理不必綁在工位前，現場也能即時查看與處置</li>
  <li><strong>能力對齊</strong>：移動端與 PC 管控臺業務能力一致，換端不換功，管控體驗無縫銜接</li>
  <li><strong>設備管理</strong>：多種接入方式統一納管，列表與通道一目瞭然，點開即可即時看圖，外出巡檢同樣心中有數</li>
  <li><strong>推流轉發</strong>：隨時創建與啓停轉發任務，掌握集羣節點與各路流狀態，遠程也能調度視頻資源</li>
  <li><strong>算法任務</strong>：即時與抓拍算法任務隨手啓停，檢測成效隨時掌握，異常發現不必等回辦公室</li>
  <li><strong>告警中心</strong>：告警隨手檢索，抓拍與錄像即點即看，移動值守也能快速覈實與跟進</li>
  <li><strong>模型管理</strong>：模型上線狀態一眼可查，部署進展心中有數</li>
  <li><strong>模型推理</strong>：現場傳圖即得識別結果，臨時覈驗與抽檢不必回 PC</li>
  <li><strong>模型訓練</strong>：訓練進度隨時盯，必要時遠程一鍵叫停，避免無效算力空轉</li>
  <li><strong>個人中心</strong>：帳號、租戶與應用偏好集中管理，多端使用各得其便</li>
  <li><strong>流暢觀看</strong>：即時畫面與告警錄像在移動端流暢回放，低延時、不卡頓，移動值守體驗不打折</li>
  <li><strong>持續在線</strong>：登入狀態自動保持，少被打斷、少重複登入，讓「雲邊端智能管控」真正觸達手機與小程序</li>
</ul>

### 📦 內置 AI 模型

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
平臺開箱即用，內置多種面向安防監控、工業現場、智慧交通等場景的預訓練模型，可在算法任務中直接選用，快速完成部署與推理，無需從零訓練即可覆蓋常見視覺檢測需求。
</p>

| 模型名稱 | 推理格式 | 基礎模型 | 能力說明 |
| :-- | :--: | :--: | :-- |
| 安全帽模型 | ONNX | YOLOv8 | 檢測作業人員是否佩戴安全帽 |
| 睡崗模型 | PyTorch | YOLOv8 | 識別崗位人員睡崗、脫崗等異常行爲 |
| 人模型 | PyTorch | YOLOv8 | 通用人體檢測，用於畫面中人員的識別與定位 |
| 車牌模型 | ONNX | YOLOv8 | 識別車輛號牌資訊 |
| 反光衣模型 | PyTorch | YOLOv8 | 檢測作業人員是否穿着反光衣 |
| 火焰模型 | PyTorch | YOLOv8 | 識別明火、火焰等火災隱患 |
| 吸菸模型 | PyTorch | YOLOv8 | 識別人員吸菸行爲 |
| 打電話模型 | ONNX | YOLOv8 | 識別人員打電話、使用手機等行爲 |
| 道路積水模型 | ONNX | YOLOv8 | 識別道路積水、路面積水等異常狀況 |
| 口罩模型 | ONNX | YOLOv8 | 檢測人員是否正確佩戴口罩 |
| 跌倒檢測模型 | ONNX | YOLOv8 | 識別人員跌倒等異常姿態 |
| 人臉檢測模型 | ONNX | YOLOv8 | 檢測畫面中人臉位置，支撐人臉識別鏈路 |

### 💡 技術理念

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
我們認爲沒有任何一個編程語言能夠擅長所有事情，但通過三種編程語言的深度融合，EasyAIoT將發揮各自優勢，構建強大的技術生態。
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Java擅長構建穩定可靠的平臺架構，但不適合網路編程和AI編程；Python擅長網路編程和AI算法開發，但在高性能任務執行方面存在瓶頸；C++擅長高性能任務執行，但在平臺開發和AI編程方面不如前兩者。EasyAIoT採用三合一語言混編架構，充分發揮各語言優勢，構建一個實現頗具挑戰，但使用極其便捷的AIoT平臺。
</p>

![EasyAIoT平臺架構.jpg](.image/iframe2.jpg)

### 🔄 模組數據流轉

<img src=".image/iframe3.jpg" alt="EasyAIoT平台架构" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

### 🤖 零樣本標註技術

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
創新性地依託大模型構建零樣本標註技術體系（理想狀態下完全去除人工標註環節，實現標註流程的自動化），該技術通過大模型生成初始數據並藉助提示詞技術完成自動標註，再經人機協同校驗確保數據質量（可選），進而訓練出初始小模型。該小模型通過持續迭代、自我優化，實現標註效率與模型精度的協同進化，最終推動系統性能不斷攀升。
</p>

<img src=".image/iframe4.jpg" alt="EasyAIoT平台架构" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

### 🏗️ 項目架構特點

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
EasyAIoT其實不是一個項目，而是九個項目。
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
好處是什麼呢？假如說你在一個受限的設備上（比如RK3588），你只需要拿出其中某個項目就可以獨立部署，所以看似這個項目是雲平臺，其實他也可以是邊緣平臺。
</p>

<div style="margin: 30px 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;">

<p style="font-size: 16px; line-height: 1.8; margin: 0; font-weight: 500;">
🌟 真開源不易，如果這個項目對您有幫助，請您點亮一顆Star再離開，這將是對我最大的支持！<br>
<small style="font-size: 14px; opacity: 0.9;">（在這個假開源橫行的時代，這個項目就是一個異類，純靠愛來發電）</small>
</p>

</div>

### 🌍 在地化支持

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT積極響應在地化戰略，全面支持在地化硬體和作業系統，爲用戶提供安全可控的AIoT解決方案：
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🖥️ 伺服器端支持</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>完美兼容海光（Hygon）x86架構處理器</li>
  <li>支持在地化伺服器硬體平臺</li>
  <li>提供針對性的性能優化方案</li>
  <li>確保企業級應用的穩定運行</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">📱 邊緣端支持</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>普通開發板也可就地承擔智能值守</li>
  <li>現場輕裝上陣，無需爲每處網點堆疊重存儲</li>
  <li>開箱即可智能化，縮短邊緣上線週期</li>
  <li>算力隨點位鋪開，告警與證據自動匯聚上雲</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🖱️ 作業系統支持</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>兼容麒麟（Kylin）作業系統</li>
  <li>支持方德（Founder）等在地化Linux發行版</li>
  <li>適配統信UOS等主流在地化作業系統</li>
  <li>提供完整的在地化部署方案</li>
</ul>
</div>

</div>

## 🎯 適用場景

<img src=".image/适用场景.png" alt="适用场景" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

## 🧩 項目結構

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT由十一個核心項目組成，並配套 COMPILE 多平臺打包交付能力：
</p>

<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50; width: 20%;">模組</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50;">描述</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>WEB模組</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">前端管理界面，提供統一的用戶交互體驗</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>APP模組</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>跨端覆蓋</strong>：一套建設、多端觸達，手機、小程序與 App 均可使用</li>
    <li><strong>能力對齊</strong>：與 PC 管控臺業務能力一致，支持多租戶切換</li>
    <li><strong>設備管理</strong>：直連攝像頭、GB28181、NVR 等多協議統一納管，在線狀態與通道瀏覽，設備詳情內一鍵即時預覽</li>
    <li><strong>推流轉發</strong>：推流任務創建、啓停、集羣節點狀態與多路流地址查看</li>
    <li><strong>算法任務</strong>：即時/抓拍算法任務列表、啓停控制與檢測/幀數統計</li>
    <li><strong>告警中心</strong>：告警事件檢索、抓拍圖預覽、告警錄像點播回放</li>
    <li><strong>模型與 AI</strong>：模型列表與部署狀態、移動端圖片推理工作臺、訓練任務進度監控與停止</li>
    <li><strong>個人中心</strong>：個人資料、帳號安全、常見問題、意見反饋與應用設置</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>DEVICE模組</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>設備管理</strong>：設備註冊、認證、狀態監控、生命週期管理</li>
    <li><strong>產品管理</strong>：產品定義、物模型管理、產品配置</li>
    <li><strong>協議支持</strong>：MQTT、TCP、HTTP、Modbus-TCP、Modbus-RTU、OPC UA 等多種物聯網與工業協議</li>
    <li><strong>設備認證</strong>：設備動態註冊、身份認證、安全接入</li>
    <li><strong>規則引擎</strong>：數據流轉規則、消息路由、數據轉換</li>
    <li><strong>數據採集</strong>：設備數據採集、存儲、查詢與分析</li>
    <li><strong>節點編排</strong>：計算/媒體節點納管、連通檢測、工作負載調度與媒體節點池分配</li>
    <li><strong>可視化後臺</strong>：統一管理大屏/組態項目、模板、素材、數據源與服務部署，為可視化編輯器與工藝組態提供工程管理與發佈能力</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>NODE模組</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>節點代理</strong>：邊緣/遠程節點 Agent，一鍵安裝部署後自動接入平臺</li>
    <li><strong>狀態上報</strong>：週期性心跳，即時上報 CPU、記憶體、磁盤、GPU 利用率及在運工作負載狀態</li>
    <li><strong>遠程工作負載</strong>：接收平臺下發的部署/停止指令，在節點本地拉起 AI 模型服務、算法任務、音視頻轉碼等工作負載</li>
    <li><strong>媒體節點池</strong>：支持在節點上遠程部署流媒體能力，實現設備與媒體節點綁定及流地址生成</li>
    <li><strong>節點角色</strong>：支持算力、媒體、混合三種角色，支撐 AI 推理、算法任務與流媒體業務的跨節點調度與彈性擴容</li>
    <li><strong>離線友好</strong>：支持離線依賴打包與 Agent 熱更新，適配無外網或受限網路環境下的批量節點納管</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>VIDEO模組</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>流媒體處理</strong>：支持RTSP/RTMP流即時處理與傳輸</li>
    <li><strong>算法任務管理</strong>：支持即時算法任務和抓拍算法任務兩種類型，分別用於即時畫面分析和抓拍圖像分析</li>
    <li><strong>抽幀器與排序器</strong>：支持靈活的抽幀策略與結果排序機制，每個算法任務可綁定獨立的抽幀器和排序器</li>
    <li><strong>佈防時段</strong>：支持全防模式和半防模式的時段化配置</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>AI模組</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>智能分析</strong>：負責視頻分析和AI算法執行</li>
    <li><strong>模型服務集羣</strong>：支持分佈式模型推理服務，實現負載均衡與高可用</li>
    <li><strong>即時推理</strong>：提供毫秒級響應的即時智能分析能力</li>
    <li><strong>模型管理</strong>：支持模型部署、版本管理與多實例調度</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>TASK模組</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">高性能任務處理模組，負責計算密集型任務執行</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>EDGE模組</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>無限聯邦邊緣集羣模式</strong>：第八核心模組，把智能能力從中心延伸到現場——普通開發板與邊緣節點可隨時加入值守網路，算力隨業務鋪開，告警與證據自動匯聚上雲</li>
    <li><strong>現場輕量值守</strong>：專注就近感知與研判回傳，不揹負重型管控界面與本地業務系統，降低邊緣部署門檻與長期運維負擔</li>
    <li><strong>開箱接入、統一納管</strong>：現場節點快速加入後由中心統一編排任務與策略，減少人工配置與分點分建成本</li>
    <li><strong>業務無縫延展</strong>：中心負責看全局、定規則，邊緣負責盯現場、快響應；節點數量可隨覆蓋範圍持續擴展，支撐即時分析、巡檢與抓拍等場景橫向鋪開</li>
    <li><strong>輕裝落地</strong>：邊緣側重「幹活」而非「堆設備」，讓廣域布點更容易落地、更容易複製</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>VISUALIZE模組</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>拖拽式大屏編輯器</strong>：第九核心模組，高性能低代碼可視化編輯器，專注畫布編輯與預覽</li>
    <li><strong>與 WEB 一體聯動</strong>：項目創建、模板、素材、數據源、發佈與投放在管理後臺「可視化」菜單完成；點擊「打開編輯器」即可進入畫布</li>
    <li><strong>大屏交付能力</strong>：圖表、指標與佈局拖拽配置，組件可掛接平臺數據源與 IoT 測點，支撐園區態勢、產線 KPI、設備運維、能源能耗等指揮大屏快速成屏</li>
    <li><strong>與組態分工清晰</strong>：指揮大屏走本模組編輯；工藝組態走 Web 組態能力；工程元數據統一由 DEVICE 側可視化後臺管理</li>
    <li><strong>部署形態</strong>：與 APP 同屬 full 完整版能力，mini / standard 可按現場硬體跳過，降低邊緣精簡部署體積</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>TRANSFORM模組</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>多向業務流轉</strong>：第十核心模組，把平臺側告警、設備事件與業務結果按約定投遞到 MES / ERP / CRM / WMS 等外部系統，打通「平臺有數 → 業務系統用得上」的最後一公里</li>
    <li><strong>可配置對接</strong>：數據目的、轉發規則與字段映射一次配好即可複用，減少「每接一家客戶系統就定制一套接口」的交付成本</li>
    <li><strong>投遞可驗收</strong>：運行集羣與投遞軌跡可監控、可回看，聯調與驗收能回答「轉沒轉到、卡在哪一步」，少靠口頭對賬</li>
    <li><strong>橫向擴展</strong>：流量上來後可按業務約定擴容消費與投遞能力，支撐多產線、多工廠、多系統並行對接</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>PANEL模組</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>交付與值守入口</strong>：第十一核心模組，獨立於業務管控臺——到場可裝、可驗、可守，縮短驗收週期，降低駐場與遠程支援成本</li>
    <li><strong>當天可閉環</strong>：按檔位界面化裝機，進度與結果當場可見，業務管控臺未就緒也能先把整機拉起來並交出去</li>
    <li><strong>自助排障</strong>：容器健康、資源水位、任務日誌與鏡像就緒度一目了然，常見啓停、拉鏡像、清緩存不必等開發敲命令</li>
    <li><strong>多現場複用</strong>：同一套入口貫穿多臺一體機與多處機房，PoC 與量產交付口徑一致</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>COMPILE打包</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>多平臺交付物</strong>：把 PANEL 等能力打成 Ubuntu / Debian、CentOS / RHEL、Windows、macOS 及 ARM / 麒麟等目標安裝包或可執行文件，方便給客戶裝機，不必現場從源碼編譯</li>
    <li><strong>縮短交付鏈路</strong>：集成商可按目標環境取對應安裝包完成部署與升級，安裝、啓停與卸載路徑統一，降低跨系統交付差異</li>
    <li><strong>與 PANEL 配套</strong>：打包產物可直接用於現場運維入口落地，讓「能打包出去」和「到場能裝能守」同一條交付鏈打通</li>
  </ul>
</td>
</tr>
</table>

## 🖥️ 跨平臺部署優勢

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT支持在Linux、Mac、Windows三大主流作業系統上部署，爲不同環境下的用戶提供靈活便捷的部署方案；配套 <strong>COMPILE</strong> 可按目標系統產出安裝包與可執行文件，配合 <strong>PANEL</strong> 完成到場裝機與日常值守：
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🐧 Linux部署優勢</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>適合生產環境，穩定可靠，資源佔用低</li>
  <li>支持Docker容器化部署，一鍵啓動所有服務</li>
  <li>完美適配伺服器、邊緣計算設備（如RK3588等ARM架構設備）</li>
  <li>提供完整的自動化安裝腳本，簡化部署流程</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🍎 Mac部署優勢</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>適合開發測試環境，與macOS系統深度集成</li>
  <li>支持本地開發和調試，快速驗證功能</li>
  <li>提供便捷的安裝腳本，支持Homebrew等包管理器</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🪟 Windows部署優勢</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>適合Windows伺服器環境，降低學習成本</li>
  <li>支持PowerShell自動化腳本，簡化部署操作</li>
  <li>兼容Windows Server和桌面版Windows系統</li>
  <li>提供圖形化安裝嚮導，用戶友好</li>
</ul>
</div>

</div>


<p style="font-size: 14px; line-height: 1.8; color: #2c3e50; font-weight: 500; margin: 20px 0; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #3498db; border-radius: 4px;">
<strong>統一體驗</strong>：無論選擇哪種作業系統，EasyAIoT都提供一致的安裝腳本和部署文件，確保跨平臺部署體驗的一致性。
</p>

## ☁️ EasyAIoT = AI + IoT = 雲邊端一體化解決方案

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
支持上千種垂直場景，支持AI模型定製化和AI算法定製化開發，深度融合。
</p>

<div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3498db;">
<h3 style="color: #2c3e50; margin-top: 0;">賦能萬物智視：EasyAIoT</h3>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
構築了物聯網設備（尤其是海量攝像頭）的高效接入與管控網路。我們深度融合流媒體即時傳輸技術與前沿人工智能（AI），打造一體化服務核心。這套方案不僅打通了異構設備的互聯互通，更將高清視頻流與強大的AI解析引擎深度集成，賦予監控系統"智能之眼"——精準實現人臉識別、異常行爲分析、風險人員布控及周界入侵檢測。
</p>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
平臺支持兩種類型的算法任務：即時算法任務用於RTSP/RTMP流的即時畫面分析，提供毫秒級響應能力；抓拍算法任務用於抓拍圖像的智能分析，支持事件回溯與圖像檢索。通過算法任務管理實現靈活的抽幀與排序策略，每個任務可綁定獨立的抽幀器和排序器，結合模型服務集羣推理能力，確保毫秒級響應與高可用保障。同時，提供全防模式和半防模式兩種佈防策略，可根據不同時段靈活配置監控規則，實現精準的時段化智能監控與告警。
</p>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
在物聯網設備管理方面，EasyAIoT提供完整的設備生命週期管理能力，支持多種物聯網與工業協議（MQTT、TCP、HTTP、Modbus-TCP、Modbus-RTU、OPC UA），實現設備的快速接入、安全認證、即時監控和智能控制。通過規則引擎實現設備數據的智能流轉與處理，結合AI能力對設備數據進行深度分析，實現從設備接入、數據採集、智能分析到決策執行的全流程自動化，真正實現萬物互聯、萬物智控。
</p>
</div>

<img src=".image/iframe1.jpg" alt="EasyAIoT平台架构" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">

## ⚠️ 免責聲明

EasyAIoT是一個開源學習項目，與商業行爲無關。用戶在使用該項目時，應遵循法律法規，不得進行非法活動。如果EasyAIoT發現用戶有違法行爲，將會配合相關機關進行調查並向政府部門舉報。用戶因非法行爲造成的任何法律責任均由用戶自行承擔，如因用戶使用造成第三方損害的，用戶應當依法予以賠償。使用EasyAIoT所有相關資源均由用戶自行承擔風險.

## 📚 部署文件

- [平臺部署文件](.doc/部署文件/平臺部署文件_zh.md) — Linux / Mac / Windows 分步部署指南
- [部署最佳實踐](.doc/部署文件/部署最佳實踐.md) — 環境要求、一鍵部署流程、運維排錯與生產環境建議

## 🎮 演示環境

- 演示地址：http://36.111.47.113:8888/
- 帳號：admin
- 密碼：admin123

## ⚙️ 項目地址

- Gitee: https://gitee.com/soaring-xiongkulu/easyaiot
- Github: https://github.com/soaring-xiongkulu/easyaiot

## 📸 截圖

<div>
  <img src=".image/banner/banner-video1000.gif" alt="演示" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner-video1001.gif" alt="演示" width="49%">
</div>

#### 🖥️ 監控大屏

| | | |
|:---:|:---:|:---:|
| ![態勢](.image/banner/banner1001.png) | ![總覽](.image/banner/banner1076.jpg) | ![告警](.image/banner/banner1074.jpg) |
| ![看板](.image/banner/banner1075.jpg) | ![多維](.image/banner/banner1095.jpg) | ![綜合](.image/banner/banner1096.jpg) |
| ![監控](.image/banner/banner1078.jpg) | ![即時](.image/banner/banner1077.jpg) |  |

#### 📺 可視化組態

| | | |
|:---:|:---:|:---:|
| ![項目](.image/banner/banner1185.png) | ![組態](.image/banner/banner1186.png) | ![編輯](.image/banner/banner1187.png) |
| ![預覽](.image/banner/banner1188.png) | ![組件](.image/banner/banner1189.png) | ![數據源](.image/banner/banner1190.png) |
| ![發佈](.image/banner/banner1191.png) | ![運行](.image/banner/banner1192.png) | ![模板](.image/banner/banner1193.png) |
| ![資產](.image/banner/banner1194.png) | ![大屏](.image/banner/banner1195.png) | ![展示](.image/banner/banner1196.png) |

#### 📹 視頻監控

| | | |
|:---:|:---:|:---:|
| ![直播](.image/banner/banner1145.jpg) | ![預覽](.image/banner/banner1146.jpg) | ![攝像頭](.image/banner/banner1051.jpg) |
| ![列表](.image/banner/banner1053.jpg) | ![推流](.image/banner/banner1083.jpg) | ![轉發](.image/banner/banner1084.jpg) |
| ![存儲](.image/banner/banner1121.png) | ![抓拍](.image/banner/banner1122.png) | ![錄像](.image/banner/banner1123.png) |
| ![配置](.image/banner/banner1124.png) | ![容量](.image/banner/banner1125.png) | ![回放](.image/banner/banner1126.png) |
| ![抓拍](.image/banner/banner1117.png) | ![文件](.image/banner/banner1118.png) | ![策略](.image/banner/banner1119.png) |
| ![配額](.image/banner/banner1120.png) | ![圖庫](.image/banner/banner1057.jpg) | ![歸檔](.image/banner/banner1058.jpg) |
| ![監控](.image/banner/banner1068.jpg) | ![統計](.image/banner/banner1069.jpg) | ![地圖](.image/banner/banner1113.png) |
| ![定位](.image/banner/banner1114.png) | ![分佈](.image/banner/banner1115.png) | ![點位](.image/banner/banner1116.png) |
| ![實況](.image/banner/banner1026.jpg) | ![多路](.image/banner/banner1028.jpg) | ![推流](.image/banner/banner1103.png) |
| ![預覽](.image/banner/banner1104.png) | ![接入](.image/banner/banner1105.png) | ![NVR](.image/banner/banner1106.png) |
| ![實況](.image/banner/banner1183.jpg) | ![地圖](.image/banner/banner1184.jpg) |  |

#### 🧠 AI模型

| | | |
|:---:|:---:|:---:|
| ![Qwen](.image/banner/banner1093.jpg) | ![視覺模型](.image/banner/banner1094.jpg) | ![列表](.image/banner/banner1099.png) |
| ![配置](.image/banner/banner1100.png) | ![詳情](.image/banner/banner1101.png) | ![調用](.image/banner/banner1102.png) |
| ![訓練](.image/banner/banner1019.jpg) | ![任務](.image/banner/banner1020.jpg) | ![列表](.image/banner/banner1023.jpg) |
| ![進度](.image/banner/banner1024.jpg) | ![參數](.image/banner/banner1017.jpg) | ![評估](.image/banner/banner1018.jpg) |
| ![詳情](.image/banner/banner1021.jpg) | ![日誌](.image/banner/banner1022.jpg) | ![管理](.image/banner/banner1097.png) |
| ![倉庫](.image/banner/banner1098.png) | ![版本](.image/banner/banner1039.jpg) | ![資產](.image/banner/banner1061.jpg) |
| ![推理](.image/banner/banner1040.jpg) | ![配置](.image/banner/banner1042.jpg) | ![結果](.image/banner/banner1043.jpg) |
| ![在線](.image/banner/banner1044.jpg) | ![批量](.image/banner/banner1047.jpg) | ![監控](.image/banner/banner1048.jpg) |
| ![服務](.image/banner/banner1045.jpg) | ![部署](.image/banner/banner1046.jpg) | ![集羣](.image/banner/banner1049.jpg) |
| ![調用](.image/banner/banner1050.jpg) | ![權重](.image/banner/banner1111.png) | ![下載](.image/banner/banner1112.png) |
| ![姿態](.image/banner/banner1147.jpg) | ![識別](.image/banner/banner1148.jpg) | ![任務](.image/banner/banner1085.jpg) |
| ![配置](.image/banner/banner1086.jpg) | ![詳情](.image/banner/banner1087.jpg) | ![運行](.image/banner/banner1088.jpg) |
| ![區域](.image/banner/banner1079.jpg) | ![檢測框](.image/banner/banner1080.jpg) | ![佈防](.image/banner/banner1081.jpg) |
| ![預覽](.image/banner/banner1082.jpg) | ![算法](.image/banner/banner1062.jpg) | ![創建](.image/banner/banner1063.png) |
| ![畫面](.image/banner/banner1064.jpg) | ![分析](.image/banner/banner1065.jpg) | ![結果](.image/banner/banner1066.jpg) |
| ![回看](.image/banner/banner1067.jpg) | ![實況](.image/banner/banner1052.jpg) | ![智能](.image/banner/banner1054.jpg) |

#### 📦 數據集

| | | |
|:---:|:---:|:---:|
| ![管理](.image/banner/banner1015.png) | ![列表](.image/banner/banner1010.jpg) | ![標註](.image/banner/banner1027.png) |
| ![任務](.image/banner/banner1016.jpg) | ![工具](.image/banner/banner1059.jpg) | ![預覽](.image/banner/banner1060.jpg) |
| ![詳情](.image/banner/banner1107.png) | ![導入](.image/banner/banner1108.png) | ![項目](.image/banner/banner1109.png) |
| ![審覈](.image/banner/banner1110.png) | ![創建](.image/banner/banner1007.jpg) | ![樣本](.image/banner/banner1008.jpg) |

#### 🔌 物聯網

| | | |
|:---:|:---:|:---:|
| ![物模型](.image/banner/banner1149.jpg) | ![定義](.image/banner/banner1150.jpg) | ![產品](.image/banner/banner1151.jpg) |
| ![詳情](.image/banner/banner1152.jpg) | ![設備](.image/banner/banner1153.jpg) | ![詳情](.image/banner/banner1154.jpg) |
| ![狀態](.image/banner/banner1155.jpg) | ![屬性](.image/banner/banner1156.jpg) | ![服務](.image/banner/banner1157.jpg) |
| ![事件](.image/banner/banner1158.jpg) | ![影子](.image/banner/banner1159.jpg) | ![拓撲](.image/banner/banner1160.jpg) |
| ![子設備](.image/banner/banner1161.jpg) | ![分組](.image/banner/banner1162.jpg) | ![控制](.image/banner/banner1163.jpg) |
| ![遙測](.image/banner/banner1164.jpg) | ![歷史](.image/banner/banner1165.jpg) | ![協議](.image/banner/banner1166.jpg) |
| ![連接](.image/banner/banner1167.jpg) | ![認證](.image/banner/banner1168.jpg) | ![調試](.image/banner/banner1169.jpg) |
| ![功能](.image/banner/banner1170.jpg) | ![讀寫](.image/banner/banner1171.jpg) | ![服務](.image/banner/banner1172.jpg) |
| ![訂閱](.image/banner/banner1173.jpg) | ![日誌](.image/banner/banner1174.jpg) | ![在線](.image/banner/banner1175.jpg) |
| ![統計](.image/banner/banner1176.jpg) | ![總覽](.image/banner/banner1177.jpg) | ![看板](.image/banner/banner1178.jpg) |
| ![產品](.image/banner/banner1006.jpg) | ![設備](.image/banner/banner1009.jpg) | ![OTA](.image/banner/banner1179.jpg) |
| ![固件](.image/banner/banner1180.jpg) | ![任務](.image/banner/banner1181.jpg) | ![進度](.image/banner/banner1182.jpg) |
| ![規則](.image/banner/banner1013.jpg) | ![編排](.image/banner/banner1014.png) |  |

#### 🖥️ 集羣

| | | |
|:---:|:---:|:---:|
| ![概覽](.image/banner/banner1127.jpg) | ![算力](.image/banner/banner1128.jpg) | ![節點](.image/banner/banner1129.jpg) |
| ![詳情](.image/banner/banner1130.jpg) | ![監控](.image/banner/banner1131.jpg) | ![調度](.image/banner/banner1132.jpg) |
| ![列表](.image/banner/banner1133.jpg) | ![狀態](.image/banner/banner1134.jpg) | ![配置](.image/banner/banner1135.jpg) |
| ![分配](.image/banner/banner1136.jpg) |  |  |

#### 🔔 告警

| | | |
|:---:|:---:|:---:|
| ![事件](.image/banner/banner1089.jpg) | ![處理](.image/banner/banner1090.jpg) | ![通知](.image/banner/banner1029.jpg) |
| ![配置](.image/banner/banner1030.jpg) | ![列表](.image/banner/banner1072.jpg) | ![詳情](.image/banner/banner1031.jpg) |
| ![處置](.image/banner/banner1070.jpg) | ![統計](.image/banner/banner1071.jpg) |  |

#### ⚙️ 系統

| | | |
|:---:|:---:|:---:|
| ![標識](.image/banner/banner1143.jpg) | ![重置](.image/banner/banner1144.jpg) | ![用戶](.image/banner/banner1003.png) |
| ![權限](.image/banner/banner1004.png) | ![菜單](.image/banner/banner1005.png) | ![配置](.image/banner/banner1002.png) |

#### 📱 APP

| | | |
|:---:|:---:|:---:|
| ![首頁](.image/banner/app/app_1000.jpg) | ![監控](.image/banner/app/app_1001.jpg) | ![預覽](.image/banner/app/app_1002.jpg) |
| ![告警](.image/banner/app/app_1003.jpg) | ![回放](.image/banner/app/app_1004.jpg) | ![設備](.image/banner/app/app_1005.jpg) |
| ![消息](.image/banner/app/app_1006.jpg) | ![我的](.image/banner/app/app_1007.jpg) |  |

## 📞 聯絡方式

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
請先關注下方公衆號，再通過技術交流羣或微信號與我們聯絡。
</p>

## 👥 公衆號

<div>
  <img src=".image/公众号.jpg" alt="公众号" width="30%">
</div>

## 💬 技術交流羣

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
關注公衆號後，使用微信掃描下方二維碼加入 EasyAIoT 技術交流羣。
</p>

<div>
  <img src=".image/交流群3群.jpg" alt="EasyAIoT技术交流3群" width="30%">
</div>

## 💬 微信號聯絡

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
關注公衆號後，如需一對一溝通，可掃描下方二維碼添加微信好友。
</p>

<div>
  <img src=".image/微信联系方式.jpg" alt="微信号联系方式" width="200">
</div>

## 🪐 知識星球：

<p>
  <img src=".image/知识星球.jpg" alt="知识星球" width="30%">
</p>

## 💰 打賞讚助

<div>
    <img src=".image/微信支付.jpg" alt="微信支付" width="30%" height="30%">
    <img src=".image/支付宝支付.jpg" alt="支付宝支付" width="30%" height="10%">
</div>

## 🤝 貢獻指南

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
我們歡迎所有形式的貢獻！無論您是代碼開發者、文件編寫者，還是問題反饋者，您的貢獻都將幫助 EasyAIoT 變得更好。以下是幾種主要的貢獻方式：
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">💻 代碼貢獻</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Fork 項目到您的 GitHub/Gitee 帳號</li>
  <li>創建特性分支 (git checkout -b feature/AmazingFeature)</li>
  <li>提交更改 (git commit -m 'Add some AmazingFeature')</li>
  <li>推送到分支 (git push origin feature/AmazingFeature)</li>
  <li>提交 Pull Request</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">📚 文件貢獻</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>完善現有文件內容</li>
  <li>補充使用示例和最佳實踐</li>
  <li>提供多語言翻譯</li>
  <li>修正文件錯誤</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🌟 其他貢獻方式</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>報告並修復 Bug</li>
  <li>提出功能改進建議</li>
  <li>參與社區討論，幫助其他開發者</li>
  <li>分享使用經驗和案例</li>
</ul>
</div>

</div>

## 🌟 重大貢獻者

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
以下是對EasyAIoT項目做出重大貢獻的傑出貢獻者，他們的貢獻對項目的發展起到了關鍵推動作用，我們表示最誠摯的感謝！
</p>

<table style="width: 100%; table-layout: fixed; border-collapse: collapse; margin: 20px 0; font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
<thead>
<tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
<th style="padding: 15px; text-align: left; font-weight: 600; border: 1px solid #e0e0e0; width: 32%; min-width: 9rem;">貢獻者</th>
<th style="padding: 15px; text-align: left; font-weight: 600; border: 1px solid #e0e0e0;">貢獻內容</th>
</tr>
</thead>
<tbody>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>℡夏别</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">爲推動EasyAIoT項目貢獻Windows部署文件，爲Windows平臺用戶提供了完整的部署指南，大大降低了Windows環境下的部署難度，讓更多用戶能夠便捷地使用EasyAIoT平臺。</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>YiYaYiYaho</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">爲推動EasyAIoT項目貢獻Mac容器一鍵部署腳本，爲Mac平臺用戶提供了自動化部署解決方案，顯著簡化了Mac環境下的部署流程，提升了開發者和用戶的部署體驗。</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>山寒</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">爲推動EasyAIoT項目貢獻Linux容器部署腳本，爲Linux平臺用戶提供了容器化部署方案，實現了快速、可靠的容器部署，爲生產環境的穩定運行提供了重要保障。</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>玖零。</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">爲推動EasyAIoT項目貢獻Linux容器部署腳本，進一步完善了Linux平臺的容器化部署方案，爲不同Linux發行版用戶提供了更多選擇，推動了項目的跨平臺部署能力。</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>爱吃小柚子</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">爲推動 EasyAIoT 項目在「訓得動、訓得穩、訓得省心」方向的發展，系統性打通多卡訓練、斷點續訓與節點側部署能力，讓現場算力真正用得上、訓練任務真正控得住：支持自動識別並使用伺服器全部 GPU，用戶可在訓練頁按需選擇單卡或多卡，不再受限於只能看到一張卡；兼容多種常見數據集格式與目錄結構，支持大容量本地數據集上傳，訓練失敗後仍可保留原始數據快速重試，顯著降低數據準備與反覆折騰的成本；完善訓練進度可見、任務可停可續，避免中斷後成果丟失、點擊停止卻仍在後臺空轉等痛點，使本地與遠程訓練調度在失敗時也能及時回退、給出清晰反饋；同步優化前端訓練任務的 GPU 選擇、繼續訓練與停止狀態展示，並修復模型發佈誤判失敗、自定義預覽圖被覆蓋、按名稱/版本查不到模型以及數據集同步易超時、易衝突等問題，讓「訓練—發佈—使用」閉環更順暢可靠。此前亦主導國標 GB28181 與 AI 業務流程的端到端聯調驗證及畫面清晰度專項評估，爲國標接入可靠性與視頻觀感優化提供了重要依據。</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>Dark</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">爲推動EasyAIoT項目在國標視頻監控方向的發展，貢獻 GB28181 能力的端到端打通，實現視頻播放與雲臺控制，使國標設備接入具備可用的實況預覽與遠程操控能力。</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>machh</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">爲推動 EasyAIoT-Edge 項目的發展，完成攝像頭接入與 AI 能力的端到端跑通，並實現功能串聯，使邊緣側「接入—智能分析」鏈路可用、可閉環。</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>遗忘的星空</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">爲推動 EasyAIoT 項目在設備直連接入方向的發展，貢獻多品牌 IP 攝像頭資產盤點與網段掃描能力，支持海康 IPC、NVR 等設備的批量發現與識別；完善直連設備在同網段、跨網段場景下的批量搜索與一鍵註冊流程，基於設備原生協議實現接入，可繞過海康 SDK、擺脫對海康平臺的強依賴，爲開放、可控的攝像頭規模化接入奠定了基礎。</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>阿龙</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">爲推動 EasyAIoT 項目在地圖可視化與空間研判方向的發展，獨立貢獻天地圖空間可視化能力的完整代碼實現，涵蓋國家天地圖底圖接入、攝像頭與告警設備布點、地圖分佈視圖、地點搜索與座標批量導入、告警事件自動上圖、以人/以車尋跡及移動設備軌跡回放等核心鏈路，使平臺「天地圖空間可視化與以圖研判」能力從方案設計真正走向可落地、可使用的生產形態。</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>雨落流殇</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">爲推動 EasyAIoT 項目在超大規模流媒體承載方向的發展，貢獻異構流媒體伺服器集羣的部署與調度思路，提出多節點池協同、流媒體與業務層解耦及節點註冊調度等可擴展方案，爲平臺支撐萬級路攝像頭併發接入、穩定分發與彈性擴容奠定了重要的架構基礎。</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>常康</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">爲推動 EasyAIoT 項目在智能交通與車輛管控方向的發展，獨立貢獻車牌識別算法與完整代碼實現，涵蓋車牌定位檢測、號碼與顏色識別、雙層牌拼接與傾斜透視校正、車牌庫管理與多庫順序匹配、算法任務一鍵聯動及異步比對等核心鏈路，全面支持藍/黃/綠/白牌及新能源車牌等主流類型，使平臺「車牌識別與車牌庫管理能力」從能力規劃真正走向可落地、可閉環的生產應用。</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>Li</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">爲推動 EasyAIoT 項目在青年開發者社羣與協作生態方向的發展，以卓越的組織領導力與感召力，帶領全校同學深度參與項目共建，匯聚青春才智、凝聚團隊合力，爲 EasyAIoT 注入了源源不斷、綿延不絕的發展動能；在項目傳播推廣、實踐落地與後續人才梯隊培育等方面，亦作出了舉足輕重、不可替代的重要貢獻。</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>陈家林</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">爲推動 EasyAIoT 項目在物聯網設備互通、工業協議接入與空天視頻融合方向的發展，打通設備指令與狀態數據的上下行閉環，使平臺真正實現「下得去、看得見、控得住」；系統性貢獻 Modbus-TCP、Modbus-RTU、OPC UA 工業協議接入能力，完成以太網側與串口側工控設備及 OPC UA 節點的統一採集、測點讀寫與物模型映射，使電錶、傳感器、PLC、控制器等海量工業設備數據可被平臺統一匯聚、監測與聯動，補齊「看得見現場、也聽得到設備」的關鍵拼圖；同時貢獻大疆司空機場與無人機畫面接入能力，把空中巡檢視角納入統一視頻與告警體系，顯著拓展平臺在工控數採、產線智控、廣域巡查、應急勘察與天地一體協同感知中的落地價值。</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>空空</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">爲推動 EasyAIoT 項目在攝像頭直連「從能發現走向能落地」方向的發展，補齊直連接入在認證、通道同步、配置變更與多品牌出流等關鍵短板，使平臺在真實 NVR / 多廠商現場具備可交付的可用性：打通設備登入認證，讓直連設備真正「登得進、管得住」；完善 NVR 同步通道後的取流模型，讓批量同步出來的流可播、可用，顯著提升 NVR 規模化接入效率；保障接入參數可持續維護；同步建設國內常用監控品牌出流規則庫，並開放自定義品牌規則，使異廠商、異型號設備可一鍵出流，不必依賴人工試地址，把直連能力從「掃得到設備」推進到「登得進、同步準、改得了、多品牌都能出流」的生產可用形態，爲後續雲臺與變焦等操控能力完善奠定堅實基礎。</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>狗娃</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">爲推動 EasyAIoT 項目在「物聯網數據可展成屏」方向的發展，前瞻提出可視化 Board（拖拽看板）模組的產品構想：傳統大屏往往每張屏、每個組件都要獨立手寫查詢，交付慢、改一次動全身、業務人員幾乎無法自助做屏。Board 方案把圖表、指標與佈局交給拖拽畫布配置，並把組件直接掛接平臺 IoT 物模型測點——即時值與歷史值從設備側一鍵取用；讓園區態勢、產線 KPI、設備運維等大屏從「開發寫查詢才能出屏」升級爲「選測點、拖組件即可成屏」，顯著縮短可視化交付週期，把 IoT「後臺有數」真正變成「前臺有屏」的可運營能力。此前亦貢獻傳感器浮點數據預測、運行狀態屬性上下閾值配置、閾值告警與規則聯動，以及中心設備關聯子設備運行狀態一屏展示，打通「預測—定界—告警—規則—一屏掌控」設備運行閉環，使平臺設備側具備「看得見數、管得住界、告得出警、看得清全局」的能力。</td>
</tr>
</tbody>
</table>

<p style="font-size: 14px; line-height: 1.8; color: #2c3e50; font-weight: 500; margin: 20px 0; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #3498db; border-radius: 4px;">
<strong>特別緻謝</strong>：以上貢獻者在跨平臺部署文件與腳本、國標視頻能力落地與 AI 聯調驗證、多卡訓練與斷點續訓、多品牌攝像頭直連發現與批量接入、天地圖空間可視化、異構流媒體集羣部署與調度、車牌識別算法與完整代碼、EasyAIoT-Edge 邊緣側端到端串聯、校園開發者社羣組織與青年協作生態構建、物聯網設備上下行閉環與大疆司空空中視角接入、Modbus-TCP / Modbus-RTU / OPC UA 工業協議接入、攝像頭直連從發現到登入/同步/配置/多品牌出流的閉環、拖拽看板（Board）構想與 IoT 測點即時/歷史值直取集成、傳感器浮點數據預測與閾值告警規則及中心設備關聯子設備運行狀態一屏展示等不同方面推動了 EasyAIoT 的發展，他們的專業精神與無私奉獻值得我們學習與尊敬。再次向這些傑出的貢獻者表示最誠摯的感謝！🙏
</p>

## 💝 開源守望者

開源專案的持續推進，從來不只依賴程式碼與文件。在 EasyAIoT 算力資源最吃緊、專案幾近難以為繼的那些日子裡，正是以下各位以真金白銀的支持，為專案注入了最關鍵的續航——你們或許未曾提交一行程式碼，但每一份信任與托舉，都讓這個專案得以跨過最難的檻、繼續向前迭代。只要有人在用、有人在撐，開源生態便值得走得更遠；EasyAIoT 今日所能抵達的高度，離不開這些在關鍵時刻雪中送炭的同行者。我們向每一位給予援手的朋友致以最誠摯的敬意與感謝！以下排名不分先後：

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
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/在路上.png" width="80px;" alt="在路上"/><br /><sub><b>在路上</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/忘记时间.png" width="80px;" alt="忘记时间"/><br /><sub><b>忘记时间</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/HuaZy.jpg" width="80px;" alt="HuaZy"/><br /><sub><b>HuaZy</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/ANDY.png" width="80px;" alt="ANDY"/><br /><sub><b>ANDY</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/A许庆.png" width="80px;" alt="A许庆"/><br /><sub><b>A许庆</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/刘兆中📶⁵ᴳ.png" width="80px;" alt="刘兆中📶⁵ᴳ"/><br /><sub><b>刘兆中📶⁵ᴳ</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/冯.png" width="80px;" alt="冯"/><br /><sub><b>冯</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/莫斯克.png" width="80px;" alt="莫斯克"/><br /><sub><b>莫斯克</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/赵欢.png" width="80px;" alt="赵欢"/><br /><sub><b>赵欢</b></sub></a></td>
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
    </tr>
  </tbody>
</table>

## 🏆 最佳實踐者

他們是將 EasyAIoT 從「可用」推向「好用、用好」的先行者——以下各位已完成 EasyAIoT 專案部署或業務場景落地，其探索與成果為社群樹立了可複製、可參考的標竿，我們向這些卓越實踐者致以崇高敬意與衷心祝賀！以下排名不分先後：

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

## 🙏 致謝

感謝以下各位對本項目包括但不限於代碼貢獻、問題反饋、資金捐贈等各種方式的支持！以下排名不分先後：
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/默者.png" width="80px;" alt="歐陽建輝"/><br /><sub><b>歐陽建輝</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/小满藏舟.png" width="80px;" alt="小滿藏舟"/><br /><sub><b>小滿藏舟</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/空空.png" width="80px;" alt="空空"/><br /><sub><b>空空</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/chen_jialin123" target="_blank"><img src="./.image/sponsor/陈家林.png" width="80px;" alt="陳家林"/><br /><sub><b>陳家林</b></sub></a></td>
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

## 💡 期望

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
歡迎提出更好的意見，幫助完善 easyaiot
</p>

## 📄 版權

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
翱翔的雄庫魯/easyaiot 採用 <a href="https://gitee.com/soaring-xiongkulu/easyaiot/blob/main/LICENSE" style="color: #3498db; text-decoration: none; font-weight: 600;">MIT LICENSE</a> 開源協議。我們致力於推動 AI 技術的普及與發展，讓更多人能夠自由使用和受益於這項技術。
</p>

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
<strong>使用許可</strong>：個人與企業可 100% 免費使用，無需保留作者、Copyright 資訊。我們相信技術的價值在於被廣泛使用和持續創新，而非被版權束縛。希望您能夠自由地使用、修改、分發本項目，讓 AI 技術真正惠及每一個人。
</p>

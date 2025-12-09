# EasyAIoT（雲邊端一體化智能算法應用平臺）

[![Gitee star](https://gitee.com/volara/easyaiot/badge/star.svg?theme=gvp)](https://gitee.com/soaring-xiongkulu/easyaiot/stargazers)
[![Gitee fork](https://gitee.com/volara/easyaiot/badge/fork.svg?theme=gvp)](https://gitee.com/soaring-xiongkulu/easyaiot/members)

<p style="font-size: 16px; line-height: 1.8; color: #555; font-weight: 400; margin: 20px 0;">
我希望全世界都能使用這個系統，實現AI的真正0門檻，人人都能體驗到AI帶來的好處，而並不只是掌握在少數人手裏。
</p>

<div align="center">
    <img src=".image/logo.png" width="30%" height="30%" alt="EasyAIoT">
</div>

<h4 align="center" style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; padding: 20px; font-weight: bold;">
  <a href="./README.md">English</a>
  <span style="display: flex; align-items: center; color: #666; font-weight: bold;">|</span>
  <a href="./README_zh.md">簡體中文</a>
  <span style="display: flex; align-items: center; color: #666; font-weight: bold;">|</span>
  <a href="./README_zh_tw.md">繁體中文</a>
  <span style="display: flex; align-items: center; color: #666; font-weight: bold;">|</span>
  <a href="./README_ru.md">Русский</a>
  <span style="display: flex; align-items: center; color: #666; font-weight: bold;">|</span>
  <a href="./README_fr.md">Français</a>
  <span style="display: flex; align-items: center; color: #666; font-weight: bold;">|</span>
  <a href="./README_ko.md">한국어</a>
</h4>

## 🌟 關於項目的一些思考

### 📍 項目定位

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT是一個雲邊端一體化的智能物聯網平臺，專註於AI與IoT的深度融合。平臺通過算法任務管理、實時流分析、模型服務集群推理等核心能力，實現從設備接入到數據采集、AI分析、智能決策的全鏈路閉環，真正實現萬物互聯、萬物智控。
</p>

#### 🧠 AI能力

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>攝像頭實時畫面AI分析</strong>：支持攝像頭實時畫面的AI智能分析，可對實時視頻流進行目標檢測、行為分析、異常識別等AI算法處理，提供毫秒級響應的實時分析結果，支持多路視頻並發分析</li>
  <li><strong>雲邊端一體算法預警監控大屏</strong>：提供統一的雲邊端一體化算法預警監控大屏，實時展示設備狀態、算法任務運行情況、告警事件統計、視頻流分析結果等關鍵信息，支持多維度數據可視化展示，實現雲端、邊緣端、設備端的統一監控與管理，為決策者提供全局視角的智能監控指揮中心</li>
  <li><strong>設備檢測區域繪制</strong>：提供可視化的設備檢測區域繪制工具，支持在設備抓拍圖片上繪制四邊形和多邊形檢測區域，支持區域與算法模型靈活關聯配置，支持區域的可視化管理、編輯、刪除等操作，支持快捷鍵操作提升繪制效率，實現精準的區域檢測配置，為算法任務提供精確的檢測範圍定義</li>
  <li><strong>智能聯動告警機制</strong>：支持檢測區域、布防時段和事件告警的三重聯動機制，系統會智能判斷檢測到的事件是否同時滿足指定的檢測區域範圍、處於布防時段內且匹配告警事件類型，只有同時滿足這三個條件時才會觸發告警，實現精準的時空條件過濾，大幅降低誤報率，提升告警系統的準確性和實用性</li>
  <li><strong>大規模攝像頭管理</strong>：支持百級攝像頭接入，提供采集、標註、訓練、推理、導出、分析、告警、錄像、存儲、部署等全流程服務</li>
  <li><strong>算法任務管理</strong>：支持創建和管理兩種類型的算法任務，每個算法任務可靈活綁定抽幀器和排序器，實現精準的視頻幀提取與結果排序
    <ul style="margin: 5px 0; padding-left: 20px;">
      <li><strong>實時算法任務</strong>：用於實時畫面分析，支持RTSP/RTMP流實時處理，提供毫秒級響應能力，適用於監控、安防等實時場景</li>
      <li><strong>抓拍算法任務</strong>：用於抓拍圖像分析，對抓拍圖片進行智能識別與分析，適用於事件回溯、圖像檢索等場景</li>
    </ul>
  </li>
  <li><strong>模型服務集群推理</strong>：支持分佈式模型推理服務集群，實現智能負載均衡、故障自動切換與高可用保障，大幅提升推理吞吐量與系統穩定性</li>
  <li><strong>布防時段管理</strong>：支持全防模式和半防模式兩種布防策略，可靈活配置不同時段的布防規則，實現精準的時段化智能監控與告警</li>
  <li><strong>OCR與語音識別</strong>：基於PaddleOCR實現高精度文字識別，支持語音轉文本功能，提供多語言識別能力</li>
  <li><strong>多模態視覺大模型</strong>：支持物體識別、文字識別等多種視覺任務，提供強大的圖像理解與場景分析能力</li>
  <li><strong>LLM大語言模型</strong>：支持RTSP流、視頻、圖像、語音、文本等多種輸入格式的智能分析與理解，實現多模態內容理解</li>
  <li><strong>模型部署與版本管理</strong>：支持AI模型的快速部署與版本管理，實現模型一鍵上線、版本回滾與灰度發布</li>
  <li><strong>多實例管理</strong>：支持多個模型實例的並發運行與資源調度，提高系統利用率與資源利用效率</li>
  <li><strong>攝像頭抓拍</strong>：支持攝像頭實時抓拍功能，可配置抓拍規則與觸發條件，實現智能抓拍與事件記錄</li>
  <li><strong>抓拍空間管理</strong>：提供抓拍圖片的存儲空間管理，支持空間配額與清理策略，確保存儲資源合理利用</li>
  <li><strong>錄像空間管理</strong>：提供錄像文件的存儲空間管理，支持自動清理與歸檔，實現存儲資源的智能管理</li>
  <li><strong>抓拍圖片管理</strong>：支持抓拍圖片的查看、檢索、下載、刪除等全生命周期管理，提供便捷的圖片管理功能</li>
  <li><strong>設備目錄管理</strong>：提供設備樹形目錄管理，支持設備分組、層級管理與權限控制，實現設備的有序組織與精細化管理</li>
  <li><strong>告警錄像</strong>：支持告警事件自動觸發錄像功能，當檢測到異常事件時自動錄制相關視頻片段，提供完整的告警證據鏈，支持告警錄像的查看、下載和管理</li>
  <li><strong>告警事件</strong>：提供完整的告警事件管理功能，支持告警事件的實時推送、歷史查詢、統計分析、事件處理與狀態跟蹤，實現告警全生命周期管理</li>
  <li><strong>錄像回放</strong>：支持歷史錄像的快速檢索與回放功能，提供時間軸定位、倍速播放、關鍵幀跳轉等便捷操作，支持多路視頻同步回放，滿足事件回溯與分析需求</li>
</ul>

#### 🌐 IoT能力

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>設備接入與管理</strong>：設備註冊、認證、狀態監控、生命周期管理</li>
  <li><strong>產品與物模型管理</strong>：產品定義、物模型配置、產品管理</li>
  <li><strong>多協議支持</strong>：MQTT、TCP、HTTP等多種物聯網協議</li>
  <li><strong>設備認證與動態註冊</strong>：安全接入、身份認證、動態設備註冊</li>
  <li><strong>規則引擎</strong>：數據流轉規則、消息路由、數據轉換</li>
  <li><strong>數據采集與存儲</strong>：設備數據采集、存儲、查詢與分析</li>
  <li><strong>設備狀態監控與告警管理</strong>：實時監控、異常告警、智能決策</li>
  <li><strong>通知管理</strong>：支持7種通知方式，包括飛書、釘釘、企業微信、郵件、騰訊雲短信、阿里雲短信、Webhook，實現靈活的多渠道告警通知</li>
</ul>


### 💡 技術理念

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
我們認為沒有任何一個編程語言能夠擅長所有事情，但通過三種編程語言的深度融合，EasyAIoT將發揮各自優勢，構建強大的技術生態。
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Java擅長構建穩定可靠的平臺架構，但不適合網絡編程和AI編程；Python擅長網絡編程和AI算法開發，但在高性能任務執行方面存在瓶頸；C++擅長高性能任務執行，但在平臺開發和AI編程方面不如前兩者。EasyAIoT采用三合一語言混編架構，充分發揮各語言優勢，構建一個實現頗具挑戰，但使用極其便捷的AIoT平臺。
</p>

![EasyAIoT平臺架構.jpg](.image/iframe2.jpg)

### 🔄 模塊數據流轉

<img src=".image/iframe3.jpg" alt="EasyAIoT平臺架構" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

### 🤖 零樣本標註技術

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
創新性地依托大模型構建零樣本標註技術體系（理想狀態下完全去除人工標註環節，實現標註流程的自動化），該技術通過大模型生成初始數據並借助提示詞技術完成自動標註，再經人機協同校驗確保數據質量（可選），進而訓練出初始小模型。該小模型通過持續叠代、自我優化，實現標註效率與模型精度的協同進化，最終推動系統性能不斷攀升。
</p>

<img src=".image/iframe4.jpg" alt="EasyAIoT平臺架構" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

### 🏗️ 項目架構特點

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
EasyAIoT其實不是一個項目，而是五個項目。
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
好處是什麽呢？假如說你在一個受限的設備上（比如RK3588），你只需要拿出其中某個項目就可以獨立部署，所以看似這個項目是雲平臺，其實他也可以是邊緣平臺。
</p>

<div style="margin: 30px 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;">

<p style="font-size: 16px; line-height: 1.8; margin: 0; font-weight: 500;">
🌟 真開源不易，如果這個項目對您有幫助，請您點亮一顆Star再離開，這將是對我最大的支持！<br>
<small style="font-size: 14px; opacity: 0.9;">（在這個假開源橫行的時代，這個項目就是一個異類，純靠愛來發電）</small>
</p>

</div>

### 🌍 本土化支持

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT積極響應本土化戰略，全面支持本土化硬件和操作系統，為用戶提供安全可控的AIoT解決方案：
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🖥️ 服務器端支持</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>完美兼容海光（Hygon）x86架構處理器</li>
  <li>支持本土化服務器硬件平臺</li>
  <li>提供針對性的性能優化方案</li>
  <li>確保企業級應用的穩定運行</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">📱 邊緣端支持</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>全面支持瑞芯微（Rockchip）ARM架構芯片</li>
  <li>完美適配RK3588等主流邊緣計算平臺</li>
  <li>針對邊緣場景進行深度優化</li>
  <li>實現邊緣智能的輕量化部署</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🖱️ 操作系統支持</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>兼容麒麟（Kylin）操作系統</li>
  <li>支持方德（Founder）等本土化Linux發行版</li>
  <li>適配統信UOS等主流本土化操作系統</li>
  <li>提供完整的本土化部署方案</li>
</ul>
</div>

</div>

## 🎯 適用場景

<img src=".image/適用場景.png" alt="適用場景" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

## 🧩 項目結構

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT由五個核心項目組成：
</p>

<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50; width: 20%;">模塊</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50;">描述</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>WEB模塊</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">基於Vue的前端管理界面，提供統一的用戶交互體驗</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>DEVICE模塊</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>技術優勢</strong>：基於JDK21，提供更好的性能和現代化特性</li>
    <li><strong>設備管理</strong>：設備註冊、認證、狀態監控、生命周期管理</li>
    <li><strong>產品管理</strong>：產品定義、物模型管理、產品配置</li>
    <li><strong>協議支持</strong>：MQTT、TCP、HTTP等多種物聯網協議</li>
    <li><strong>設備認證</strong>：設備動態註冊、身份認證、安全接入</li>
    <li><strong>規則引擎</strong>：數據流轉規則、消息路由、數據轉換</li>
    <li><strong>數據采集</strong>：設備數據采集、存儲、查詢與分析</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>VIDEO模塊</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>流媒體處理</strong>：支持RTSP/RTMP流實時處理與傳輸</li>
    <li><strong>算法任務管理</strong>：支持實時算法任務和抓拍算法任務兩種類型，分別用於實時畫面分析和抓拍圖像分析</li>
    <li><strong>抽幀器與排序器</strong>：支持靈活的抽幀策略與結果排序機制，每個算法任務可綁定獨立的抽幀器和排序器</li>
    <li><strong>布防時段</strong>：支持全防模式和半防模式的時段化配置</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>AI模塊</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>智能分析</strong>：負責視頻分析和AI算法執行</li>
    <li><strong>模型服務集群</strong>：支持分佈式模型推理服務，實現負載均衡與高可用</li>
    <li><strong>實時推理</strong>：提供毫秒級響應的實時智能分析能力</li>
    <li><strong>模型管理</strong>：支持模型部署、版本管理與多實例調度</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>TASK模塊</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">基於C++的高性能任務處理模塊，負責計算密集型任務執行</td>
</tr>
</table>

## 🖥️ 跨平臺部署優勢

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT支持在Linux、Mac、Windows三大主流操作系統上部署，為不同環境下的用戶提供靈活便捷的部署方案：
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🐧 Linux部署優勢</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>適合生產環境，穩定可靠，資源占用低</li>
  <li>支持Docker容器化部署，一鍵啟動所有服務</li>
  <li>完美適配服務器、邊緣計算設備（如RK3588等ARM架構設備）</li>
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
  <li>適合Windows服務器環境，降低學習成本</li>
  <li>支持PowerShell自動化腳本，簡化部署操作</li>
  <li>兼容Windows Server和桌面版Windows系統</li>
  <li>提供圖形化安裝向導，用戶友好</li>
</ul>
</div>

</div>


<p style="font-size: 14px; line-height: 1.8; color: #2c3e50; font-weight: 500; margin: 20px 0; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #3498db; border-radius: 4px;">
<strong>統一體驗</strong>：無論選擇哪種操作系統，EasyAIoT都提供一致的安裝腳本和部署文檔，確保跨平臺部署體驗的一致性。
</p>

## ☁️ EasyAIoT = AI + IoT = 雲邊端一體化解決方案

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
支持上千種垂直場景，支持AI模型定制化和AI算法定制化開發，深度融合。
</p>

<div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3498db;">
<h3 style="color: #2c3e50; margin-top: 0;">賦能萬物智視：EasyAIoT</h3>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
構築了物聯網設備（尤其是海量攝像頭）的高效接入與管控網絡。我們深度融合流媒體實時傳輸技術與前沿人工智能（AI），打造一體化服務核心。這套方案不僅打通了異構設備的互聯互通，更將高清視頻流與強大的AI解析引擎深度集成，賦予監控系統"智能之眼"——精準實現人臉識別、異常行為分析、風險人員布控及周界入侵檢測。
</p>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
平臺支持兩種類型的算法任務：實時算法任務用於RTSP/RTMP流的實時畫面分析，提供毫秒級響應能力；抓拍算法任務用於抓拍圖像的智能分析，支持事件回溯與圖像檢索。通過算法任務管理實現靈活的抽幀與排序策略，每個任務可綁定獨立的抽幀器和排序器，結合模型服務集群推理能力，確保毫秒級響應與高可用保障。同時，提供全防模式和半防模式兩種布防策略，可根據不同時段靈活配置監控規則，實現精準的時段化智能監控與告警。
</p>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
在物聯網設備管理方面，EasyAIoT提供完整的設備生命周期管理能力，支持多種物聯網協議（MQTT、TCP、HTTP），實現設備的快速接入、安全認證、實時監控和智能控制。通過規則引擎實現設備數據的智能流轉與處理，結合AI能力對設備數據進行深度分析，實現從設備接入、數據采集、智能分析到決策執行的全流程自動化，真正實現萬物互聯、萬物智控。
</p>
</div>

<img src=".image/iframe1.jpg" alt="EasyAIoT平臺架構" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">

## ⚠️ 免責聲明

EasyAIoT是一個開源學習項目，與商業行為無關。用戶在使用該項目時，應遵循法律法規，不得進行非法活動。如果EasyAIoT發現用戶有違法行為，將會配合相關機關進行調查並向政府部門舉報。用戶因非法行為造成的任何法律責任均由用戶自行承擔，如因用戶使用造成第三方損害的，用戶應當依法予以賠償。使用EasyAIoT所有相關資源均由用戶自行承擔風險.

## 📚 部署文檔

- [平臺部署文檔](.doc/部署文档/平台部署文档_zh_tw.md)

## 🎮 演示環境

- 演示地址：http://36.111.47.113:8888/
- 賬號：admin
- 密碼：admin123

## ⚙️ 項目地址

- Gitee: https://gitee.com/soaring-xiongkulu/easyaiot
- Github: https://github.com/soaring-xiongkulu/easyaiot

## 📸 截圖
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
  <img src=".image/banner/banner1079.jpg" alt="Screenshot 1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1080.jpg" alt="Screenshot 1" width="49%">
</div>
<div>
  <img src=".image/banner/banner1081.jpg" alt="Screenshot 1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1082.jpg" alt="Screenshot 1" width="49%">
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

## 🛠️ 服務支持

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
我們提供了各種服務方式幫助您深入了解EasyAIoT平臺和代碼，通過產品文檔、技術交流群、付費教學等方式，你將獲得如下服務：
</p>

<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
<thead>
<tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
<th style="padding: 15px; text-align: left; font-weight: 600;">服務項</th>
<th style="padding: 15px; text-align: left; font-weight: 600;">服務內容</th>
<th style="padding: 15px; text-align: center; font-weight: 600;">服務收費</th>
<th style="padding: 15px; text-align: left; font-weight: 600;">服務方式</th>
</tr>
</thead>
<tbody>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50;">系統部署</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">在客戶指定的網絡和硬件環境中完成EasyAIoT部署</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; text-align: center; color: #e74c3c; font-weight: 600;">500元</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">線上部署支持</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50;">技術支持</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">提供各類部署、功能使用中遇到的問題答疑</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; text-align: center; color: #e74c3c; font-weight: 600;">200元</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">半小時內 線上遠程支持</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50;">其他服務</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">垂直領域解決方案定制化開發；定制化時長、功能服務等</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; text-align: center; color: #e74c3c; font-weight: 600;">面議</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">面議</td>
</tr>
</tbody>
</table>

## 📞 聯系方式（添加微信後，需關註公眾號，拉入技術交流群）

<div>
  <img src=".image/聯系方式.jpg" alt="聯系方式" width="30%" style="margin-right: 50px;">
  <img src=".image/联系方式2.png" alt="聯系方式" width="30%">
</div>

## 👥 公眾號

<div>
  <img src=".image/公眾號.jpg" alt="公眾號" width="30%">
</div>

## 🪐 知識星球：

<p>
  <img src=".image/知識星球.jpg" alt="知識星球" width="30%">
</p>

## 💰 打賞贊助

<div>
    <img src=".image/微信支付.jpg" alt="微信支付" width="30%" height="30%">
    <img src=".image/支付寶支付.jpg" alt="支付寶支付" width="30%" height="10%">
</div>

## 🤝 貢獻指南

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
我們歡迎所有形式的貢獻！無論您是代碼開發者、文檔編寫者，還是問題反饋者，您的貢獻都將幫助 EasyAIoT 變得更好。以下是幾種主要的貢獻方式：
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">💻 代碼貢獻</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Fork 項目到您的 GitHub/Gitee 賬號</li>
  <li>創建特性分支 (git checkout -b feature/AmazingFeature)</li>
  <li>提交更改 (git commit -m 'Add some AmazingFeature')</li>
  <li>推送到分支 (git push origin feature/AmazingFeature)</li>
  <li>提交 Pull Request</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">📚 文檔貢獻</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>完善現有文檔內容</li>
  <li>補充使用示例和最佳實踐</li>
  <li>提供多語言翻譯</li>
  <li>修正文檔錯誤</li>
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

<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
<thead>
<tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
<th style="padding: 15px; text-align: left; font-weight: 600; border: 1px solid #e0e0e0;">貢獻者</th>
<th style="padding: 15px; text-align: left; font-weight: 600; border: 1px solid #e0e0e0;">貢獻內容</th>
</tr>
</thead>
<tbody>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 20%;">℡夏別</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">為推動EasyAIoT項目貢獻Windows部署文檔，為Windows平台用戶提供了完整的部署指南，大大降低了Windows環境下的部署難度，讓更多用戶能夠便捷地使用EasyAIoT平台。</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 20%;">YiYaYiYaho</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">為推動EasyAIoT項目貢獻Mac容器一鍵部署腳本，為Mac平台用戶提供了自動化部署解決方案，顯著簡化了Mac環境下的部署流程，提升了開發者和用戶的部署體驗。</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 20%;">山寒</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">為推動EasyAIoT項目貢獻Linux容器部署腳本，為Linux平台用戶提供了容器化部署方案，實現了快速、可靠的容器部署，為生產環境的穩定運行提供了重要保障。</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 20%;">玖零。</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">為推動EasyAIoT項目貢獻Linux容器部署腳本，進一步完善了Linux平台的容器化部署方案，為不同Linux發行版用戶提供了更多選擇，推動了項目的跨平台部署能力。</td>
</tr>
</tbody>
</table>

<p style="font-size: 14px; line-height: 1.8; color: #2c3e50; font-weight: 500; margin: 20px 0; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #3498db; border-radius: 4px;">
<strong>特別致謝</strong>：以上貢獻者的工作為EasyAIoT項目的跨平台部署能力奠定了堅實基礎，他們的專業精神和無私奉獻精神值得我們學習和尊敬。再次向這些傑出的貢獻者表示最誠摯的感謝！🙏
</p>

## 🙏 致謝

感謝以下各位對本項目包括但不限於代碼貢獻、問題反饋、資金捐贈等各種方式的支持！以下排名不分先後：
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/bcake" target="_blank"><img src=".image/sponsor/大餅.jpg" width="80px;" alt="大餅"/><br /><sub><b>大餅</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/jiang4yu" target="_blank"><img src=".image/sponsor/山寒.jpg" width="80px;" alt="山寒"/><br /><sub><b>山寒</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/baobaomo" target="_blank"><img src="./.image/sponsor/放學丶別走.jpg" width="80px;" alt="放學丶別走"/><br /><sub><b>放學丶別走</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/wagger" target="_blank"><img src="./.image/sponsor/春和.jpg" width="80px;" alt="春和"/><br /><sub><b>春和</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/longbinwu" target="_blank"><img src="./.image/sponsor/章魚小丸子.jpg" width="80px;" alt="章魚小丸子"/><br /><sub><b>章魚小丸子</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Catwings.jpg" width="80px;" alt="Catwings"/><br /><sub><b>Catwings</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/小工頭.jpg" width="80px;" alt="小工頭"/><br /><sub><b>小工頭</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/西鄉一粒沙.jpg" width="80px;" alt="西鄉一粒沙"/><br /><sub><b>西鄉一粒沙</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/L_Z_M" target="_blank"><img src=".image/sponsor/玖零。.jpg" width="80px;" alt="玖零。"/><br /><sub><b>玖零。</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/36436022" target="_blank"><img src=".image/sponsor/金鴻偉.jpg" width="80px;" alt="金鴻偉"/><br /><sub><b>金鴻偉</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/cnlijf" target="_blank"><img src="./.image/sponsor/李江峰.jpg" width="80px;" alt="李江峰"/><br /><sub><b>李江峰</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src=".image/sponsor/Best%20Yao.jpg" width="80px;" alt="Best Yao"/><br /><sub><b>Best Yao</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/weiloser" target="_blank"><img src=".image/sponsor/無為而治.jpg" width="80px;" alt="無為而治"/><br /><sub><b>無為而治</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/shup092_admin" target="_blank"><img src="./.image/sponsor/shup.jpg" width="80px;" alt="shup"/><br /><sub><b>shup</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/gampa" target="_blank"><img src="./.image/sponsor/也許.jpg" width="80px;" alt="也許"/><br /><sub><b>也許</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/leishaozhuanshudi" target="_blank"><img src="./.image/sponsor/⁰ʚᦔrꫀꪖꪑ⁰ɞ%20..jpg" width="80px;" alt="⁰ʚᦔrꫀꪖꪑ⁰ɞ ."/><br /><sub><b>⁰ʚᦔrꫀꪖꪑ⁰ɞ .</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/fateson" target="_blank"><img src="./.image/sponsor/逆.jpg" width="80px;" alt="逆"/><br /><sub><b>逆</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/dongGezzz_admin" target="_blank"><img src="./.image/sponsor/廖東旺.jpg" width="80px;" alt="廖東旺"/><br /><sub><b>廖東旺</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/huangzhen1993" target="_blank"><img src="./.image/sponsor/黃振.jpg" width="80px;" alt="黃振"/><br /><sub><b>黃振</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/fengchunshen" target="_blank"><img src="./.image/sponsor/春生.jpg" width="80px;" alt="春生"/><br /><sub><b>春生</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/mrfox_wang" target="_blank"><img src="./.image/sponsor/貴陽王老板.jpg" width="80px;" alt="貴陽王老板"/><br /><sub><b>貴陽王老板</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/haobaby" target="_blank"><img src="./.image/sponsor/hao_chen.jpg" width="80px;" alt="hao_chen"/><br /><sub><b>hao_chen</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/finalice" target="_blank"><img src="./.image/sponsor/盡千.jpg" width="80px;" alt="盡千"/><br /><sub><b>盡千</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/yuer629" target="_blank"><img src="./.image/sponsor/yuer629.jpg" width="80px;" alt="yuer629"/><br /><sub><b>yuer629</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/cai-peikai/ai-project" target="_blank"><img src="./.image/sponsor/kong.jpg" width="80px;" alt="kong"/><br /><sub><b>kong</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/HB1731276584" target="_blank"><img src="./.image/sponsor/歲月靜好.jpg" width="80px;" alt="歲月靜好"/><br /><sub><b>歲月靜好</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/hy5128" target="_blank"><img src="./.image/sponsor/Kunkka.jpg" width="80px;" alt="Kunkka"/><br /><sub><b>Kunkka</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/guo-dida" target="_blank"><img src="./.image/sponsor/灬.jpg" width="80px;" alt="灬"/><br /><sub><b>灬</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/XyhBill" target="_blank"><img src="./.image/sponsor/Mr.LuCkY.jpg" width="80px;" alt="Mr.LuCkY"/><br /><sub><b>Mr.LuCkY</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/timeforeverz" target="_blank"><img src="./.image/sponsor/泓.jpg" width="80px;" alt="泓"/><br /><sub><b>泓</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/mySia" target="_blank"><img src="./.image/sponsor/i.jpg" width="80px;" alt="i"/><br /><sub><b>i</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/依依.jpg" width="80px;" alt="依依"/><br /><sub><b>依依</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/sunbirder" target="_blank"><img src="./.image/sponsor/小菜鳥先飛.jpg" width="80px;" alt="小菜鳥先飛"/><br /><sub><b>小菜鳥先飛</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/mmy0" target="_blank"><img src="./.image/sponsor/追溯未來-_-.jpg" width="80px;" alt="追溯未來"/><br /><sub><b>追溯未來</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/ccqingshan" target="_blank"><img src="./.image/sponsor/青衫.jpg" width="80px;" alt="青衫"/><br /><sub><b>青衫</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/jiangchunJava" target="_blank"><img src="./.image/sponsor/Fae.jpg" width="80px;" alt="Fae"/><br /><sub><b>Fae</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/huang-xiangtai" target="_blank"><img src="./.image/sponsor/憨憨.jpg" width="80px;" alt="憨憨"/><br /><sub><b>憨憨</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/gu-beichen-starlight" target="_blank"><img src="./.image/sponsor/文藝小青年.jpg" width="80px;" alt="文藝小青年"/><br /><sub><b>文藝小青年</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/zhangnanchao" target="_blank"><img src="./.image/sponsor/lion.jpg" width="80px;" alt="lion"/><br /><sub><b>lion</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/yupccc" target="_blank"><img src="./.image/sponsor/汪汪隊立大功.jpg" width="80px;" alt="汪汪隊立大功"/><br /><sub><b>汪汪隊立大功</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/wcjjjjjjj" target="_blank"><img src="./.image/sponsor/wcj.jpg" width="80px;" alt="wcj"/><br /><sub><b>wcj</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/hufanglei" target="_blank"><img src="./.image/sponsor/🌹怒放de生命😋.jpg" width="80px;" alt="怒放de生命"/><br /><sub><b>怒放de生命</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/juyunsuan" target="_blank"><img src="./.image/sponsor/藍速傳媒.jpg" width="80px;" alt="藍速傳媒"/><br /><sub><b>藍速傳媒</b></sub></a></td>
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
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/nctwo" target="_blank"><img src=".image/sponsor/信微輸傳助手.jpg" width="80px;" alt="信微輸傳助手"/><br /><sub><b>信微輸傳助手</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/l9999_admin" target="_blank"><img src=".image/sponsor/一往無前.jpg" width="80px;" alt="一往無前"/><br /><sub><benen>一往無前</benen></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/stenin" target="_blank"><img src="./.image/sponsor/Charon.jpg" width="80px;" alt="Charon"/><br /><sub><b>Charon</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/zhao-yihuiwifi" target="_blank"><img src="./.image/sponsor/趙WIFI..jpg" width="80px;" alt="趙WIFI."/><br /><sub><b>趙WIFI.</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/Yang619" target="_blank"><img src="./.image/sponsor/Chao..jpg" width="80px;" alt="Chao."/><br /><sub><b>Chao.</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/lcrsd123" target="_blank"><img src=".image/sponsor/城市稻草人.jpg" width="80px;" alt="城市稻草人"/><br /><sub><b>城市稻草人</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/Mo_bai1016" target="_blank"><img src=".image/sponsor/Bug寫手墨白.jpg" width="80px;" alt="Bug寫手墨白"/><br /><sub><b>Bug寫手墨白</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/kevinosc_admin" target="_blank"><img src=".image/sponsor/kevin.jpg" width="80px;" alt="kevin"/><br /><sub><b>kevin</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/lhyicn" target="_blank"><img src=".image/sponsor/童年.jpg" width="80px;" alt="童年"/><br /><sub><b>童年</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/dubai100" target="_blank"><img src="./.image/sponsor/sherry金.jpg" width="80px;" alt="sherry金"/><br /><sub><b>sherry金</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/℡夏別.jpg" width="80px;" alt="℡夏別"/><br /><sub><b>℡夏別</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/翠翠草原.jpg" width="80px;" alt="翠翠草原"/><br /><sub><b>翠翠草原</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/慕容曦.jpg" width="80px;" alt="慕容曦"/><br /><sub><b>慕容曦</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Tyrion.jpg" width="80px;" alt="Tyrion"/><br /><sub><b>Tyrion</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/大漠孤煙.jpg" width="80px;" alt="大漠孤煙"/><br /><sub><b>大漠孤煙</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Return.jpg" width="80px;" alt="Return"/><br /><sub><b>Return</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/一杯拿鐵.jpg" width="80px;" alt="一杯拿鐵"/><br /><sub><b>一杯拿鐵</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Thuri.jpg" width="80px;" alt="Thuri"/><br /><sub><b>Thuri</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Liu.jpg" width="80px;" alt="Liu"/><br /><sub><b>Liu</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/三金.jpg" width="80px;" alt="三金"/><br /><sub><b>三金</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/ZPort.jpg" width="80px;" alt="ZPort"/><br /><sub><b>ZPort</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Li.jpg" width="80px;" alt="Li"/><br /><sub><b>Li</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/嘉樹.jpg" width="80px;" alt="嘉樹"/><br /><sub><b>嘉樹</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/俊采星馳.jpg" width="80px;" alt="俊采星馳"/><br /><sub><b>俊采星馳</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/oi.jpg" width="80px;" alt="oi"/><br /><sub><b>oi</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/ZhangY_000.jpg" width="80px;" alt="ZhangY_000"/><br /><sub><b>ZhangY_000</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/℡夏別.jpg" width="80px;" alt="℡夏別"/><br /><sub><b>℡夏別</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/張瑞麟.jpg" width="80px;" alt="張瑞麟"/><br /><sub><b>張瑞麟</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Lion King.jpg" width="80px;" alt="Lion King"/><br /><sub><b>Lion King</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Frank.jpg" width="80px;" alt="Frank"/><br /><sub><b>Frank</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/徐夢陽.jpg" width="80px;" alt="徐夢陽"/><br /><sub><b>徐夢陽</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/九月.jpg" width="80px;" alt="九月"/><br /><sub><b>九月</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/tangl偉.jpg" width="80px;" alt="tangl偉"/><br /><sub><b>tangl偉</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/馮瑞倫.jpg" width="80px;" alt="馮瑞倫"/><br /><sub><b>馮瑞倫</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/楊林.jpg" width="80px;" alt="楊林"/><br /><sub><b>楊林</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/梧桐有語。.jpg" width="80px;" alt="梧桐有語。"/><br /><sub><b>梧桐有語。</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/歌德de花燭.jpg" width="80px;" alt="歌德de花燭"/><br /><sub><b>歌德de花燭</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/泥嚎.jpg" width="80px;" alt="泥嚎"/><br /><sub><b>泥嚎</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/翠翠草原.jpg" width="80px;" alt="翠翠草原"/><br /><sub><b>翠翠草原</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/胡澤龍.jpg" width="80px;" alt="胡澤龍"/><br /><sub><b>胡澤龍</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/蘇葉.jpg" width="80px;" alt="蘇葉"/><br /><sub><b>蘇葉</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/裴先生.jpg" width="80px;" alt="裴先生"/><br /><sub><b>裴先生</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/譚遠彪.jpg" width="80px;" alt="譚遠彪"/><br /><sub><b>譚遠彪</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/陳祺.jpg" width="80px;" alt="陳祺"/><br /><sub><b>陳祺</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/零點就睡.jpg" width="80px;" alt="零點就睡"/><br /><sub><b>零點就睡</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/風之羽.jpg" width="80px;" alt="風之羽"/><br /><sub><b>風之羽</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/fufeng1908" target="_blank"><img src="./.image/sponsor/王守仁.jpg" width="80px;" alt="王守仁"/><br /><sub><b>王守仁</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/kaigejava" target="_blank"><img src="./.image/sponsor/狼ྂ圖ྂ騰ྂ.jpg" width="80px;" alt="狼圖騰"/><br /><sub><b>狼圖騰</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/馬到成功.jpg" width="80px;" alt="馬到成功"/><br /><sub><b>馬到成功</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/做生活的高手.jpg" width="80px;" alt="做生活的高手"/><br /><sub><b>做生活的高手</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/清歡之戀.jpg" width="80px;" alt="清歡之戀"/><br /><sub><b>清歡之戀</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/絕域時空.jpg" width="80px;" alt="絕域時空"/><br /><sub><b>絕域時空</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/風雨.jpg" width="80px;" alt="風雨"/><br /><sub><b>風雨</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Nicola.jpg" width="80px;" alt="Nicola"/><br /><sub><b>Nicola</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/雲住.jpg" width="80px;" alt="雲住"/><br /><sub><b>雲住</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Mr.Zhang.jpg" width="80px;" alt="Mr.Zhang"/><br /><sub><b>Mr.Zhang</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/劍.jpg" width="80px;" alt="劍"/><br /><sub><b>劍</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/shen.jpg" width="80px;" alt="shen"/><br /><sub><b>shen</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/嗯.jpg" width="80px;" alt="嗯"/><br /><sub><b>嗯</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/周華.jpg" width="80px;" alt="周華"/><br /><sub><b>周華</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/太陽鳥.jpg" width="80px;" alt="太陽鳥"/><br /><sub><b>太陽鳥</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/了了.jpg" width="80px;" alt="了了"/><br /><sub><b>了了</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/第七次日落.jpg" width="80px;" alt="第七次日落"/><br /><sub><b>第七次日落</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/npc.jpg" width="80px;" alt="npc"/><br /><sub><b>npc</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/承擔不一樣的天空.jpg" width="80px;" alt="承擔不一樣的天空"/><br /><sub><b>承擔不一樣的天空</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/鐵木.jpg" width="80px;" alt="鐵木"/><br /><sub><b>鐵木</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Orion.jpg" width="80px;" alt="Orion"/><br /><sub><b>Orion</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/森源-金福洪.jpg" width="80px;" alt="森源-金福洪"/><br /><sub><b>森源-金福洪</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/薛繼超.jpg" width="80px;" alt="薛繼超"/><br /><sub><b>薛繼超</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/虎虎虎.jpg" width="80px;" alt="虎虎虎"/><br /><sub><b>虎虎虎</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Everyman.jpg" width="80px;" alt="Everyman"/><br /><sub><b>Everyman</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/NXL.jpg" width="80px;" alt="NXL"/><br /><sub><b>NXL</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/孫濤.jpg" width="80px;" alt="孫濤"/><br /><sub><b>孫濤</b></sub></a></td>
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

## 💡 期望

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
歡迎提出更好的意見，幫助完善 easyaiot
</p>

## 📄 版權

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
翺翔的雄庫魯/easyaiot 采用 <a href="https://gitee.com/soaring-xiongkulu/easyaiot/blob/main/LICENSE" style="color: #3498db; text-decoration: none; font-weight: 600;">APACHE LICENSE 2.0</a> 開源協議，您在使用過程中，需要註意以下幾點：
</p>

<ol style="font-size: 14px; line-height: 1.8; color: #444; margin: 15px 0; padding-left: 25px;">
  <li>不得修改產品相關代碼的源碼頭註釋和出處；</li>
  <li>不得應用於危害國家安全、榮譽和利益的行為，不能以任何形式用於非法目的；</li>
</ol>

## 🌟 Star增長趨勢圖

[![Stargazers over time](https://starchart.cc/soaring-xiongkulu/easyaiot.svg?variant=adaptive)](https://starchart.cc/soaring-xiongkulu/easyaiot)
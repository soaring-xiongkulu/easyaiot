# EasyAIoT (클라우드-엣지-디바이스 통합 지능형 알고리즘 응용 플랫폼)

[![Gitee star](https://gitee.com/volara/easyaiot/badge/star.svg?theme=gvp)](https://gitee.com/soaring-xiongkulu/easyaiot/stargazers)
[![Gitee fork](https://gitee.com/volara/easyaiot/badge/fork.svg?theme=gvp)](https://gitee.com/soaring-xiongkulu/easyaiot/members)

<p style="font-size: 16px; line-height: 1.8; color: #555; font-weight: 400; margin: 20px 0;">
전 세계 사람들이 이 시스템을 사용하여 AI의 진정한 무장벽화를 실현하고, AI가 가져다주는 혜택을 누리길 바랍니다. 이는 소수의 사람들만이 접근할 수 있는 것이 아닙니다.
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

## 🌟 프로젝트에 대한 몇 가지 생각

### 📍 프로젝트 포지셔닝

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT는 AI와 IoT의 심층적 융합에 초점을 맞춘 클라우드-엣지-디바이스 통합 지능형 사물인터넷 플랫폼입니다. 플랫폼은 알고리즘 태스크 관리, 실시간 스트림 분석, 모델 서비스 클러스터 추론 등의 핵심 기능을 통해, 디바이스 접속부터 데이터 수집, AI 분석, 지능형 의사결정에 이르는 전 과정의 폐쇄 루프를 실현하여 진정한 만물 인터넷화, 만물 지능화 제어를 실현합니다.
</p>

#### 🧠 AI 기능

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>카메라 실시간 영상 AI 분석</strong>: 카메라 실시간 영상의 AI 지능형 분석을 지원하며, 실시간 비디오 스트림에 대해 객체 감지, 행동 분석, 이상 식별 등의 AI 알고리즘 처리를 수행할 수 있습니다. 밀리초 단위 응답의 실시간 분석 결과를 제공하며, 다중 비디오 병렬 분석을 지원합니다.</li>
  <li><strong>클라우드-엣지-디바이스 통합 알고리즘 경보 모니터링 대시보드</strong>: 통일된 클라우드-엣지-디바이스 통합 알고리즘 경보 모니터링 대시보드를 제공하며, 디바이스 상태, 알고리즘 태스크 실행 상황, 경보 이벤트 통계, 비디오 스트림 분석 결과 등 주요 정보를 실시간으로 표시합니다. 다차원 데이터 시각화 표시를 지원하여 클라우드, 엣지, 디바이스 측의 통합 모니터링 및 관리를 실현하며, 의사결정자에게 전역적 관점의 지능형 모니터링 지휘 센터를 제공합니다.</li>
  <li><strong>디바이스 감지 영역 그리기</strong>: 시각적 디바이스 감지 영역 그리기 도구를 제공하며, 디바이스 스냅샷 이미지에서 사각형 및 다각형 감지 영역 그리기를 지원합니다. 영역과 알고리즘 모델 간의 유연한 연관 구성 설정을 지원하며, 영역의 시각적 관리, 편집, 삭제 등의 작업을 지원합니다. 그리기 효율성을 높이기 위한 키보드 단축키를 지원하며, 정밀한 영역 감지 구성을 실현하고 알고리즘 태스크에 대한 정확한 감지 범위 정의를 제공합니다.</li>
  <li><strong>지능형 연동 경보 메커니즘</strong>: 감지 영역, 방어 시간대 및 이벤트 경보 간의 삼중 연동 메커니즘을 지원합니다. 시스템은 감지된 이벤트가 지정된 감지 영역 범위를 동시에 충족하고, 방어 시간대 내에 있으며 경보 이벤트 유형과 일치하는지 지능적으로 판단합니다. 세 가지 조건이 모두 충족될 때만 경보가 트리거되어 정밀한 시공간 조건 필터링을 실현하고, 오탐률을 크게 낮추며 경보 시스템의 정확성과 실용성을 향상시킵니다.</li>
  <li><strong>대규모 카메라 관리</strong>: 수백 대 규모의 카메라 접속을 지원하며, 수집, 라벨링, 학습, 추론, 내보내기, 분석, 경보, 녹화, 저장, 배포 등의 전 과정 서비스를 제공합니다.</li>
  <li><strong>알고리즘 태스크 관리</strong>: 두 가지 유형의 알고리즘 태스크 생성 및 관리를 지원하며, 각 알고리즘 태스크는 프레임 추출기(Frame Extractor)와 정렬기(Sorter)를 유연하게 바인딩하여 정밀한 비디오 프레임 추출 및 결과 정렬을 실현합니다.
    <ul style="margin: 5px 0; padding-left: 20px;">
      <li><strong>실시간 알고리즘 태스크</strong>: 실시간 영상 분석에 사용되며, RTSP/RTMP 스트림 실시간 처리를 지원하고 밀리초 단위 응답 능력을 제공하여 모니터링, 보안 등의 실시간 시나리오에 적합합니다.</li>
      <li><strong>캡처 알고리즘 태스크</strong>: 캡처 이미지 분석에 사용되며, 캡처 이미지에 대한 지능형 식별 및 분석을 수행하여 이벤트 복원, 이미지 검색 등의 시나리오에 적합합니다.</li>
    </ul>
  </li>
  <li><strong>스트림 전달</strong>: AI 분석 기능을 활성화하지 않고도 카메라 실시간 영상을 직접 시청할 수 있습니다. 스트림 전달 작업을 생성하여 여러 카메라를 일괄 전달할 수 있으며, 여러 비디오 스트림의 동기화된 시청을 실현하여 순수 비디오 모니터링 시나리오 요구사항을 충족합니다.</li>
  <li><strong>모델 서비스 클러스터 추론</strong>: 분산형 모델 추론 서비스 클러스터를 지원하여 지능형 부하 분산, 장애 자동 전환 및 고가용성 보장을 실현하며, 추론 처리량과 시스템 안정성을 크게 향상시킵니다.</li>
  <li><strong>방어 시간대 관리</strong>: 완전 방어 모드(All-defense)와 반방어 모드(Semi-defense) 두 가지 방어 전략을 지원하며, 다른 시간대의 방어 규칙을 유연하게 구성하여 정밀한 시간대별 지능형 모니터링 및 경보를 실현합니다.</li>
  <li><strong>OCR 및 음성 인식</strong>: PaddleOCR 기반의 고정밀 문자 인식을 구현하며, 음성-텍스트 변환 기능을 지원하고 다중 언어 인식 능력을 제공합니다.</li>
  <li><strong>다중 모달 비전 대형 모델</strong>: 객체 인식, 문자 인식 등 다양한 비전(Vision) 태스크를 지원하며, 강력한 이미지 이해 및 장면 분석 능력을 제공합니다.</li>
  <li><strong>LLM 대형 언어 모델</strong>: RTSP 스트림, 비디오, 이미지, 음성, 텍스트 등 다양한 입력 형식의 지능형 분석 및 이해를 지원하여 다중 모달 콘텐츠 이해를 실현합니다.</li>
  <li><strong>모델 배포 및 버전 관리</strong>: AI 모델의 빠른 배포 및 버전 관리를 지원하여 모델 원클릭 배포, 버전 롤백 및 카나리아 배포를 실현합니다.</li>
  <li><strong>다중 인스턴스 관리</strong>: 여러 모델 인스턴스의 동시 실행 및 리소스 스케줄링을 지원하여 시스템 활용도와 리소스 이용 효율성을 향상시킵니다.</li>
  <li><strong>카메라 캡처</strong>: 카메라 실시간 캡처 기능을 지원하며, 캡처 규칙 및 트리거 조건을 구성하여 지능형 캡처 및 이벤트 기록을 실현합니다.</li>
  <li><strong>캡처 공간 관리</strong>: 캡처 이미지의 저장 공간 관리를 제공하며, 공간 할당량 및 정리 정책을 지원하여 저장 리소스의 합리적 이용을 보장합니다.</li>
  <li><strong>녹화 공간 관리</strong>: 녹화 파일의 저장 공간 관리를 제공하며, 자동 정리 및 아카이빙을 지원하여 저장 리소스의 지능형 관리를 실현합니다.</li>
  <li><strong>캡처 이미지 관리</strong>: 캡처 이미지의 조회, 검색, 다운로드, 삭제 등의 전 생명주기 관리를 지원하여 편리한 이미지 관리 기능을 제공합니다.</li>
  <li><strong>디바이스 디렉토리 관리</strong>: 디바이스 트리 구조 디렉토리 관리를 제공하며, 디바이스 그룹화, 계층 관리 및 권한 제어를 지원하여 디바이스의 체계적 조직화 및 세밀한 관리를 실현합니다.</li>
  <li><strong>경보 녹화</strong>: 경보 이벤트 자동 트리거 녹화 기능을 지원합니다. 이상 이벤트가 감지되면 관련 비디오 클립을 자동으로 녹화하여 완전한 경보 증거 체인을 제공하며, 경보 녹화의 조회, 다운로드 및 관리를 지원합니다.</li>
  <li><strong>경보 이벤트</strong>: 완전한 경보 이벤트 관리 기능을 제공하며, 경보 이벤트의 실시간 푸시, 기록 조회, 통계 분석, 이벤트 처리 및 상태 추적을 지원하여 경보 전 생명주기 관리를 실현합니다.</li>
  <li><strong>녹화 재생</strong>: 기록 녹화의 빠른 검색 및 재생 기능을 지원하며, 타임라인 위치 지정, 배속 재생, 키 프레임 점프 등 편리한 조작을 제공합니다. 다중 비디오 동기 재생을 지원하여 이벤트 복원 및 분석 요구를 충족시킵니다.</li>
</ul>

#### 🌐 IoT 기능

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>디바이스 접속 및 관리</strong>: 디바이스 등록, 인증, 상태 모니터링, 생명주기 관리</li>
  <li><strong>제품 및 사물 모델(Thing Model) 관리</strong>: 제품 정의, 사물 모델 구성, 제품 관리</li>
  <li><strong>다중 프로토콜 지원</strong>: MQTT, TCP, HTTP 등 다양한 IoT 프로토콜</li>
  <li><strong>디바이스 인증 및 동적 등록</strong>: 안전한 접속, 신원 인증, 동적 디바이스 등록</li>
  <li><strong>규칙 엔진</strong>: 데이터 흐름 규칙, 메시지 라우팅, 데이터 변환</li>
  <li><strong>데이터 수집 및 저장</strong>: 디바이스 데이터 수집, 저장, 조회 및 분석</li>
  <li><strong>디바이스 상태 모니터링 및 경보 관리</strong>: 실시간 모니터링, 이상 경보, 지능형 의사결정</li>
  <li><strong>알림 관리</strong>: Feishu, DingTalk, Enterprise WeChat, Email, Tencent Cloud SMS, Alibaba Cloud SMS, Webhook 등 7가지 알림 방식을 지원하여 유연한 다채널 경보 알림을 구현합니다.</li>
</ul>

### 💡 기술 철학

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
우리는 어떤 프로그래밍 언어도 모든 것을 잘할 수는 없다고 생각합니다. 그러나 세 가지 프로그래밍 언어의 심층적인 융합을 통해 EasyAIoT는 각 언어의 장점을 발휘하여 강력한 기술 생태계를 구축합니다.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Java는 안정적이고 신뢰할 수 있는 플랫폼 아키텍처 구축에 능숙하지만 네트워크 프로그래밍과 AI 프로그래밍에는 적합하지 않습니다. Python은 네트워크 프로그래밍과 AI 알고리즘 개발에 능숙하지만 고성능 태스크 실행에는 병목 현상이 있습니다. C++는 고성능 태스크 실행에 능숙하지만 플랫폼 개발과 AI 프로그래밍에서는 앞의 두 언어에 미치지 못합니다. EasyAIoT는 세 언어 혼합 아키텍처를 채택하여 각 언어의 장점을 최대한 발휘하고, 구현은 상당히 도전적이지만 사용은 매우 편리한 AIoT 플랫폼을 구축합니다.
</p>

![EasyAIoT 플랫폼 아키텍처.jpg](.image/iframe2.jpg)

### 🔄 모듈 데이터 흐름

<img src=".image/iframe3.jpg" alt="EasyAIoT 플랫폼 아키텍처" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

### 🤖 제로샷 라벨링 기술

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
대형 모델을 기반으로 제로샷 라벨링 기술 시스템을 혁신적으로 구축합니다 (이상적으로는 인공 라벨링 단계를 완전히 제거하여 라벨링 프로세스의 자동화를 실현). 이 기술은 대형 모델을 통해 초기 데이터를 생성하고 프롬프트 기술을 통해 자동 라벨링을 완료한 후, 인-기 협업 검증(옵션)을 통해 데이터 품질을 보장합니다. 그런 다음 초기 소형 모델을 학습시킵니다. 이 소형 모델은 지속적인 반복과 자기 최적화를 통해 라벨링 효율성과 모델 정밀도의 협력적 진화를 실현하며, 궁극적으로 시스템 성능의 지속적인 향상을 촉진합니다.
</p>

<img src=".image/iframe4.jpg" alt="EasyAIoT 플랫폼 아키텍처" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

### 🏗️ 프로젝트 아키텍처 특징

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
EasyAIoT는 사실 하나의 프로젝트가 아닌, 다섯 개의 프로젝트입니다.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
이점은 무엇일까요? 만약 제한된 디바이스(예: RK3588)에서 작업한다면, 그 중 특정 프로젝트만 꺼내어 독립적으로 배포할 수 있습니다. 따라서 이 프로젝트는 클라우드 플랫폼처럼 보이지만, 사실상 엣지 플랫폼이 될 수도 있습니다.
</p>

<div style="margin: 30px 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;">

<p style="font-size: 16px; line-height: 1.8; margin: 0; font-weight: 500;">
🌟 진정한 오픈소스는 쉽지 않습니다. 이 프로젝트가 도움이 되셨다면, 떠나시기 전에 별(Star) 하나를 눌러 주세요. 이는 저에게 가장 큰 지지가 될 것입니다!<br>
<small style="font-size: 14px; opacity: 0.9;">(가짜 오픈소스가 횡행하는 이 시대에, 이 프로젝트는 한 이질적인 존재로, 순전히 열정으로 전기를 생산합니다)</small>
</p>

</div>

### 🌍 현지화 지원

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT는 현지화 전략에 적극적으로 대응하며, 현지화 하드웨어와 운영체제를 전면적으로 지원하여 사용자에게 안전하고 제어 가능한 AIoT 솔루션을 제공합니다:
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🖥️ 서버 측 지원</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>하이곤(Hygon) x86 아키텍처 프로세서와 완벽하게 호환됩니다.</li>
  <li>현지화 서버 하드웨어 플랫폼을 지원합니다.</li>
  <li>대상 성능 최적화 솔루션을 제공합니다.</li>
  <li>기업급 응용의 안정적인 운영을 보장합니다.</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">📱 엣지 측 지원</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>록칩(Rockchip) ARM 아키텍처 칩을 전면적으로 지원합니다.</li>
  <li>RK3588 등 주류 엣지 컴퓨팅 플랫폼에 완벽하게 적합합니다.</li>
  <li>엣지 시나리오에 대한 심층 최적화를 수행했습니다.</li>
  <li>엣지 지능의 경량화 배포를 실현합니다.</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🖱️ 운영체제 지원</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>기린(Kylin) 운영체제와 호환됩니다.</li>
  <li>팡더(Founder) 등 현지화 Linux 배포판을 지원합니다.</li>
  <li>통신 UOS 등 주류 현지화 운영체제에 적합합니다.</li>
  <li>완전한 현지화 배포 솔루션을 제공합니다.</li>
</ul>
</div>

</div>

## 🎯 적용 시나리오

<img src=".image/适用场景.png" alt="적용 시나리오" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

## 🧩 프로젝트 구조

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT는 다섯 개의 핵심 프로젝트로 구성됩니다:
</p>

<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50; width: 20%;">모듈</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50;">설명</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>WEB 모듈</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">Vue 기반의 프론트엔드 관리 인터페이스로, 통일된 사용자 상호작용 경험을 제공합니다.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>DEVICE 모듈</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>기술적 장점</strong>: JDK21 기반으로 더 나은 성능과 현대적 특성을 제공합니다.</li>
    <li><strong>디바이스 관리</strong>: 디바이스 등록, 인증, 상태 모니터링, 생명주기 관리</li>
    <li><strong>제품 관리</strong>: 제품 정의, 사물 모델 관리, 제품 구성</li>
    <li><strong>프로토콜 지원</strong>: MQTT, TCP, HTTP 등 다양한 IoT 프로토콜</li>
    <li><strong>디바이스 인증</strong>: 디바이스 동적 등록, 신원 인증, 안전한 접속</li>
    <li><strong>규칙 엔진</strong>: 데이터 흐름 규칙, 메시지 라우팅, 데이터 변환</li>
    <li><strong>데이터 수집</strong>: 디바이스 데이터 수집, 저장, 조회 및 분석</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>VIDEO 모듈</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>스트리밍 미디어 처리</strong>: RTSP/RTMP 스트림 실시간 처리 및 전송 지원</li>
    <li><strong>알고리즘 태스크 관리</strong>: 실시간 알고리즘 태스크와 캡처 알고리즘 태스크 두 가지 유형을 지원하며, 각각 실시간 영상 분석과 캡처 이미지 분석에 사용됩니다.</li>
    <li><strong>프레임 추출기 및 정렬기</strong>: 유연한 프레임 추출 전략과 결과 정렬 메커니즘을 지원하며, 각 알고리즘 태스크는 독립적인 프레임 추출기와 정렬기에 바인딩할 수 있습니다.</li>
    <li><strong>방어 시간대</strong>: 완전 방어 모드와 반방어 모드의 시간대별 구성 지원</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>AI 모듈</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>지능형 분석</strong>: 비디오 분석 및 AI 알고리즘 실행을 담당합니다.</li>
    <li><strong>모델 서비스 클러스터</strong>: 분산형 모델 추론 서비스를 지원하여 부하 분산 및 고가용성을 실현합니다.</li>
    <li><strong>실시간 추론</strong>: 밀리초 단위 응답의 실시간 지능형 분석 능력을 제공합니다.</li>
    <li><strong>모델 관리</strong>: 모델 배포, 버전 관리 및 다중 인스턴스 스케줄링을 지원합니다.</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>TASK 모듈</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">C++ 기반의 고성능 태스크 처리 모듈로, 계산 집약적 태스크 실행을 담당합니다.</td>
</tr>
</table>

## 🖥️ 크로스 플랫폼 배포 장점

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT는 Linux, Mac, Windows 세 가지 주류 운영체제에서의 배포를 지원하여 다양한 환경의 사용자에게 유연하고 편리한 배포 솔루션을 제공합니다:
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🐧 Linux 배포 장점</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>프로덕션 환경에 적합하며, 안정적이고 신뢰할 수 있으며 리소스 점유율이 낮습니다.</li>
  <li>Docker 컨테이너화 배포를 지원하여 모든 서비스를 원클릭으로 시작할 수 있습니다.</li>
  <li>서버, 엣지 컴퓨팅 디바이스 (예: RK3588 등 ARM 아키텍처 디바이스)에 완벽하게 적합합니다.</li>
  <li>완전한 자동화 설치 스크립트를 제공하여 배포 프로세스를 단순화합니다.</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🍎 Mac 배포 장점</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>개발 및 테스트 환경에 적합하며, macOS 시스템과 깊이 통합됩니다.</li>
  <li>로컬 개발 및 디버깅을 지원하여 기능을 빠르게 검증할 수 있습니다.</li>
  <li>편리한 설치 스크립트를 제공하며, Homebrew 등의 패키지 관리자를 지원합니다.</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🪟 Windows 배포 장점</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Windows 서버 환경에 적합하여 학습 비용을 낮춥니다.</li>
  <li>PowerShell 자동화 스크립트를 지원하여 배포 작업을 단순화합니다.</li>
  <li>Windows Server 및 데스크톱 Windows 시스템과 호환됩니다.</li>
  <li>그래픽 설치 마법사를 제공하여 사용자 친화적입니다.</li>
</ul>
</div>

</div>


<p style="font-size: 14px; line-height: 1.8; color: #2c3e50; font-weight: 500; margin: 20px 0; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #3498db; border-radius: 4px;">
<strong>통일된 경험</strong>: 어떤 운영체제를 선택하든 EasyAIoT는 일관된 설치 스크립트와 배포 문서를 제공하여 크로스 플랫폼 배포 경험의 일관성을 보장합니다.
</p>

## ☁️ EasyAIoT = AI + IoT = 클라우드-엣지-디바이스 통합 솔루션

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
수천 가지 수직 시나리오를 지원하며, AI 모델 맞춤화 및 AI 알고리즘 맞춤형 개발을 지원하고, 심층적으로 융합됩니다.
</p>

<div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3498db;">
<h3 style="color: #2c3e50; margin-top: 0;">만물 지능형 시각화를 위한 역량 부여: EasyAIoT</h3>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
IoT 디바이스(특히 대량의 카메라)의 효율적인 접속 및 제어 네트워크를 구축했습니다. 우리는 스트리밍 미디어 실시간 전송 기술과 최첨단 인공지능(AI)을 심층적으로 융합하여 통합 서비스 핵심을 구축했습니다. 이 솔루션은 이기종 디바이스의 상호 연결 및 통신을 뚫을 뿐만 아니라 고화질 비디오 스트림과 강력한 AI 해석 엔진을 심층적으로 통합하여 모니터링 시스템에 "지능형 눈"을 부여합니다. 이는 얼굴 인식, 이상 행동 분석, 위험 인원 배치 및 주변 침입 감지를 정확하게 실현합니다.
</p>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
플랫폼은 두 가지 유형의 알고리즘 태스크를 지원합니다: 실시간 알고리즘 태스크는 RTSP/RTMP 스트림의 실시간 영상 분석에 사용되어 밀리초 단위 응답 능력을 제공하며, 캡처 알고리즘 태스크는 캡처 이미지의 지능형 분석에 사용되어 이벤트 복원 및 이미지 검색을 지원합니다. 알고리즘 태스크 관리를 통해 유연한 프레임 추출 및 정렬 전략을 실현하며, 각 태스크는 독립적인 프레임 추출기와 정렬기에 바인딩할 수 있습니다. 모델 서비스 클러스터 추론 능력과 결합하여 밀리초 단위 응답과 고가용성 보장을 확실히 합니다. 동시에 완전 방어 모드와 반방어 모드 두 가지 방어 전략을 제공하여 다른 시간대에 따라 모니터링 규칙을 유연하게 구성할 수 있으며, 정밀한 시간대별 지능형 모니터링 및 경보를 실현합니다.
</p>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
IoT 디바이스 관리 측면에서 EasyAIoT는 완전한 디바이스 생명주기 관리 능력을 제공하며, 다양한 IoT 프로토콜(MQTT, TCP, HTTP)을 지원하여 디바이스의 빠른 접속, 안전 인증, 실시간 모니터링 및 지능형 제어를 실현합니다. 규칙 엔진을 통해 디바이스 데이터의 지능형 흐름 및 처리를 실현하며, AI 기능과 결합하여 디바이스 데이터를 심층 분석합니다. 이는 디바이스 접속, 데이터 수집, 지능형 분석에서 의사결정 실행에 이르는 전 과정 자동화를 실현하여 진정한 만물 인터넷화, 만물 지능화 제어를 실현합니다.
</p>
</div>

<img src=".image/iframe1.jpg" alt="EasyAIoT 플랫폼 아키텍처" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">

## ⚠️ 책임 한계

EasyAIoT는 오픈소스 학습 프로젝트이며 상업적 행위와 무관합니다. 사용자는 이 프로젝트를 사용할 때 법률 및 규정을 준수해야 하며 불법 활동을 해서는 안 됩니다. 만약 EasyAIoT가 사용자의 불법 행위를 발견하면 관련 기관의 조사에 협력하고 정부 부서에 신고할 것입니다. 사용자의 불법 행위로 인한 모든 법적 책임은 사용자가 스스로 부담하며, 사용자의 사용으로 인해 제3자에게 손해가 발생한 경우 사용자는 법에 따라 배상해야 합니다. EasyAIoT의 모든 관련 리소스 사용은 사용자가 스스로 위험을 부담합니다.

## 📚 배포 문서

- [플랫폼 배포 문서](.doc/部署文档/平台部署文档_ko.md)

## 🎮 데모 환경

- 데모 주소: http://36.111.47.113:8888/
- 계정: admin
- 비밀번호: admin123

## ⚙️ 프로젝트 주소

- Gitee: https://gitee.com/soaring-xiongkulu/easyaiot
- Github: https://github.com/soaring-xiongkulu/easyaiot

## 📸 스크린샷
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
  <img src=".image/banner/banner1083.jpg" alt="Screenshot 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1084.jpg" alt="Screenshot 7" width="49%">
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

## 🛠️ 서비스 지원

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT 플랫폼과 코드를 깊이 이해하실 수 있도록 다양한 서비스 방식을 제공해 드립니다. 제품 문서, 기술 교류 그룹, 유료 교육 등을 통해 다음과 같은 서비스를 받으실 수 있습니다:
</p>

<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
<thead>
<tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
<th style="padding: 15px; text-align: left; font-weight: 600;">서비스 항목</th>
<th style="padding: 15px; text-align: left; font-weight: 600;">서비스 내용</th>
<th style="padding: 15px; text-align: center; font-weight: 600;">서비스 비용</th>
<th style="padding: 15px; text-align: left; font-weight: 600;">서비스 방식</th>
</tr>
</thead>
<tbody>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50;">시스템 배포</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">고객이 지정한 네트워크 및 하드웨어 환경에서 EasyAIoT 배포 완료</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; text-align: center; color: #e74c3c; font-weight: 600;">500위안</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">온라인 배포 지원</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50;">기술 지원</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">다양한 배포, 기능 사용 중 발생한 문제에 대한 답변 제공</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; text-align: center; color: #e74c3c; font-weight: 600;">200위안</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">30분 이내 온라인 원격 지원</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50;">기타 서비스</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">수직 영역 솔루션 맞춤형 개발; 맞춤형 기간, 기능 서비스 등</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; text-align: center; color: #e74c3c; font-weight: 600;">협의</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">협의</td>
</tr>
</tbody>
</table>

## 📞 연락처 (위챗(WeChat) 추가 후, 공식 계정을 팔로우하고 기술 교류 그룹에 초대해 드립니다)

<div>
  <img src=".image/联系方式.jpg" alt="연락처" width="30%" style="margin-right: 50px;">
  <img src=".image/联系方式2.png" alt="연락처" width="30%">
</div>

## 👥 공식 계정

<div>
  <img src=".image/公众号.jpg" alt="공식 계정" width="30%">
</div>

## 🪐 지식 스타 (Knowledge Planet):

<p>
  <img src=".image/知识星球.jpg" alt="지식 스타" width="30%">
</p>

## 💰 후원하기

<div>
    <img src=".image/微信支付.jpg" alt="위챗페이" width="30%" height="30%">
    <img src=".image/支付宝支付.jpg" alt="알리페이" width="30%" height="10%">
</div>

## 🤝 기여 가이드

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
우리는 모든 형태의 기여를 환영합니다! 코드 개발자, 문서 작성자, 문제 보고자이든 상관없이 여러분의 기여가 EasyAIoT를 더 좋게 만드는 데 도움이 될 것입니다. 다음은 주요 기여 방법입니다:
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">💻 코드 기여</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>프로젝트를 GitHub/Gitee 계정으로 Fork</li>
  <li>기능 브랜치 생성 (git checkout -b feature/AmazingFeature)</li>
  <li>변경사항 커밋 (git commit -m 'Add some AmazingFeature')</li>
  <li>브랜치에 푸시 (git push origin feature/AmazingFeature)</li>
  <li>Pull Request 제출</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">📚 문서 기여</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>기존 문서 내용 개선</li>
  <li>사용 예제 및 모범 사례 추가</li>
  <li>다국어 번역 제공</li>
  <li>문서 오류 수정</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🌟 기타 기여 방법</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>버그 보고 및 수정</li>
  <li>기능 개선 제안</li>
  <li>커뮤니티 토론 참여 및 다른 개발자 도움</li>
  <li>사용 경험 및 사례 공유</li>
</ul>
</div>

</div>

## 🌟 주요 기여자

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
다음은 EasyAIoT 프로젝트에 중요한 기여를 한 탁월한 기여자들입니다. 그들의 기여는 프로젝트 개발을 촉진하는 데 핵심적인 역할을 했습니다. 진심으로 감사드립니다!
</p>

<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
<thead>
<tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
<th style="padding: 15px; text-align: left; font-weight: 600; border: 1px solid #e0e0e0;">기여자</th>
<th style="padding: 15px; text-align: left; font-weight: 600; border: 1px solid #e0e0e0;">기여 내용</th>
</tr>
</thead>
<tbody>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 20%;">℡夏别</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">EasyAIoT 프로젝트를 위해 Windows 배포 문서를 기여하여 Windows 플랫폼 사용자에게 완전한 배포 가이드를 제공하고, Windows 환경에서의 배포 난이도를 크게 낮춰 더 많은 사용자가 EasyAIoT 플랫폼을 편리하게 사용할 수 있도록 했습니다.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 20%;">YiYaYiYaho</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">EasyAIoT 프로젝트를 위해 Mac 컨테이너 원클릭 배포 스크립트를 기여하여 Mac 플랫폼 사용자에게 자동화된 배포 솔루션을 제공하고, Mac 환경에서의 배포 프로세스를 크게 단순화하여 개발자와 사용자의 배포 경험을 향상시켰습니다.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 20%;">山寒</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">EasyAIoT 프로젝트를 위해 Linux 컨테이너 배포 스크립트를 기여하여 Linux 플랫폼 사용자에게 컨테이너화된 배포 솔루션을 제공하고, 빠르고 안정적인 컨테이너 배포를 실현하여 프로덕션 환경의 안정적인 운영을 위한 중요한 보장을 제공했습니다.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 20%;">玖零。</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">EasyAIoT 프로젝트를 위해 Linux 컨테이너 배포 스크립트를 기여하여 Linux 플랫폼의 컨테이너화된 배포 솔루션을 더욱 개선하고, 다양한 Linux 배포판 사용자에게 더 많은 선택권을 제공하며, 프로젝트의 크로스 플랫폼 배포 능력을 촉진했습니다.</td>
</tr>
</tbody>
</table>

<p style="font-size: 14px; line-height: 1.8; color: #2c3e50; font-weight: 500; margin: 20px 0; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #3498db; border-radius: 4px;">
<strong>특별 감사</strong>: 위 기여자들의 작업은 EasyAIoT 프로젝트의 크로스 플랫폼 배포 능력에 견고한 기반을 마련했습니다. 그들의 전문성과 무사심한 헌신은 우리가 배우고 존경할 가치가 있습니다. 다시 한 번 이 탁월한 기여자들에게 진심으로 감사드립니다! 🙏
</p>

## 🙏 감사의 말

다음 분들께 코드 기여, 문제 피드백, 자금 기부 등 다양한 방식으로 이 프로젝트를 지원해 주셔서 감사드립니다! 아래 순서는 무작위입니다:
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
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/l9999_admin" target="_blank"><img src=".image/sponsor/一往无前.jpg" width="80px;" alt="一往无前"/><br /><benen>一往无前</benen></sub></a></td>
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

## 💡 기대

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
좋은 의견을 제안하여 easyaiot을 완성하는 데 도움을 주세요.
</p>

## 📄 저작권

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
翱翔的雄库鲁/easyaiot는 <a href="https://gitee.com/soaring-xiongkulu/easyaiot/blob/main/LICENSE" style="color: #3498db; text-decoration: none; font-weight: 600;">APACHE LICENSE 2.0</a> 오픈소스 라이선스를 채택합니다. 사용 과정에서 다음 사항에 유의해야 합니다:
</p>

<ol style="font-size: 14px; line-height: 1.8; color: #444; margin: 15px 0; padding-left: 25px;">
  <li>제품 관련 코드의 소스 헤더 주석과 출처를 수정해서는 안 됩니다;</li>
  <li>국가 안전, 명예 및 이익을 해치는 행위에 사용해서는 안 되며, 불법적인 목적으로 어떤 형태로든 사용해서는 안 됩니다;</li>
</ol>

## 🌟 Star 증가 추세도

[![Stargazers over time](https://starchart.cc/soaring-xiongkulu/easyaiot.svg?variant=adaptive)](https://starchart.cc/soaring-xiongkulu/easyaiot)
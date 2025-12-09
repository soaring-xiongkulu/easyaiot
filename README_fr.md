# EasyAIoT (Plateforme d'Application d'Algorithmes Intelligents à Intégration Cloud-Bord-Périphérique)

[![Gitee star](https://gitee.com/volara/easyaiot/badge/star.svg?theme=gvp)](https://gitee.com/soaring-xiongkulu/easyaiot/stargazers)
[![Gitee fork](https://gitee.com/volara/easyaiot/badge/fork.svg?theme=gvp)](https://gitee.com/soaring-xiongkulu/easyaiot/members)

<p style="font-size: 16px; line-height: 1.8; color: #555; font-weight: 400; margin: 20px 0;">
Mon souhait est que ce système soit utilisé dans le monde entier, rendant l'IA véritablement accessible à tous, permettant à chacun de bénéficier des avantages de l'IA, et non pas seulement réservée à une minorité.
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

## 🌟 Réflexions sur le projet

### 📍 Positionnement du projet

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT est une plateforme intelligente d'Internet des Objets (IoT) à intégration cloud-bord-périphérique, se concentrant sur l'intégration profonde de l'IA et de l'IoT. Grâce à des capacités fondamentales telles que la gestion des tâches algorithmiques, l'analyse de flux en temps réel et le raisonnement en cluster de services de modèles, la plateforme réalise une boucle fermée complète allant de la connexion des appareils à la collecte de données, l'analyse par IA et la prise de décision intelligente, atteignant véritablement l'interconnexion et le contrôle intelligent de toutes choses.
</p>

#### 🧠 Capacités d'IA

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Analyse IA en temps réel des flux vidéo</strong> : Prend en charge l'analyse intelligente par IA des flux vidéo en temps réel des caméras. Permet le traitement par algorithmes d'IA (détection d'objets, analyse comportementale, identification d'anomalies, etc.) des flux vidéo en temps réel, fournissant des résultats d'analyse en temps réel avec une réponse en millisecondes. Prend en charge l'analyse simultanée de multiples flux vidéo.</li>
  <li><strong>Tableau de bord unifié de surveillance et d'alerte algorithmique cloud-bord-périphérique</strong> : Fournit un tableau de bord unifié de surveillance et d'alerte algorithmique à intégration cloud-bord-périphérique, affichant en temps réel les informations clés telles que l'état des appareils, l'exécution des tâches algorithmiques, les statistiques d'événements d'alerte, les résultats d'analyse des flux vidéo, etc. Prend en charge la visualisation de données multidimensionnelles, réalisant une surveillance et une gestion unifiées du cloud, du bord et des périphériques, offrant aux décideurs un centre de commande de surveillance intelligent avec une vue globale.</li>
  <li><strong>Dessin de régions de détection d'appareils</strong> : Fournit un outil visuel de dessin de régions de détection d'appareils, prend en charge le dessin de régions de détection rectangulaires et polygonales sur les images instantanées des appareils, prend en charge la configuration flexible d'association entre les régions et les modèles algorithmiques, prend en charge la gestion visuelle, l'édition et la suppression des régions, prend en charge les raccourcis clavier pour améliorer l'efficacité du dessin, permettant une configuration précise de la détection de régions et fournissant des définitions précises de la plage de détection pour les tâches algorithmiques.</li>
  <li><strong>Mécanisme d'alerte liée intelligente</strong> : Prend en charge un mécanisme de triple liaison entre les régions de détection, les périodes de défense et les alertes d'événements. Le système détermine intelligemment si un événement détecté satisfait simultanément la plage de région de détection spécifiée, se trouve dans la période de défense et correspond au type d'alerte d'événement. Les alertes ne sont déclenchées que lorsque les trois conditions sont simultanément remplies, réalisant un filtrage conditionnel spatio-temporel précis, réduisant considérablement les taux de faux positifs et améliorant la précision et la praticité du système d'alerte.</li>
  <li><strong>Gestion de caméras à grande échelle</strong> : Prend en charge la connexion de centaines de caméras, fournissant des services complets pour la collecte, l'annotation, l'entraînement, le raisonnement, l'exportation, l'analyse, l'alerte, l'enregistrement, le stockage et le déploiement.</li>
  <li><strong>Gestion des tâches algorithmiques</strong> : Prend en charge la création et la gestion de deux types de tâches algorithmiques. Chaque tâche peut être liée de manière flexible à un extracteur d'images et un trieur pour réaliser une extraction précise des images vidéo et un tri des résultats.
    <ul style="margin: 5px 0; padding-left: 20px;">
      <li><strong>Tâches algorithmiques en temps réel</strong> : Utilisées pour l'analyse en temps réel des flux, prennent en charge le traitement en temps réel des flux RTSP/RTMP, offrant une capacité de réponse en millisecondes. Adaptées aux scénarios en temps réel comme la surveillance et la sécurité.</li>
      <li><strong>Tâches algorithmiques de capture d'images</strong> : Utilisées pour l'analyse des images capturées (instantanés). Effectuent une reconnaissance et une analyse intelligente des images capturées. Adaptées aux scénarios de revue d'événements, de recherche d'images, etc.</li>
    </ul>
  </li>
  <li><strong>Raisonnement en cluster de services de modèles</strong> : Prend en charge un cluster distribué de services de raisonnement de modèles, réalisant un équilibrage de charge intelligent, une bascule automatique en cas de défaillance et une haute disponibilité, améliorant considérablement le débit de raisonnement et la stabilité du système.</li>
  <li><strong>Gestion des plages horaires de surveillance</strong> : Prend en charge deux stratégies de surveillance : mode de surveillance complète et mode de surveillance partielle. Permet de configurer de manière flexible les règles de surveillance pour différentes périodes, réalisant une surveillance et des alertes intelligentes et précises selon les horaires.</li>
  <li><strong>OCR et reconnaissance vocale</strong> : Basé sur PaddleOCR pour une reconnaissance de texte haute précision. Prend en charge la conversion de la parole en texte et offre des capacités de reconnaissance multilingue.</li>
  <li><strong>Grand modèle visuel multimodal</strong> : Prend en charge diverses tâches visuelles comme la reconnaissance d'objets et la reconnaissance de texte, offrant des capacités puissantes de compréhension d'image et d'analyse de scène.</li>
  <li><strong>Grand modèle linguistique (LLM)</strong> : Prend en charge l'analyse et la compréhension intelligentes de divers formats d'entrée tels que les flux RTSP, la vidéo, l'image, l'audio et le texte, réalisant une compréhension de contenu multimodal.</li>
  <li><strong>Déploiement et gestion de version des modèles</strong> : Prend en charge le déploiement rapide et la gestion de version des modèles d'IA, permettant la mise en ligne en un clic, le retour à une version antérieure et la publication progressive.</li>
  <li><strong>Gestion multi-instances</strong> : Prend en charge l'exécution simultanée et l'ordonnancement des ressources de plusieurs instances de modèles, améliorant l'utilisation du système et l'efficacité des ressources.</li>
  <li><strong>Capture d'images par caméra</strong> : Prend en charge la fonction de capture d'images instantanées par caméra en temps réel. Permet de configurer des règles de capture et des conditions de déclenchement pour une capture intelligente et un enregistrement d'événements.</li>
  <li><strong>Gestion de l'espace de stockage des captures</strong> : Fournit une gestion de l'espace de stockage pour les images capturées, prenant en charge les quotas d'espace et les stratégies de nettoyage, assurant une utilisation rationnelle des ressources de stockage.</li>
  <li><strong>Gestion de l'espace de stockage des enregistrements</strong> : Fournit une gestion de l'espace de stockage pour les fichiers d'enregistrement vidéo, prenant en charge le nettoyage et l'archivage automatiques, réalisant une gestion intelligente des ressources de stockage.</li>
  <li><strong>Gestion des images capturées</strong> : Prend en charge la gestion complète du cycle de vie des images capturées (visualisation, recherche, téléchargement, suppression, etc.), offrant des fonctionnalités pratiques de gestion d'images.</li>
  <li><strong>Gestion du répertoire des appareils</strong> : Fournit une gestion en arborescence du répertoire des appareils, prenant en charge le regroupement, la gestion hiérarchique et le contrôle des autorisations, permettant une organisation ordonnée et une gestion fine des appareils.</li>
  <li><strong>Enregistrement vidéo d'alerte</strong> : Prend en charge la fonction d'enregistrement vidéo automatique déclenché par les événements d'alerte. Enregistre automatiquement les séquences vidéo pertinentes lors de la détection d'événements anormaux, fournissant une chaîne de preuves complète pour les alertes. Prend en charge la visualisation, le téléchargement et la gestion des enregistrements d'alerte.</li>
  <li><strong>Événements d'alerte</strong> : Fournit une fonctionnalité complète de gestion des événements d'alerte, prenant en charge la notification en temps réel, la consultation historique, l'analyse statistique, le traitement des événements et le suivi de l'état, réalisant une gestion du cycle de vie complet des alertes.</li>
  <li><strong>Relecture des enregistrements</strong> : Prend en charge la recherche rapide et la relecture des enregistrements historiques. Offre des opérations pratiques comme la navigation par timeline, la lecture à vitesse variable, le saut vers les images clés. Prend en charge la relecture synchronisée de multiples flux vidéo, répondant aux besoins de revue et d'analyse d'événements.</li>
</ul>

#### 🌐 Capacités IoT

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Connexion et gestion des appareils</strong> : Enregistrement, authentification, surveillance d'état, gestion du cycle de vie des appareils.</li>
  <li><strong>Gestion des produits et des modèles d'appareils</strong> : Définition de produit, configuration du modèle d'appareil, gestion des produits.</li>
  <li><strong>Support multi-protocoles</strong> : MQTT, TCP, HTTP et d'autres protocoles IoT.</li>
  <li><strong>Authentification des appareils et enregistrement dynamique</strong> : Connexion sécurisée, authentification d'identité, enregistrement dynamique des appareils.</li>
  <li><strong>Moteur de règles</strong> : Règles de flux de données, routage des messages, transformation des données.</li>
  <li><strong>Collecte et stockage des données</strong> : Collecte, stockage, requête et analyse des données des appareils.</li>
  <li><strong>Surveillance d'état des appareils et gestion des alertes</strong> : Surveillance en temps réel, alertes d'anomalies, prise de décision intelligente.</li>
  <li><strong>Gestion des notifications</strong> : Prend en charge 7 méthodes de notification, notamment Feishu, DingTalk, Enterprise WeChat, Email, Tencent Cloud SMS, Alibaba Cloud SMS et Webhook, permettant des notifications d'alerte flexibles et multi-canaux.</li>
</ul>


### 💡 Philosophie technique

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Nous pensons qu'aucun langage de programmation n'excelle en toute chose, mais grâce à une intégration profonde de trois langages de programmation, EasyAIoT exploite leurs avantages respectifs pour construire un écosystème technique puissant.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Java excelle pour construire une architecture de plateforme stable et fiable, mais il n'est pas adapté à la programmation réseau et à l'IA ; Python excelle en programmation réseau et développement d'algorithmes d'IA, mais présente des limites pour l'exécution de tâches haute performance ; C++ excelle pour l'exécution de tâches haute performance, mais il est moins bon que les deux précédents pour le développement de plateformes et la programmation IA. EasyAIoT adopte une architecture hybride trilingue, exploitant pleinement les avantages de chaque langage, pour construire une plateforme AIoT dont la réalisation est ambitieuse mais l'utilisation extrêmement simple.
</p>

![Architecture de la plateforme EasyAIoT.jpg](.image/iframe2.jpg)

### 🔄 Flux de données entre modules

<img src=".image/iframe3.jpg" alt="Architecture de la plateforme EasyAIoT" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

### 🤖 Technologie d'annotation à échantillon zéro

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
En s'appuyant de manière innovante sur les grands modèles, nous construisons un système technologique d'annotation à échantillon zéro (idéalement, éliminant complètement l'intervention humaine dans l'annotation pour automatiser le processus). Cette technologie génère des données initiales via les grands modèles et utilise des techniques d'incitation (prompt) pour réaliser l'annotation automatique. La qualité des données est ensuite assurée par une validation humaine (facultative), permettant d'entraîner un petit modèle initial. Ce petit modèle, grâce à des itérations continues et une auto-optimisation, réalise une évolution conjointe de l'efficacité d'annotation et de la précision du modèle, conduisant finalement à une amélioration constante des performances du système.
</p>

<img src=".image/iframe4.jpg" alt="Architecture de la plateforme EasyAIoT" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

### 🏗️ Caractéristiques de l'architecture du projet

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
EasyAIoT n'est pas vraiment un seul projet, mais cinq projets distincts.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
L'avantage ? Si vous êtes sur un appareil aux ressources limitées (comme un RK3588), vous pouvez extraire et déployer indépendamment l'un de ces projets. Ainsi, bien qu'il s'agisse d'une plateforme cloud, elle peut aussi fonctionner comme une plateforme edge.
</p>

<div style="margin: 30px 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;">

<p style="font-size: 16px; line-height: 1.8; margin: 0; font-weight: 500;">
🌟 Le vrai open source n'est pas facile. Si ce projet vous est utile, merci de lui attribuer une étoile (Star) avant de partir, ce serait le plus grand soutien pour moi !<br>
<small style="font-size: 14px; opacity: 0.9;">(À une époque où le faux open source est répandu, ce projet est une exception, fonctionnant uniquement par passion.)</small>
</p>

</div>

### 🌍 Support de localisation

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT répond activement à la stratégie de localisation, prenant pleinement en charge les matériels et systèmes d'exploitation locaux, offrant aux utilisateurs des solutions AIoT sûres et contrôlables :
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🖥️ Support côté serveur</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Compatibilité parfaite avec les processeurs d'architecture x86 Hygon (Haiguang)</li>
  <li>Support des plateformes matérielles de serveurs locaux</li>
  <li>Solutions d'optimisation des performances adaptées</li>
  <li>Assure un fonctionnement stable pour les applications d'entreprise</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">📱 Support côté edge (périphérie)</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Support complet des puces d'architecture ARM Rockchip (Ruixinwei)</li>
  <li>Adaptation parfaite aux plateformes de calcul edge mainstream comme le RK3588</li>
  <li>Optimisations profondes pour les scénarios edge</li>
  <li>Réalise un déploiement léger de l'intelligence edge</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🖱️ Support des systèmes d'exploitation</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Compatibilité avec le système d'exploitation Kylin (Qilin)</li>
  <li>Support des distributions Linux locales comme Founder (Fangde)</li>
  <li>Adaptation aux systèmes d'exploitation locaux mainstream comme Tongxin UOS</li>
  <li>Fournit des solutions de déploiement localisées complètes</li>
</ul>
</div>

</div>

## 🎯 Scénarios d'application

<img src=".image/适用场景.png" alt="Scénarios d'application" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

## 🧩 Structure du projet

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT est composé de cinq projets principaux :
</p>

<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50; width: 20%;">Module</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50;">Description</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Module WEB</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">Interface de gestion frontend basée sur Vue, offrant une expérience utilisateur unifiée.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Module DEVICE</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Avantage technique</strong> : Basé sur JDK21, offrant de meilleures performances et des fonctionnalités modernes.</li>
    <li><strong>Gestion des appareils</strong> : Enregistrement, authentification, surveillance d'état, gestion du cycle de vie des appareils.</li>
    <li><strong>Gestion des produits</strong> : Définition de produit, gestion des modèles d'appareils, configuration des produits.</li>
    <li><strong>Support des protocoles</strong> : MQTT, TCP, HTTP et autres protocoles IoT.</li>
    <li><strong>Authentification des appareils</strong> : Enregistrement dynamique, authentification d'identité, connexion sécurisée.</li>
    <li><strong>Moteur de règles</strong> : Règles de flux de données, routage des messages, transformation des données.</li>
    <li><strong>Collecte de données</strong> : Collecte, stockage, requête et analyse des données des appareils.</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Module VIDEO</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Traitement des flux multimédias</strong> : Prend en charge le traitement et la transmission en temps réel des flux RTSP/RTMP.</li>
    <li><strong>Gestion des tâches algorithmiques</strong> : Prend en charge deux types de tâches algorithmiques (en temps réel et de capture d'images) pour l'analyse des flux vidéo en temps réel et l'analyse des images capturées respectivement.</li>
    <li><strong>Extracteurs d'images et Trieurs</strong> : Prend en charge des stratégies flexibles d'extraction d'images et des mécanismes de tri des résultats. Chaque tâche peut être liée à un extracteur et un trieur indépendants.</li>
    <li><strong>Plages horaires de surveillance</strong> : Prend en charge la configuration par périodes des modes de surveillance complète et partielle.</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Module AI</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Analyse intelligente</strong> : Responsable de l'analyse vidéo et de l'exécution des algorithmes d'IA.</li>
    <li><strong>Cluster de services de modèles</strong> : Prend en charge les services de raisonnement de modèles distribués, réalisant l'équilibrage de charge et la haute disponibilité.</li>
    <li><strong>Raisonnement en temps réel</strong> : Fournit des capacités d'analyse intelligente en temps réel avec réponse en millisecondes.</li>
    <li><strong>Gestion des modèles</strong> : Prend en charge le déploiement, la gestion de version et l'ordonnancement multi-instances des modèles.</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Module TASK</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">Module de traitement de tâches haute performance basé sur C++, responsable de l'exécution de tâches nécessitant beaucoup de calcul.</td>
</tr>
</table>

## 🖥️ Avantages du déploiement multiplateforme

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT prend en charge le déploiement sur les trois principaux systèmes d'exploitation : Linux, Mac et Windows, offrant aux utilisateurs des solutions de déploiement flexibles et pratiques dans différents environnements :
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🐧 Avantages du déploiement Linux</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Adapté aux environnements de production, stable et fiable, faible consommation de ressources.</li>
  <li>Prend en charge le déploiement conteneurisé Docker, démarrage de tous les services en un clic.</li>
  <li>Adaptation parfaite aux serveurs et aux appareils de calcul edge (comme les appareils ARM RK3588).</li>
  <li>Fournit des scripts d'installation automatisés complets pour simplifier le processus de déploiement.</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🍎 Avantages du déploiement Mac</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Adapté aux environnements de développement et de test, intégration profonde avec le système macOS.</li>
  <li>Prend en charge le développement et le débogage locaux pour une validation rapide des fonctionnalités.</li>
  <li>Fournit des scripts d'installation pratiques, supporte les gestionnaires de paquets comme Homebrew.</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🪟 Avantages du déploiement Windows</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Adapté aux environnements serveurs Windows, réduisant la courbe d'apprentissage.</li>
  <li>Prend en charge les scripts d'automatisation PowerShell pour simplifier les opérations de déploiement.</li>
  <li>Compatibilité avec Windows Server et les versions desktop de Windows.</li>
  <li>Fournit un assistant d'installation graphique, convivial pour l'utilisateur.</li>
</ul>
</div>

</div>


<p style="font-size: 14px; line-height: 1.8; color: #2c3e50; font-weight: 500; margin: 20px 0; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #3498db; border-radius: 4px;">
<strong>Expérience unifiée</strong> : Quel que soit le système d'exploitation choisi, EasyAIoT fournit des scripts d'installation et une documentation de déploiement cohérents, garantissant une expérience de déploiement multiplateforme uniforme.
</p>

## ☁️ EasyAIoT = IA + IoT = Solution d'intégration cloud-bord-périphérique

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Prend en charge des milliers de scénarios verticaux, le développement sur mesure des modèles d'IA et des algorithmes d'IA, avec une intégration profonde.
</p>

<div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3498db;">
<h3 style="color: #2c3e50; margin-top: 0;">Doter tous les objets d'une vision intelligente : EasyAIoT</h3>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
Nous construisons un réseau efficace de connexion et de contrôle des appareils IoT (en particulier des caméras en masse). Nous intégrons profondément la technologie de transmission en temps réel des flux multimédias et l'intelligence artificielle (IA) de pointe pour créer un cœur de services unifié. Cette solution permet non seulement l'interconnexion d'appareils hétérogènes, mais intègre aussi profondément les flux vidéo haute définition avec de puissants moteurs d'analyse IA, donnant aux systèmes de surveillance des "yeux intelligents" – réalisant avec précision la reconnaissance faciale, l'analyse comportementale anormale, le contrôle des personnes à risque et la détection d'intrusion périmétrique.
</p>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
La plateforme prend en charge deux types de tâches algorithmiques : les tâches en temps réel pour l'analyse des flux RTSP/RTMP, offrant une réponse en millisecondes ; les tâches de capture d'images pour l'analyse intelligente des images capturées, supportant la revue d'événements et la recherche d'images. Grâce à la gestion des tâches algorithmiques, des stratégies flexibles d'extraction et de tri sont mises en œuvre, chaque tâche pouvant être liée à des extracteurs et trieurs indépendants. Combiné aux capacités de raisonnement en cluster des services de modèles, cela garantit une réponse en millisecondes et une haute disponibilité. En parallèle, deux stratégies de surveillance (complète et partielle) sont proposées, permettant une configuration flexible des règles de surveillance selon les horaires, pour une surveillance et des alertes intelligentes et précises par périodes.
</p>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
Concernant la gestion des appareils IoT, EasyAIoT fournit des capacités complètes de gestion du cycle de vie des appareils, prenant en charge plusieurs protocoles IoT (MQTT, TCP, HTTP), permettant une connexion rapide, une authentification sécurisée, une surveillance en temps réel et un contrôle intelligent des appareils. Le moteur de règles permet un flux et un traitement intelligents des données des appareils. Combiné aux capacités d'IA pour une analyse approfondie des données des appareils, il réalise une automatisation complète du processus allant de la connexion des appareils, la collecte de données, l'analyse intelligente à l'exécution des décisions, atteignant véritablement l'interconnexion et le contrôle intelligent de toutes choses.
</p>
</div>

<img src=".image/iframe1.jpg" alt="Architecture de la plateforme EasyAIoT" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">

## ⚠️ Clause de non-responsabilité

EasyAIoT est un projet d'apprentissage open source, sans lien avec des activités commerciales. Les utilisateurs doivent respecter les lois et règlements lors de l'utilisation de ce projet et ne pas mener d'activités illégales. Si EasyAIoT découvre que des utilisateurs ont des comportements illégaux, il coopérera avec les autorités concernées pour enquêter et signalera aux agences gouvernementales. Toute responsabilité légale découlant d'actes illégaux des utilisateurs sera assumée par l'utilisateur lui-même. En cas de dommages causés à des tiers par l'utilisation de l'utilisateur, l'utilisateur devra les indemniser conformément à la loi. L'utilisation de toutes les ressources associées à EasyAIoT est aux risques et périls de l'utilisateur.

## 📚 Documentation de déploiement

- [Documentation de déploiement de la plateforme](.doc/部署文档/平台部署文档_fr.md)

## 🎮 Environnement de démonstration

- URL de démo : http://36.111.47.113:8888/
- Compte : admin
- Mot de passe : admin123

## ⚙️ Dépôts du projet

- Gitee: https://gitee.com/soaring-xiongkulu/easyaiot
- Github: https://github.com/soaring-xiongkulu/easyaiot

## 📸 Captures d'écran
<div>
  <img src=".image/banner/banner-video1000.gif" alt="Capture d'écran 1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner-video1001.gif" alt="Capture d'écran 1" width="49%">
</div>
<div>
  <img src=".image/banner/banner1001.png" alt="Capture d'écran 1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1076.jpg" alt="Capture d'écran 1" width="49%">
</div>
<div>
  <img src=".image/banner/banner1074.jpg" alt="Capture d'écran 1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1075.jpg" alt="Capture d'écran 1" width="49%">
</div>
<div>
  <img src=".image/banner/banner1078.jpg" alt="Capture d'écran 1" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1077.jpg" alt="Capture d'écran 1" width="49%">
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
  <img src=".image/banner/banner1006.jpg" alt="Capture d'écran 3" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1009.jpg" alt="Capture d'écran 1" width="49%">
</div>
<div>
  <img src=".image/banner/banner1051.jpg" alt="Capture d'écran 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1053.jpg" alt="Capture d'écran 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1062.jpg" alt="Capture d'écran 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1063.png" alt="Capture d'écran 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1064.jpg" alt="Capture d'écran 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1065.jpg" alt="Capture d'écran 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1066.jpg" alt="Capture d'écran 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1067.jpg" alt="Capture d'écran 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1052.jpg" alt="Capture d'écran 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1054.jpg" alt="Capture d'écran 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1055.jpg" alt="Capture d'écran 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1056.jpg" alt="Capture d'écran 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1057.jpg" alt="Capture d'écran 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1058.jpg" alt="Capture d'écran 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1068.jpg" alt="Capture d'écran 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1069.jpg" alt="Capture d'écran 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1026.jpg" alt="Capture d'écran 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1028.jpg" alt="Capture d'écran 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1029.jpg" alt="Capture d'écran 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1030.jpg" alt="Capture d'écran 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1072.jpg" alt="Capture d'écran 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1031.jpg" alt="Capture d'écran 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1070.jpg" alt="Capture d'écran 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1071.jpg" alt="Capture d'écran 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1033.jpg" alt="Capture d'écran 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1035.jpg" alt="Capture d'écran 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1034.jpg" alt="Capture d'écran 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1036.jpg" alt="Capture d'écran 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1037.jpg" alt="Capture d'écran 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1038.jpg" alt="Capture d'écran 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1015.png" alt="Capture d'écran 5" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1010.jpg" alt="Capture d'écran 3" width="49%">
</div>
<div>
  <img src=".image/banner/banner1027.png" alt="Capture d'écran 2" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1016.jpg" alt="Capture d'écran 6" width="49%">
</div>
<div>
  <img src=".image/banner/banner1059.jpg" alt="Capture d'écran 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1060.jpg" alt="Capture d'écran 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1007.jpg" alt="Capture d'écran 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1008.jpg" alt="Capture d'écran 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1019.jpg" alt="Capture d'écran 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1020.jpg" alt="Capture d'écran 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1023.jpg" alt="Capture d'écran 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1024.jpg" alt="Capture d'écran 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1017.jpg" alt="Capture d'écran 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1018.jpg" alt="Capture d'écran 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1039.jpg" alt="Capture d'écran 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1061.jpg" alt="Capture d'écran 7" width="49%">
</div>
<div>
  <img src=".image/banner/banner1040.jpg" alt="Capture d'écran 8" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1042.jpg" alt="Capture d'écran 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1043.jpg" alt="Capture d'écran 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1044.jpg" alt="Capture d'écran 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1021.jpg" alt="Capture d'écran 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1022.jpg" alt="Capture d'écran 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1045.jpg" alt="Capture d'écran 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1046.jpg" alt="Capture d'écran 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1047.jpg" alt="Capture d'écran 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1048.jpg" alt="Capture d'écran 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1049.jpg" alt="Capture d'écran 7" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1050.jpg" alt="Capture d'écran 8" width="49%">
</div>
<div>
  <img src=".image/banner/banner1013.jpg" alt="Capture d'écran 9" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1014.png" alt="Capture d'écran 10" width="49%">
</div>
<div>
  <img src=".image/banner/banner1003.png" alt="Capture d'écran 13" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1004.png" alt="Capture d'écran 14" width="49%">
</div>
<div>
  <img src=".image/banner/banner1005.png" alt="Capture d'écran 15" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner1002.png" alt="Capture d'écran 16" width="49%">
</div>

## 🛠️ Support de service

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Nous offrons diverses méthodes de service pour vous aider à mieux comprendre la plateforme EasyAIoT et son code. Grâce à la documentation produit, aux groupes d'échange technique, à l'enseignement payant, etc., vous bénéficierez des services suivants :
</p>

<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
<thead>
<tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
<th style="padding: 15px; text-align: left; font-weight: 600;">Élément de service</th>
<th style="padding: 15px; text-align: left; font-weight: 600;">Contenu du service</th>
<th style="padding: 15px; text-align: center; font-weight: 600;">Tarification du service</th>
<th style="padding: 15px; text-align: left; font-weight: 600;">Méthode de service</th>
</tr>
</thead>
<tbody>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50;">Déploiement du système</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">Réaliser le déploiement d'EasyAIoT dans l'environnement réseau et matériel spécifié par le client.</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; text-align: center; color: #e74c3c; font-weight: 600;">500 RMB</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">Support de déploiement en ligne</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50;">Support technique</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">Fournir des réponses aux questions concernant les problèmes rencontrés lors du déploiement et de l'utilisation des fonctionnalités.</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; text-align: center; color: #e74c3c; font-weight: 600;">200 RMB</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">Support à distance en ligne dans les 30 minutes</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50;">Autres services</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">Développement sur mesure de solutions pour des domaines verticaux ; services de fonctionnalités et de durée sur mesure, etc.</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; text-align: center; color: #e74c3c; font-weight: 600;">À discuter</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444;">À discuter</td>
</tr>
</tbody>
</table>

## 📞 Contact (Après avoir ajouté WeChat, il faut suivre le compte officiel pour être ajouté au groupe d'échange technique)

<div>
  <img src=".image/联系方式.jpg" alt="Informations de contact" width="30%" style="margin-right: 20px;">
  <img src=".image/联系方式2.png" alt="Informations de contact" width="30%">
</div>

## 👥 Compte officiel (WeChat)

<div>
  <img src=".image/公众号.jpg" alt="Compte officiel" width="30%">
</div>

## 🪐 Planète du savoir (Zhishi Xingqiu) :

<p>
  <img src=".image/知识星球.jpg" alt="Planète du savoir" width="30%">
</p>

## 💰 Soutien / Don

<div>
    <img src=".image/微信支付.jpg" alt="Paiement WeChat" width="30%" height="30%">
    <img src=".image/支付宝支付.jpg" alt="Paiement Alipay" width="30%" height="10%">
</div>

## 🤝 Guide de contribution

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Nous accueillons toutes les formes de contributions ! Que vous soyez développeur de code, rédacteur de documentation ou rapporteur de problèmes, votre contribution aidera à améliorer EasyAIoT. Voici les principales façons de contribuer :
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">💻 Contribution au code</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Forkez le projet sur votre compte GitHub/Gitee</li>
  <li>Créez une branche de fonctionnalité (git checkout -b feature/AmazingFeature)</li>
  <li>Commitez vos modifications (git commit -m 'Add some AmazingFeature')</li>
  <li>Poussez vers la branche (git push origin feature/AmazingFeature)</li>
  <li>Ouvrez une Pull Request</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">📚 Contribution à la documentation</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Améliorez le contenu de la documentation existante</li>
  <li>Ajoutez des exemples d'utilisation et des meilleures pratiques</li>
  <li>Fournissez des traductions multilingues</li>
  <li>Corrigez les erreurs de documentation</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🌟 Autres façons de contribuer</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Signalez et corrigez les bugs</li>
  <li>Suggérez des améliorations de fonctionnalités</li>
  <li>Participez aux discussions de la communauté et aidez les autres développeurs</li>
  <li>Partagez vos expériences d'utilisation et des études de cas</li>
</ul>
</div>

</div>

## 🌟 Contributeurs majeurs

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Voici les contributeurs exceptionnels qui ont apporté une contribution significative au projet EasyAIoT. Leurs contributions ont joué un rôle clé dans la promotion du développement du projet. Nous exprimons notre gratitude la plus sincère !
</p>

<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
<thead>
<tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
<th style="padding: 15px; text-align: left; font-weight: 600; border: 1px solid #e0e0e0;">Contributeur</th>
<th style="padding: 15px; text-align: left; font-weight: 600; border: 1px solid #e0e0e0;">Contribution</th>
</tr>
</thead>
<tbody>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 20%;">℡夏别</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">A contribué à la documentation de déploiement Windows pour le projet EasyAIoT, fournissant un guide de déploiement complet pour les utilisateurs de la plateforme Windows, réduisant considérablement la difficulté de déploiement dans les environnements Windows et permettant à plus d'utilisateurs d'utiliser facilement la plateforme EasyAIoT.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 20%;">YiYaYiYaho</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">A contribué au script de déploiement en un clic de conteneurs Mac pour le projet EasyAIoT, fournissant une solution de déploiement automatisé pour les utilisateurs de la plateforme Mac, simplifiant considérablement le processus de déploiement dans les environnements Mac et améliorant l'expérience de déploiement pour les développeurs et les utilisateurs.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 20%;">山寒</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">A contribué au script de déploiement de conteneurs Linux pour le projet EasyAIoT, fournissant une solution de déploiement conteneurisé pour les utilisateurs de la plateforme Linux, réalisant un déploiement de conteneurs rapide et fiable, et fournissant des garanties importantes pour un fonctionnement stable dans les environnements de production.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 20%;">玖零。</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">A contribué au script de déploiement de conteneurs Linux pour le projet EasyAIoT, améliorant davantage la solution de déploiement conteneurisé pour les plateformes Linux, fournissant plus d'options pour les utilisateurs de différentes distributions Linux et promouvant les capacités de déploiement multiplateforme du projet.</td>
</tr>
</tbody>
</table>

<p style="font-size: 14px; line-height: 1.8; color: #2c3e50; font-weight: 500; margin: 20px 0; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #3498db; border-radius: 4px;">
<strong>Remerciements spéciaux</strong> : Le travail des contributeurs ci-dessus a jeté des bases solides pour les capacités de déploiement multiplateforme d'EasyAIoT. Leur professionnalisme et leur dévouement désintéressé méritent notre apprentissage et notre respect. Encore une fois, nous exprimons notre gratitude la plus sincère à ces contributeurs exceptionnels ! 🙏
</p>

## 🙏 Remerciements

Nous remercions les personnes suivantes pour leur soutien à ce projet, sous forme de contributions de code, de retours sur problèmes, de dons financiers, etc. ! L'ordre ci-dessous n'est pas hiérarchique :
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

## 💡 Attentes

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Vos suggestions pour améliorer EasyAIoT sont les bienvenues.
</p>

## 📄 Licence

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
翱翔的雄库鲁/easyaiot utilise la licence open source <a href="https://gitee.com/soaring-xiongkulu/easyaiot/blob/main/LICENSE" style="color: #3498db; text-decoration: none; font-weight: 600;">APACHE LICENSE 2.0</a>. Lors de l'utilisation, veuillez noter les points suivants :
</p>

<ol style="font-size: 14px; line-height: 1.8; color: #444; margin: 15px 0; padding-left: 25px;">
  <li>Ne pas modifier les commentaires d'en-tête du code source indiquant la provenance et l'origine du produit.</li>
  <li>Ne pas l'utiliser pour des actes nuisant à la sécurité nationale, à l'honneur et aux intérêts du pays, ni à des fins illégales de quelque manière que ce soit.</li>
</ol>

## 🌟 Tendance de croissance des Stars

[![Stargazers over time](https://starchart.cc/soaring-xiongkulu/easyaiot.svg?variant=adaptive)](https://starchart.cc/soaring-xiongkulu/easyaiot)
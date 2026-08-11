# EasyAIoT (Plateforme d'application d'algorithmes intelligents intégrée cloud-bord-périphérie)

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

## 🌐 Site officiel

Site officiel EasyAIoT : [http://36.111.47.113:8090/](http://36.111.47.113:8090/)

Présentation produit, fonctionnalités, trois niveaux matériels, téléchargement des installateurs et accès à la documentation — pour comprendre rapidement la valeur de la plateforme et démarrer le déploiement.

## 📖 Présentation du projet

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
<strong>EasyAIoT</strong> (Easy AI Internet of Things) est une <strong>plateforme d'application d'algorithmes intelligents à intégration cloud-bord-périphérique</strong>, dédiée à la fusion profonde de l'intelligence artificielle et de l'Internet des objets — permettant aux caméras, capteurs et ressources de calcul en périphérie de collaborer sur le terrain. De la connexion des appareils et la collecte de données à l'analyse visuelle en temps réel, l'évaluation intelligente et l'orchestration des alertes, l'ensemble de la chaîne s'accomplit au sein d'une seule pile logicielle.
</p>

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
De nombreux projets IoT intelligents se heurtent au même obstacle lors du déploiement : systèmes vidéo, plateformes d'appareils et services algorithmiques fonctionnent en silos — l'intégration est coûteuse, l'exploitation fragmentée et la montée en charge difficile. <strong>EasyAIoT résout ce problème avec une plateforme unique</strong> — le même logiciel se déploie sur une box edge de 4 Go pour l'intelligence ponctuelle, sur des caméras IA tout-en-un pour une couverture à l'échelle d'un étage, ou dans un appliance full-stack d'entreprise regroupant gestion IoT, accès vidéo massif et analyse IA — sans maintenir plusieurs versions ni réintégrer des systèmes hétérogènes.
</p>

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
La plateforme comprend notamment les modules <strong>WEB, APP, DEVICE, NODE, VIDEO, RTC, AI, RUNTIME, VISUALIZE, TRANSFORM, PANEL et SITE</strong>, avec <strong>COMPILE</strong> pour le packaging et la livraison multiplateformes (dont Ubuntu / CentOS·RHEL <strong>7–9</strong> (x86 + <strong>CentOS ARM</strong>, paquets el7/el8/el9) / <strong>Kylin (麒麟) / openEuler (欧拉)</strong> / Windows / macOS / ARM). Côté capacités : accès caméra multi-protocoles GB28181 / ONVIF, <strong>pont P2P RTC pour caméras grand public</strong> (basé sur go2rtc, couvrant <strong>Tapo, Tuya, Ring, Nest, Xiaomi, Wyze, DoorBird, GoPro et Roborock</strong> — complément Tapo en magasin, onboarding Tuya white-label, sonnettes Ring/Nest à l'étranger, réutilisation Xiaomi, scale-out Wyze, interphone DoorBird, vues mobiles GoPro, caméras Roborock — onboarding Web en un clic vers vidéo unifiée et jugement IA), <strong>accès vue aérienne dock/drone DJI</strong>, tâches algorithmiques temps réel / capture / patrouille, <strong>couche d’exécution native haute vitesse RUNTIME</strong> (binaire compilé pour pull/décodage, inférence YOLO, push à cadres et relais multi-canal brut — moins de CPU/mémoire et latence plus stable qu’une chaîne interprétée ; un seul binaire couvre temps réel / capture / patrouille / relais), détection d'objets YOLO et annotation automatique SAM zero-shot, reconnaissance faciale/plaques, post-traitement métier orchestrable, planification de clusters de calcul fédérés, et <strong>mode cluster edge fédéré illimité</strong> (cartes de développement ordinaires prêtes à l'emploi, décision intelligente sur site, alertes et preuves agrégées automatiquement vers le cloud, puissance de calcul déployable selon les besoins), ainsi que la gestion du cycle de vie des appareils IoT MQTT / TCP / HTTP / Modbus-TCP / Modbus-RTU / OPC UA, et <strong>grands écrans de visualisation et synoptiques de processus Web</strong>, pour que les données alimentent la situation de commandement et les synoptiques de processus ; plus le nouvel <strong>engine TRANSFORM de flux de données multidirectionnel</strong>, qui livre les événements métier de la plateforme vers MES / ERP / CRM / WMS selon contrat — intégration multipartite configurable, traçable et réutilisable ; et l'<strong>entrée de livraison et de permanence PANEL</strong> pour installer et réceptionner l'appliance dès l'arrivée, sans attendre à chaque fois que les développeurs tapent des commandes à distance ; ainsi que le <strong>site officiel SITE</strong> pour présenter la valeur produit, trois niveaux matériels et l'entrée téléchargement — comprendre d'abord, puis télécharger et déployer. Côté expérience : console Web et App mobile / mini-programme alignées — centres de commande et inspections terrain partagent la même logique métier, partout et à tout moment.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 16px 0 8px 0;">
<strong>En une phrase :</strong> EasyAIoT = IA + IoT — interconnecter toutes choses tout en leur donnant une vision et un contrôle intelligents.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
📄 Pour une présentation illustrée plus complète, consultez <a href=".doc/项目介绍/EasyAIoT项目介绍 V2.0.pptx" style="color: #3498db; text-decoration: none; font-weight: 600;">Présentation du projet EasyAIoT V2.0 (PPT)</a>, ainsi que <a href=".doc/项目介绍/AI视频监控分析平台.pdf" style="color: #3498db; text-decoration: none; font-weight: 600;">Plateforme d'analyse de vidéosurveillance IA (PDF)</a>.
</p>

## 🌟 Réflexions sur le projet

### 📍 Positionnement du projet

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT est une plateforme intelligente d'Internet des Objets (IoT) à intégration cloud-bord-périphérique, se concentrant sur l'intégration profonde de l'IA et de l'IoT. Grâce à des capacités fondamentales telles que la gestion des tâches algorithmiques, l'analyse de flux en temps réel et le raisonnement en cluster de services de modèles, la plateforme réalise une boucle fermée complète allant de la connexion des appareils à la collecte de données, l'analyse par IA et la prise de décision intelligente, atteignant véritablement l'interconnexion et le contrôle intelligent de toutes choses.
</p>

### 🎛️ PANEL : installer et réceptionner dès l'arrivée — permanence sans attendre le remote

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Les projets IoT intelligents butent le plus souvent sur le « dernier kilomètre » : la machine est sur site, mais <strong>elle ne s'installe pas, ne passe pas la recette, et en panne on ne peut qu'attendre que les développeurs tapent des commandes à distance</strong> — coût de présence et délai de réception restent bloqués sur les personnes. PANEL est une <strong>entrée indépendante de livraison et de permanence</strong> pour intégrateurs et exploitation terrain — installation en un clic par niveau, santé et dépendances de la machine visibles, démarrer/arrêter et lire les journaux sur place ; <strong>même avant que la console métier soit prête, on peut monter, tenir et livrer l'appliance</strong>, transformant « machine sur site → plateforme utilisable → prête à la recette » d'une attente en une boucle fermée le jour même.
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Recette plus rapide</strong> : Sur place, choisir mini / standard / full, installer, voir progrès et résultats immédiatement — moins de « bloqué à mi-chemin sans savoir où » ; PoC et livraison série passent la recette plus vite</li>
  <li><strong>Moins de coût présence et remote</strong> : Conteneurs actifs, pression ressources, logs bloqués — visibles d'un coup d'œil ; redémarrer, nettoyer le cache, tirer les images sans d'abord fouiller la doc ni attendre le support développeur ; la permanence traite seule les pannes courantes</li>
  <li><strong>Un même référentiel multi-projets</strong> : La même entrée d'install et d'ops se réutilise sur appliances et salles — livraison, permanence et handover partagent un standard, sans « chaque site a sa tradition orale »</li>
</ul>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0 8px 0;">
📦 <strong>Téléchargement des installateurs</strong> : Paquets pour Ubuntu / Debian, CentOS / RHEL <strong>7–9</strong> (x86 + <strong>CentOS ARM</strong>, RPM el7/el8/el9), Windows, macOS et cibles ARM / <strong>Kylin (麒麟) / openEuler (欧拉)</strong> sur <a href="https://gitee.com/volara/easyaiot/releases" style="color: #3498db; text-decoration: none; font-weight: 600;">Gitee Releases</a>.
</p>

| | | |
|:---:|:---:|:---:|
| ![Vue d'ensemble](.image/banner/panel/panel_1000.png) | ![Conteneurs](.image/banner/panel/panel_1001.png) | ![Journaux](.image/banner/panel/panel_1002.png) |
| ![Déploiement](.image/banner/panel/panel_1003.png) | ![Images prêtes](.image/banner/panel/panel_1004.png) | ![Pull images](.image/banner/panel/panel_1005.png) |
| ![Diagnostic](.image/banner/panel/panel_1006.png) | ![Maintenance](.image/banner/panel/panel_1007.png) | ![Topologie](.image/banner/panel/panel_1008.png) |

### 📡 RTC : pont P2P caméras grand public — intégrer les appareils « sans RTSP »

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
À la maison, en magasin ou en sécurité légère, de nombreux appareils proviennent de <strong>Tapo, Tuya, Ring, Nest, Xiaomi, Wyze, DoorBird, GoPro et Roborock</strong> — protocoles P2P propriétaires, <strong>sans RTSP standard</strong>. EasyAIoT ajoute le module <strong>RTC</strong> basé sur <a href="https://github.com/AlexxIT/go2rtc" style="color: #3498db; text-decoration: none; font-weight: 600;">go2rtc</a>, qui <strong>unifie flux et audio bidirectionnel pour les neuf marques</strong> — enregistrement, prévisualisation, relais, tâches IA et alertes comme les caméras GB28181/ONVIF.
</p>

<table style="width: 100%; border-collapse: collapse; margin: 12px 0 20px; font-size: 14px;">
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; width: 14%;">Marque</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; width: 18%;">Fabricant</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; width: 28%;">Appareils typiques</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600;">Valeur</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Tapo</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">TP-Link</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">IPC maison/magasin</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Complément à faible coût ; audio bidirectionnel</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Tuya</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">Tuya Smart</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">IPC écosystème Tuya</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Onboarding white-label/OEM massif</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Ring</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">Amazon</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Sonnettes, caméras extérieures</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Surveillance sonnettes à l'étranger</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Nest</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">Google</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Nest Cam, Doorbell</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Sites premium écosystème Google</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Xiaomi</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">Mi Home</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Caméras Mi Home</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Réutilisation du parc installé</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Wyze</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">Wyze</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Wyze Cam v3/v4</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Scale-out ultra low-cost</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>DoorBird</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">DoorBird</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Sonnettes intelligentes</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Interphone d'entrée premium</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>GoPro</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">GoPro</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">HERO9–12</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Vues tactiques mobiles</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Roborock</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">Roborock</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Aspirateurs avec caméra</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Vues mobiles sous les meubles</td></tr>
</table>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Onboarding Web en un clic</strong> : « Connecter caméra RTC » avec formulaires dynamiques par marque</li>
  <li><strong>Chaîne complète</strong> : WEB → VIDEO <code>/register/device/rtc-live</code> → API RTC → go2rtc P2P → RTSP → SRS → Jessibuca + IA</li>
  <li><strong>Audio bidirectionnel</strong> : Tapo, Tuya, Ring, Wyze, DoorBird, Roborock</li>
  <li><strong>Cycle de vie synchronisé</strong> : suppression appareil nettoie les flux go2rtc</li>
  <li><strong>Docker tout-en-un</strong> : <code>bash RTC/install_linux.sh start</code> lance go2rtc + API de gestion ; host network pour P2P LAN</li>
</ul>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0 8px 0;">
📖 Voir <a href="RTC/README.md" style="color: #3498db; text-decoration: none; font-weight: 600;">README du module RTC</a>.
</p>

### 🎯 Trois profils matériels, une plateforme

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Beaucoup de projets IoT intelligents butent au déploiement : <strong>les fonctionnalités complètes ne tiennent pas sur de petites machines ; pour les faire tenir, on réduit les capacités, on scinde les versions et on maintient plusieurs packages de déploiement.</strong> EasyAIoT résout ce dilemme avec une seule plateforme — <strong>boîtier edge pour l'intelligence ponctuelle, caméra tout-en-un IA pour l'analyse au mur, tout-en-un full-stack AIoT pour la chaîne complète en une seule boîte</strong>. Choisissez le niveau adapté à votre matériel terrain ; le même logiciel couvre le pilote mono-site, la couverture d'un bâtiment et la livraison full-stack — sans versions séparées.
</p>

| Niveau | Matériel typique (exemples) | RAM recommandée | Ce que vous pouvez faire | Vérifié |
| :-- | :-- | :--: | :-- | :--: |
| **mini** Edge Lite | <strong>Boîtier edge</strong> (PC industriel 8 GB, tout-en-un sécurité magasin, passerelle de site) | ≥ 8 GB | <strong>Intelligence à un point</strong> : accès caméras, analyse temps réel, alertes intelligentes, inférence ; plan événements identique à standard/full (Gateway + iot-sink + EMQX) | ~4–6 GB utilisés, marge confortable |
| **standard** Standard | <strong>Caméra tout-en-un IA</strong> (terminal caméra intelligent, caméra de surveillance IA avec calcul, analyseur IA multi-capteurs) | ≥ 16 GB | <strong>Chaque caméra est un nœud intelligent</strong> : plusieurs caméras au mur couvrent un étage/campus ; appareils, règles et calcul orchestrés ensemble | ~10 GB, stable avec marge |
| **full** Complet (défaut) | <strong>Tout-en-un full-stack AIoT</strong> (tout-en-un pilotage full-stack entreprise, hôte IoT full-stack sectoriel, plateforme intelligente cloud-bord-périphérique) | ≥ 20 GB | <strong>IoT + vidéo + IA en une boîte</strong> : gestion des appareils, accès massif, analyse intelligente, commandement unifié — capacités complètes à long terme | ~14 GB, pleine capacité avec marge |

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 16px 0 8px 0;">
<strong>Sélection du niveau et conformité des ressources (vérifié) :</strong>
</p>

| | | |
|:---:|:---:|:---:|
| ![Boîtier edge mini](.image/deploy-profile-mini.png) | ![Caméra tout-en-un IA standard](.image/deploy-profile-standard.png) | ![Tout-en-un full-stack full](.image/deploy-profile-full.png) |

#### 🧠 Capacités d'IA

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Couche d’exécution haute vitesse RUNTIME</strong> : Sort « regarder / calculer / pousser » des chaînes interprétées vers un <strong>binaire natif</strong> qui porte <strong>pull → décodage → inférence → callback d’alerte → push à cadres</strong>. Face aux chemins Python, il évite le GIL et le coût multi-processus — sur le même matériel : <strong>plus de canaux par boîtier, latence bout-en-bout plus basse, moins de CPU/mémoire</strong>. Temps réel / capture / patrouille et relais multi-canal brut partagent la même capacité ; défaut <code>executor=cpp</code>. En pratique : d’abord des dizaines de canaux NVR clairs, puis l’IA seulement sur les canaux critiques ; basculer aperçu brut et jugement à cadres sans qu’un chemin n’écrase l’autre ; VIDEO/WEB gardent orchestration, archivage et droits, RUNTIME se concentre sur débit et latence — monter en canaux sans changer toute la machine</li>
  <li><strong>Relais de flux haute performance</strong> : Conçu pour « remplir d’abord le mur / l’écran partagé, sans activer l’IA sur chaque canal » — canaux NVR et points bâtiment en un clic. Chemin par défaut : <strong>RUNTIME</strong> haute performance (mode compatibilité toujours possible) pour garder le multi-canal brut à moindre coût. Vision brute et jugement IA peuvent coexister ; au démarrage/arrêt des tâches algo, la politique de relais suit automatiquement. Prévisualisation côte à côte pour comparer latence et cadres à l’acceptance</li>
  <li><strong>Personnalisation du nom et du logo sur tous les points de contact</strong> : Une fois EasyAIoT déployé sur site, les utilisateurs doivent voir « leur » plateforme, et non un nom de produit générique. Le tableau de bord de monitoring intègre un panneau visuel « Identité de la plateforme » permettant aux administrateurs de remplacer l'image de marque depuis l'interface — nom et logo de la console d'administration (barre latérale, titre du navigateur) ; titre indépendant du tableau de commandement ; page de connexion avec nom, logo, titre du formulaire et images de fond claires/sombres. Trois points de contact unifiés, effet immédiat, sauvegarde et réinitialisation en un clic.
    <ul style="margin: 5px 0; padding-left: 20px;">
      <li><strong>Pour les intégrateurs système et éditeurs de solutions</strong> : suppression des coûts de reskin frontend, de développement sur mesure et de cycles de release ; bascule rapide entre démo PoC et livraison client, une même base de code pour plusieurs clients, cycles de paiement raccourcis et meilleure réutilisation des solutions</li>
      <li><strong>Pour les utilisateurs finaux (administrations, campus, hôpitaux, etc.)</strong> : page de connexion, grand écran de commandement et console quotidienne affichent le nom et l'identité de l'organisation — plus d'appropriation et de crédibilité lors des visites de direction et du déploiement interne, conforme aux exigences d'image de marque des organismes publics et grandes entreprises</li>
      <li><strong>Pour les équipes de déploiement privé et d'exploitation</strong> : configuration sur site le jour de l'installation pour validation immédiate, sans attente de planning développement ; restauration en un clic après démos multi-clients ou phases pilotes, réduisant les coûts de bascule et de redéploiement</li>
    </ul>
  </li>
  <li><strong>Détection d'objets YOLO26 nouvelle génération</strong> : Détection d'objets de dernière génération intégrée à la plateforme, prête à l'emploi pour l'analyse en temps réel et la reconnaissance sur captures. Sur le même matériel, connectez davantage de caméras avec une réponse plus rapide et moins de fausses alertes. Couvre la boucle complète de la collecte de données, de l'annotation et de l'entraînement jusqu'au déploiement et à l'inférence, permettant d'itérer à moindre coût des modèles de détection sur mesure et de couvrir rapidement les scénarios courants de sécurité et industriels (port du casque, intrusion, risque d'incendie, etc.), pour que « voir juste, calculer vite, évoluer facilement » devienne la norme</li>
  <li><strong>Analyse de pose humaine YOLO26</strong> : Au-delà de la détection d'objets, ajoute l'analyse des points clés du corps et de la pose squelettique, prête à l'emploi, avec trois modes d'entrée : images, vidéos et flux caméra en temps réel. Le mode image produit simultanément annotations de squelette et comptage de personnes ; le mode vidéo prend en charge le suivi de progression et le téléchargement des résultats ; le mode caméra se connecte aux flux RTSP/RTMP en temps réel et superpose les résultats de pose sur le flux relayé pour la surveillance à distance et l'analyse comportementale. La page d'inférence de modèle permet de basculer en un clic entre « Analyse de pose » et « Détection d'objets », adaptée aux normes de travail sur chantier, l'évaluation des mouvements sportifs, la perception des rassemblements de foule et autres scénarios nécessitant de « voir clairement la structure et la forme du corps humain », faisant évoluer la plateforme de « encadrer les cibles » vers « comprendre la pose »</li>
  <li><strong>Support d'accès multi-protocole pour caméras</strong> : Support complet des deux principaux protocoles de vidéosurveillance GB28181 et ONVIF, permettant un accès et une gestion standardisés des appareils. GB28181, en tant que norme nationale chinoise, s'adapte parfaitement aux équipements de vidéosurveillance domestiques principaux ; ONVIF, en tant que norme universelle internationale, est largement compatible avec les principales marques de caméras mondiales. Grâce au support double protocole, la plateforme s'intègre de manière transparente aux systèmes de vidéosurveillance existants, réalisant un accès plug-and-play, une découverte automatique et une gestion unifiée, réduisant considérablement les barrières d'accès, améliorant la compatibilité et l'évolutivité, et fournissant une base technique solide pour le déploiement à grande échelle de caméras. En outre, ajout du scan, de l'enregistrement et de la gestion unifiée en masse des NVR sur le même sous-réseau et entre sous-réseaux, couvrant Hikvision, Dahua, Huawei, Ezviz, Xiaomi et autres marques majeures — découverte par sous-réseau, enregistrement en un clic et importation groupée des canaux via les protocoles natifs des appareils. Pour les caméras grand public sans RTSP comme Mi Home, le <strong>module RTC (pont go2rtc)</strong> les intègre à la même plateforme, réduisant davantage les coûts d'intégration et d'exploitation</li>
  <li><strong>Accès vue aérienne dock / drone DJI</strong> : Dépasse la limite des caméras fixes « sol uniquement, difficile de couvrir de larges zones » ; intègre les images aériennes des docks et drones du système DJI FlightHub dans la boucle unifiée vidéo et jugement IA. Le module streaming offre « Connexion live DJI » avec <strong>démarrage live via API FlightHub</strong> et <strong>source live manuelle</strong> — le mode API lance en un clic le flux live fabricant et enregistre automatiquement l'appareil ; le mode manuel accepte directement RTSP / RTMP / HTTP-FLV / HLS. Une fois connectées, les images aériennes peuvent être co-gérées à l'écran avec les points GB28181/ONVIF ; les responsables consultent l'état des docks et des appareils comme pour des caméras fixes, puis y raccordent l'analyse IA temps réel, les alarmes et la conservation de preuves — couvrant rapidement patrouille à large zone, reconnaissance d'urgence et comblement de périmètre que les points fixes peinent à atteindre, raccourcissant la chaîne « détecter — localiser — agir » et faisant passer la sécurité intelligente d'un déploiement plan à une perception collaborative ciel–terre.</li>
  <li><strong>Pont P2P RTC caméras grand public</strong> : Une intégration pour <strong>Tapo, Tuya, Ring/Nest, Xiaomi Mi Home, Wyze, DoorBird, GoPro et Roborock</strong> — neuf marques sans RTSP standard. Le module RTC sur go2rtc fournit pont P2P et API unifiée. Console Web « Connecter caméra RTC » avec formulaires par marque ou OAuth ; après pont, caméras grand public et pro GB28181/ONVIF <strong>même écran, mêmes tâches IA et alertes</strong></li>
  <li><strong>Interphonie en temps réel et contrôle PTZ à distance</strong> : Dépasse la limite traditionnelle de la vidéosurveillance « voir sans agir ». Les opérateurs peuvent effectuer l'annonce vocale et le contrôle PTZ sur le même écran de prévisualisation en temps réel — sans changer de système ni se rendre sur place. Communication à distance, guidage d'évacuation ou interdiction d'actes illicites : la réponse passe de « envoyer quelqu'un sur site » à « parler et agir immédiatement ». Le contrôle PTZ permet d'orienter, zoomer et focaliser la caméra à volonté — en cas d'urgence, viser rapidement la zone concernée et agrandir les détails, formant une boucle de gestion sur site intégrée « voir clairement, viser précisément, parler et toucher ». Pleinement compatible avec les appareils GB28181 et ONVIF, tire parti des actifs de vidéosurveillance existants sans achat d'équipement d'interphonie ou de logiciels tiers, donnant instantanément aux caméras déployées des capacités de communication à distance et de dispatch flexible, réduisant significativement les silos système et les coûts de surveillance</li>
  <li><strong>Post-traitement algorithmique orchestrable</strong> : Dépasse le goulot d'étranglement « détecter sans pouvoir juger » en ajoutant une couche métier d'analyse indépendante au-dessus de la détection d'objets, transformant les résultats de perception visuelle en événements métier exploitables, traçables et statistiquement mesurables. Permet de définir de manière flexible par tâche des règles de scénario telles que le comptage de personnes, le franchissement de ligne, le dépassement de temps de présence, la présence prolongée en zone et les alertes composites multi-conditions — pour s'adapter rapidement aux besoins différenciés de la supervision de chantiers, de la sécurité de campus et du contrôle du trafic sans retoucher constamment les modèles, forgeant les capacités visuelles génériques en leviers de gestion proches du terrain. Le post-traitement et l'analyse en temps réel fonctionnent de manière indépendante et en parallèle — les flux de surveillance continuent d'être analysés sans interruption tandis que la logique métier s'étend élastiquement à la demande ; les résultats d'analyse sont automatiquement archivés et déclenchent des alertes précises, réduisant nettement les faux positifs/négatifs et les coûts de revue manuelle. Les métiers se concentrent sur l'expression des règles, la plateforme assure la distribution, l'exécution et la montée en charge — pour passer réellement de « voir » à « juger clairement, maîtriser et mettre en œuvre »</li>
  <li><strong>Cluster fédéré multi-nœuds centraux × multi-nœuds de travail</strong> : Conçu pour les déploiements inter-régionaux, multi-salles et cloud-bord, la plateforme adopte une architecture fédérée « N nœuds centraux + N nœuds de travail » — les nœuds centraux assurent l'orchestration unifiée, les nœuds de travail portent l'exécution calcul et média, avec extension horizontale. Chaque nœud central gère les nœuds de travail de son domaine, avec distribution à distance et déploiement en un clic des capacités de streaming, transcodage audio-vidéo, analyse vidéo, inférence et entraînement de modèles ; plusieurs nœuds centraux peuvent s'interconnecter et se synchroniser. La vue en couloirs du cluster présente intuitivement la topologie « central — travail » et les niveaux de ressources. Tâches algorithmiques, pipelines d'annotation automatique et relais de flux sont planifiés intelligemment selon le rôle des nœuds et les capacités GPU — ingestion massive de flux, inférence à haute concurrence et entraînement distribué coexistent dans un même cluster : « intégration fluide, planification claire, extension ouverte, gouvernance complète »</li>
  <li><strong>Pipeline d'orchestration d'annotation automatique SAM à démarrage zéro</strong> : Conçu pour les scénarios de démarrage à froid sans échantillons annotés ni modèle de détection utilisable, la plateforme intègre la segmentation SAM à vocabulaire ouvert et fournit un pipeline d'annotation sans surveillance en un clic. Selon la stratégie configurée, le système enchaîne automatiquement l'extraction d'images depuis les caméras, l'annotation initiale par invites textuelles, le fine-tuning YOLO déclenché une fois les seuils atteints, l'inférence YOLO à haute vitesse en phase de production avec bascule intelligente vers SAM pour les détections manquées, l'entraînement itératif périodique et l'export automatique des jeux de données — bouclant la chaîne complète « capture — annotation — entraînement — export ». Prend en charge la pause/reprise et la planification élastique sur files locales ou cluster, avec configuration visuelle des stratégies et journaux d'exécution, pour faire émerger une capacité de détection sur mesure à partir de zéro échantillon et zéro modèle — « définir les catégories en mots, laisser le modèle se construire » devient le chemin par défaut pour constituer des jeux de données</li>
  <li><strong>Cluster de calcul élastique à dizaines de milliers de nœuds et pool d'extension horizontale</strong> : Conçu pour les charges de travail IA et vidéo à très grande échelle, la plateforme constitue une base de calcul distribuée cloud-bord-périphérique qui regroupe tâches algorithmiques, relais de flux, services algorithmiques, entraînement et inférence de modèles dans un même cadre d'équilibrage de charge horizontal et d'élasticité. Chaque nouveau serveur intégré en un clic rejoint immédiatement le pool de calcul programmable ; le planificateur répartit automatiquement les tâches selon les niveaux de ressources et la pression métier, permettant une montée en charge linéaire — de quelques centaines à des dizaines de milliers de caméras, d'une machine unique à un cluster de dizaines de milliers de nœuds — sans redéploiement ni réglage manuel. Ingestion massive de flux, inférence à haute concurrence et entraînement distribué coexistent dans un même pool : « extension à la demande, exécution stable, gouvernance maîtrisée »</li>
  <li><strong>Visualisation spatiale Tianditu et analyse sur carte</strong> : Intégration avec la carte nationale chinoise Tianditu pour rassembler caméras, alertes et reconnaissance personnes/véhicules sur une seule carte, faisant passer la surveillance de « regarder les flux » à « voir l'ensemble ». Les modules média en streaming et alertes proposent une vue « Distribution cartographique » avec arborescence des appareils pour un focus régional, offrant une visibilité immédiate sur la disposition des points de contrôle et l'état en ligne. Clic sur carte, recherche de lieu et import par lot de coordonnées permettent de géolocaliser rapidement les canaux GB, NVR et caméras directes, afin que chaque flux ait un contexte spatial clair. Les alertes sont automatiquement positionnées via les coordonnées des caméras ; filtres par heure, type d'événement, tâche et étiquettes métier, avec accès aux captures et enregistrements en un clic — pour passer rapidement de « où cela s'est-il produit » à l'action. Combiné aux bibliothèques faciales et de plaques, les correspondances sur plusieurs sites forment des fils spatiaux — <strong>recherche de traces par personne</strong> pour reconstituer trajets et présence dans la zone surveillée ; <strong>recherche de traces par véhicule</strong> pour relier les passages et localiser itinéraires et zones d'arrêt, pour retrouver personnes/véhicules, déployer la patrouille et analyser après incident. Les appareils mobiles supportent aussi la relecture de trajectoires sur une frise chronologique. Basculement libre entre fond vectoriel et imagerie satellite avec ajustement automatique de la vue, pour que les responsables utilisent la carte comme levier de détection, ciblage et coordination</li>
  <li><strong>Déploiement multi-GPU Qwen / DeepSeek</strong> : Prend en charge le déploiement de grands modèles de langage tels que Qwen et DeepSeek en parallèle sur plusieurs GPU. Les ressources GPU peuvent être planifiées de manière flexible au niveau du cluster et des Workers, permettant la mise à l'échelle élastique et l'équilibrage de charge des instances de modèles pour fournir une inférence stable en cas de forte concurrence et de contextes longs</li>
  <li><strong>Compréhension intelligente des grands modèles visuels</strong> : Intégré avec le grand modèle visuel QwenVL3, prend en charge le raisonnement visuel profond et la compréhension sémantique des images vidéo en temps réel, capable d'effectuer une analyse intelligente et une compréhension de scène du contenu des images, fournissant des capacités cognitives visuelles plus riches, réalisant un saut de la perception au niveau des pixels à la compréhension au niveau sémantique</li>
  <li><strong>Analyse IA en temps réel des flux vidéo des caméras</strong> : Pour les flux RTSP/RTMP, pipeline complet pull/décodage → inférence → sortie structurée → alertes ; par défaut via <strong>RUNTIME</strong> (même exécuteur que capture/patrouille), réponse en millisecondes, et <strong>push par défaut du flux de détection à cadres</strong> pour bascule opérateur. Vision (brut) et algorithme (détection) indépendants ; résultats liés aux zones, périodes, visage/plaque et post-traitement orchestrable</li>
  <li><strong>Patrouille intelligente des caméras</strong> : Pour les scénarios de surveillance à grand nombre de caméras et effectifs limités, la plateforme offre des patrouilles multi-écrans et par lot depuis l'arborescence des appareils, réalisant une analyse IA en rotation sur de larges parcs caméras avec un nombre limité de connexions simultanées. Trois modes de planification : rotation, pool de connexions et hybride — capture automatique à intervalle défini, exécution des modèles de détection et liaison avec alertes et reconnaissance faciale/plaques ; en mode hybride, les flux prioritaires restent en surveillance permanente tandis que les flux secondaires tournent en pool, conciliant ciblage et couverture globale. Progression en temps réel, archivage automatique des captures, lancement en un clic de sessions de patrouille sur des centaines de caméras depuis l'écran partagé ou le catalogue — « moins de connexions, plus de couverture, détection rapide », pour passer d'une surveillance manuelle écran par écran à une patrouille automatisée intelligente</li>
  <li><strong>Tableau de bord unifié de surveillance et d'alerte algorithmique cloud-bord-périphérique</strong> : Fournit un tableau de bord unifié de surveillance et d'alerte algorithmique à intégration cloud-bord-périphérique, affichant en temps réel les informations clés telles que l'état des appareils, l'exécution des tâches algorithmiques, les statistiques d'événements d'alerte, les résultats d'analyse des flux vidéo, etc. Prend en charge la visualisation de données multidimensionnelles, réalisant une surveillance et une gestion unifiées du cloud, du bord et des périphériques, offrant aux décideurs un centre de commande de surveillance intelligent avec une vue globale.</li>
  <li><strong>Reconnaissance faciale et gestion de la base de visages</strong> : Prend en charge l'activation flexible de la reconnaissance faciale dans les tâches caméra, avec gestion de la base de visages et des caractéristiques faciales — ajout, consultation, mise à jour, suppression et recherche efficace des échantillons/caractéristiques. Prend en charge la comparaison faciale et la recherche d'identité sur les images capturées, tout en enregistrant de façon complète les résultats de correspondance, les captures, la localisation de la caméra et le contexte de l'appareil, afin de faciliter le suivi de trajectoire des personnes, l'investigation de sécurité et l'analyse statistique multidimensionnelle.</li>
  <li><strong>Reconnaissance de plaques d'immatriculation et gestion de base de plaques</strong> : Activez la reconnaissance de plaques en un clic dans les tâches de surveillance. Le système lit automatiquement les plaques des véhicules en passage et les compare en temps réel à vos bases de plaques. Gérez librement listes blanches, listes noires et étiquettes métier ; déclenchez des alertes instantanées lorsqu'un véhicule correspond aux règles — contrôle d'accès aux entrées/sorties, surveillance de véhicules ciblés, gestion visiteurs/véhicules enregistrés. Enregistre automatiquement les nouvelles plaques détectées et conserve l'historique complet des captures et correspondances pour les recherches a posteriori, la vérification de trajets et la conservation de preuves. La reconnaissance s'exécute en parallèle de l'analyse vidéo existante sans affecter la stabilité ni la réactivité de la surveillance et des alertes</li>
  <li><strong>Dessin de régions de détection d'appareils</strong> : Fournit un outil visuel de dessin de régions de détection d'appareils, prend en charge le dessin de régions de détection rectangulaires et polygonales sur les images instantanées des appareils, prend en charge la configuration flexible d'association entre les régions et les modèles algorithmiques, prend en charge la gestion visuelle, l'édition et la suppression des régions, prend en charge les raccourcis clavier pour améliorer l'efficacité du dessin, permettant une configuration précise de la détection de régions et fournissant des définitions précises de la plage de détection pour les tâches algorithmiques.</li>
  <li><strong>Mécanisme d'alerte liée intelligente</strong> : Prend en charge un mécanisme de triple liaison entre les régions de détection, les périodes de défense et les alertes d'événements. Le système détermine intelligemment si un événement détecté satisfait simultanément la plage de région de détection spécifiée, se trouve dans la période de défense et correspond au type d'alerte d'événement. Les alertes ne sont déclenchées que lorsque les trois conditions sont simultanément remplies, réalisant un filtrage conditionnel spatio-temporel précis, réduisant considérablement les taux de faux positifs et améliorant la précision et la praticité du système d'alerte.</li>
  <li><strong>Gestion de caméras à grande échelle</strong> : Prend en charge la connexion de centaines de caméras, fournissant des services complets pour la collecte, l'annotation, l'entraînement, le raisonnement, l'exportation, l'analyse, l'alerte, l'enregistrement, le stockage et le déploiement.</li>
  <li><strong>Gestion des tâches algorithmiques</strong> : Prend en charge la création et la gestion de tâches en temps réel, de capture et de patrouille. Chaque tâche peut être liée de manière flexible à un extracteur d'images et un trieur pour une extraction précise des images vidéo et un tri des résultats.
    <ul style="margin: 5px 0; padding-left: 20px;">
            <li><strong>Tâches algorithmiques en temps réel</strong> : Analyse live RTSP/RTMP ; backend par défaut <code>executor=cpp</code> (démarre <strong>RUNTIME</strong>, push AI à cadres + alertes/heartbeats), chemin <code>python</code> de compatibilité optionnel</li>
      <li><strong>Tâches algorithmiques de capture d'images</strong> : Analyse d'images capturées ; peut aussi utiliser <code>executor=cpp</code> (RUNTIME SnapScheduler / Cron)</li>
      <li><strong>Tâches algorithmiques de patrouille</strong> : Rotation multi-flux / pool ; peut aussi utiliser <code>executor=cpp</code> (RUNTIME PatrolScheduler)</li>
    </ul>
  </li>
  <li><strong>Annotation de jeux de données et gestion multi-formats</strong> : Fournit un espace de travail d'annotation d'images visuel, prenant en charge l'annotation par rectangles et polygones, la gestion des catégories et le suivi de progression ; prend en charge l'importation et l'exportation flexibles des formats de jeux de données courants (YOLO, COCO, ImageFolder, etc.), avec intégration aux jeux de données sur plateforme cloud pour l'importation en un clic et l'exportation synchronisée, assurant la continuité du pipeline complet : collecte de données, annotation, entraînement et déploiement.</li>
  <li><strong>Entraînement multi-GPU, reprise depuis point de contrôle et déploiement côté nœud</strong> : Surmonte les goulots d'étranglement de l'entraînement — « GPU présents mais inutilisés, tâches difficilement maîtrisables, résultats perdus en cas d'interruption » — en reliant de façon systémique l'exploitation multi-GPU, l'ordonnancement contrôlable des tâches et le déploiement côté nœud, pour que la puissance GPU sur site soit réellement exploitable et que les jobs d'entraînement soient réellement maîtrisables. La plateforme détecte et planifie automatiquement l'ensemble des GPU serveur ; l'utilisateur peut choisir une ou plusieurs cartes sur la page d'entraînement. Compatible avec de nombreux formats de jeux de données courants, elle prend en charge le téléversement de jeux locaux volumineux et conserve les données d'origine après un échec pour une nouvelle tentative rapide. La progression est entièrement visible, les tâches peuvent être arrêtées et reprises ; les ordonnanceurs locaux et distants se rétractent aussi rapidement en cas d'échec avec un retour clair, pour une boucle « entraîner — publier — utiliser » plus fluide et fiable.</li>
  <li><strong>Redirection de flux</strong> : Regarder le live caméra sans activer l’IA ; push par lots et création auto des tâches canaux NVR prêts à l’emploi. Chemin par défaut <strong>RUNTIME</strong> haute performance — « remplir le mur d’abord, IA sur les canaux clés » ; sites particuliers : mode compatibilité Python/FFmpeg</li>
  <li><strong>Détection GPU, répartition de charge et coopération multi-GPU</strong> : La plateforme détecte les GPU disponibles et alloue intelligemment l'encodage/décodage vidéo et l'inférence algorithmique selon la charge en temps réel de chaque carte, avec exécution parallèle sur plusieurs GPU lorsque c'est pertinent, afin d'augmenter le débit multi-flux et l'utilisation des ressources tout en préservant la stabilité et la coordination encodage–inférence en configuration multi-cartes.</li>
  <li><strong>Transport intelligent et tirage de flux hautement fiable</strong> : Sur les chemins RTSP et assimilés, le système peut choisir automatiquement le mode de transport adapté au scénario pour concilier latence et stabilité. En cas d'écrans gris, d'erreurs de décodage ou de blocage d'image, une reconnexion et une restauration de liaison sont déclenchées automatiquement afin de limiter l'impact des artefacts prolongés ou du gel d'image sur l'activité.</li>
  <li><strong>Double voie vision et jugement</strong> : Séparer « mur / split en image brute » et « résultats algo » — côté permanence, clarté et fluidité d’abord ; côté jugement, cadres en sortie indépendante, sans se voler la bande passante. Une même caméra peut garder live et analyse ; l’échelle des canaux n’oblige plus à choisir entre « voir clair » et « analyser assez »</li>
  <li><strong>Raisonnement en cluster de services de modèles</strong> : Prend en charge un cluster distribué de services de raisonnement de modèles, réalisant un équilibrage de charge intelligent, une bascule automatique en cas de défaillance et une haute disponibilité, améliorant considérablement le débit de raisonnement et la stabilité du système.</li>
  <li><strong>Gestion des plages horaires de surveillance</strong> : Prend en charge deux stratégies de surveillance : mode de surveillance complète et mode de surveillance partielle. Permet de configurer de manière flexible les règles de surveillance pour différentes périodes, réalisant une surveillance et des alertes intelligentes et précises selon les horaires.</li>
  <li><strong>OCR et reconnaissance vocale</strong> : Fournit une reconnaissance de texte haute précision et la conversion de la parole en texte, avec prise en charge multilingue.</li>
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

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0 8px 0;">
Beaucoup de projets réduisent l'IoT à un « registre d'appareils + relais de messages » : on se connecte, mais on ne gouverne pas ; on remonte des données, mais on ne déclenche rien ; on alerte, mais on ne voit pas le terrain ; on a des chiffres, mais pas d'écran ni de synoptique de processus. EasyAIoT positionne l'IoT comme le nerf d'exécution de la boucle <strong>perception — compréhension — décision — exécution</strong> : capteurs et actionneurs fournissent les « chiffres », caméras et IA fournissent les « images », grands écrans de visualisation et synoptiques de processus Web transforment les « chiffres » en situation de commandement, règles et ombres tressent le tout en actions métier opérables — pour que la plateforme ne se contente pas de « voir », mais sache aussi « afficher en écran, comprendre le processus, gouverner, piloter juste et scaler ».
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Gestion de la visualisation</strong> : Si points de mesure, alertes et indicateurs métier restent dans des listes et des messages, la direction ne voit pas l'ensemble, la garde ne lit pas clairement et les rapports exigent encore des PPT — la valeur des données reste bloquée à « on collecte mais on n'affiche pas ». La plateforme regroupe projets de visualisation, centre de modèles, bibliothèque de ressources, sources de données et déploiement de services : glisser-déposer des données IoT pour composer des grands écrans opérables de situation de campus, KPI de ligne, exploitation d'équipements, etc. ; brouillon modifiable, version mature publiable, publication diffusable — l'IoT passe de « des chiffres en coulisse » à « un écran en façade », sans outil de grand écran externe pour le commandement et la présentation</li>
  <li><strong>Cycle de vie complet des projets de visualisation</strong> : Si les grands écrans vivent sur des PC personnels et des liens temporaires, les passations se désorganisent, les versions se perdent et la mise en production devient conflictuelle. La plateforme gère de bout en bout la création, l'édition, l'aperçu, la publication et la mise hors ligne ; vues tableau/carte pour inventorier ; publiés et non publiés distinguables d'un coup d'œil — qui travaille, où en est-on, peut-on projeter : état de projet traçable, transmissible et acceptable ; « faire un écran » devient un actif de livraison opérable</li>
  <li><strong>Centre de modèles de visualisation</strong> : Repartir d'une toile vierge à chaque projet allonge forcément délais de conception et d'intégration. Des modèles matures — vue d'ensemble de campus, situation d'usine, tableau de bord d'équipements — se capitalisent et se réutilisent ; nouveau projet en un clic puis ajustements — moins de dessin from scratch pour des scénarios similaires, PoC et copies multi-projets plus rapides et homogènes ; « savoir le faire une fois » devient « livrer plusieurs fois »</li>
  <li><strong>Gouvernance des ressources et sources de données de visualisation</strong> : Icônes, fonds et vidéos cachés par projet, interfaces de données réécrites écran par écran — styles incohérents et champs qui ne correspondent plus. Bibliothèque centralisée d'actifs visuels réutilisables ; sources de données raccordées uniformément aux appareils et interfaces métier — même style, même définition de champs pour plusieurs grands écrans ; modifier une fois profite à plusieurs, moins de construction en double et de disputes sur les définitions</li>
  <li><strong>Publication de visualisation et déploiement de services</strong> : Un grand écran terminé mais non diffusable reste inutile. Après validation, associer un déploiement de service et diffuser selon le scénario — centre de commandement, salle de garde ou vitrine externe ; aperçu et diffusion officielle sur le même projet — passage explicite de « mode édition » à « mode garde » ; acceptation et astreinte quotidienne sans liens temporaires ni accords verbaux</li>
  <li><strong>Gestion des synoptiques de processus</strong> : Sur le terrain industriel et tertiaire, la crainte est « plein de valeurs, processus illisible » — compteurs, vannes, niveaux de cuve ont des lectures, mais la garde ne les relie ni aux conduites ni aux étapes ; les anomalies se devinent à l'oral et à l'expérience. La plateforme propose des synoptiques de processus Web : points de mesure liés à des vues d'ensemble d'usine d'eau, tableaux de ligne, réseaux d'usine, surveillance électrique de salle de distribution ; édition et aperçu au même endroit, publication prête pour la garde — les « chiffres » retournent sur le « schéma », l'état du processus se lit d'un coup d'œil ; la garde passe de feuilleter des tableaux à juger et agir sur le synoptique</li>
  <li><strong>Surveillance et contrôle limité en temps réel sur synoptique de processus</strong> : Une liste seule « voit les points, pas le flux » — localisation lente, passation difficile, formation au petit bonheur. L'exécution du synoptique anime cuves, vannes, moteurs et interrupteurs ; tendances et états se rafraîchissent sur le même écran ; démarrage/arrêt, reset, etc. depuis le synoptique si besoin — les nouveaux prennent en main plus vite, l'équipe suivante voit la même image ; l'anomalie passe de « trouver le point » à « lire le processus » — le terrain industriel entre vraiment dans une exploitation quotidienne surveillable, transmissible et extensible</li>
  <li><strong>Gestion des modèles de produit</strong> : Le coût le plus élevé de l'IoT n'est souvent pas l'achat d'appareils, mais de reconfigurer une fiche à chaque nouvelle classe. La plateforme prend le produit comme modèle pour des appareils similaires — création, activation/arrêt, recherche et vues tableau/carte ; scénario, fabricant et modèle se configurent une fois — l'extension réutilise ensuite le modèle produit sans tout remplir appareil par appareil ; une fiche pour une classe, réutilisable à grande échelle, transforme le coût d'accès d'une croissance linéaire en actif reproductible</li>
  <li><strong>Modélisation multi-types de produits</strong> : Quand coexistent terminaux directs, passerelles edge, sous-appareils de passerelle et appareils vidéo, forcer un seul chemin d'accès brouille la topologie et casse les protocoles. La plateforme crée des produits selon quatre formes — connexion directe, passerelle, sous-appareil de passerelle et vidéo — chaque morphologie garde son propre chemin — topologie non mélangée, protocoles non mal câblés, squelette produit correct pour une gouvernance à l'échelle</li>
  <li><strong>Protocole d'accès et authentification au niveau produit</strong> : Negocier protocole et auth appareil par appareil est le foyer des retouches d'intégration. Au niveau produit, on fige une fois protocole (MQTT / TCP / HTTP / Modbus-TCP / Modbus-RTU / OPC UA), format de données, mode d'authentification et stratégie de chiffrement/déchiffrement ; les appareils enfants héritent automatiquement du même contrat — plus d'accords auth/format au cas par cas ; la norme d'accès passe du « oral transmis » au « contrat héritables au niveau produit »</li>
  <li><strong>Accès Ethernet industriel Modbus-TCP</strong> : Pour compteurs, PLC, variateurs côté Ethernet, la plateforme intègre une capacité d'acquisition Modbus-TCP maître — configurer les paramètres d'accès et les points de mesure au niveau produit/appareil suffit pour la mise en service ; les lectures alimentent automatiquement l'ombre d'appareil et l'état en ligne, les écritures et le downlink de propriétés sont reliés — les points industriels rejoignent le modèle d'objet IoT, le moteur de règles et les alarmes dans la même boucle, sans outil d'acquisition séparé.</li>
  <li><strong>Accès terrain série Modbus-RTU</strong> : Beaucoup d'instruments restent sur RS-485 ; si seul le passage par passerelle TCP est possible, coûts et points de panne doublent. La plateforme prend en charge l'acquisition Modbus-RTU série maître, adaptée aux ports virtuels et réels — les appareils bus sont aussi intégrés à la gouvernance unifiée et au contrôle montée/descente, comblant le vide « Ethernet inaccessible, série non gérée ».</li>
  <li><strong>Accès interconnectivité industrielle OPC UA</strong> : Pour les scénarios d'interconnexion industrielle moderne et de systèmes de supervision, la plateforme prend en charge l'accès client OPC UA avec configuration d'abonnement/lecture/écriture — les modèles d'appareils complexes peuvent être mappés en propriétés du modèle d'objet plateforme ; acquisition montante et écriture descendante s'intègrent à l'ombre d'appareil, aux chaînes de règles et aux notifications — les actifs OPC UA entrent dans un AIoT « visible, contrôlable, interconnectable ».</li>
  <li><strong>Définition des propriétés du modèle d'objet</strong> : Si écrans, règles et alertes inventent chacun leurs noms de points, ils finissent par ne plus se comprendre. La plateforme fixe d'abord les points reportables/lisibles-écritables, modèles standard ou personnalisés ; brouillon puis publication — écrans, règles et alertes partagent un même jeu de champs ; « ce que l'on peut observer » a une sémantique unifiée, et les retouches dues aux noms divergents disparaissent à la racine</li>
  <li><strong>Définition des services du modèle d'objet</strong> : Si chaque démarrage/arrêt ou reset produit une API ponctuelle, le plan de contrôle se fragmente. La plateforme formalise en contrat les services invocables à distance avec paramètres d'entrée/sortie ; brouillon puis publication — « ce que l'on peut faire à distance » se remplit selon le contrat, sans empiler d'API jetables ; la capacité de contrôle devient réutilisable et auditable</li>
  <li><strong>Définition des événements du modèle d'objet</strong> : Sans accord préalable sur les événements métier remontés, le vocabulaire d'alerte diverge. La plateforme convient d'abord des types d'événements ; après publication du brouillon, ils s'appliquent uniformément — journaux d'événements et déclencheurs de règles partagent la même sémantique ; « ce qui peut arriver » a un langage commun, les alertes ne se contredisent plus</li>
  <li><strong>Contrôle de publication du modèle d'objet</strong> : Pousser une modification de modèle directement sur les appareils en ligne peut impacter toute une flotte d'un faux geste. Les changements partent d'abord en brouillon et n'atteignent le côté appareil qu'après confirmation et publication — tampon avant impact ; les changements non validés ne frappent pas le terrain en ligne, risque d'erreur nettement réduit</li>
  <li><strong>Adaptation par scripts de protocole</strong> : Le plus dur sur le terrain n'est pas le MQTT standard, mais les trames propriétaires et les boîtes noires « débogables seulement en local ». Les trames standard marchent hors boîte ; pour un protocole privé, on écrit l'encodage/décodage montée/descente avec modèles, validation, débogage immédiat et rechargement à chaud — l'intégration passe de « modifier le firmware / attendre le fournisseur » à « configurer un script, effet à chaud » ; les stocks multi-fournisseurs rejoignent le modèle unifié sans changer le firmware</li>
  <li><strong>Guide d'accès produit</strong> : Si l'intégration des nouveaux repose sur l'oral des experts sur site, la cadence de livraison est bloquée sur les personnes. La fiche produit intègre paramètres d'intégration, authentification, messages et notes d'acceptance — suivre la page suffit pour accepter — chaque produit livre son playbook standard ; moins de dépendance à l'oral, PoC et acceptance plus rapides et stables</li>
  <li><strong>Vue des appareils liés au produit</strong> : Ops et acceptance se disputent souvent « combien cette flotte couvre-t-elle vraiment, quel est le taux en ligne ? ». Ouvrir le produit montre la liste des appareils et leur état en ligne — taux en ligne et couverture d'un coup d'œil ; ops et acceptance ont chacun leur périmètre, frontières de responsabilité claires</li>
  <li><strong>Gestion des fiches appareils</strong> : Des appareils éparpillés dans tableurs, chats et mémoires terrain rendent inventaire et transfert incontrôlables. CRUD complet, recherche par produit/identifiant/état en ligne, bascule tableau/carte — les terminaux dispersés deviennent un registre searchable ; inventaire, transfert et extension passent par une seule entrée</li>
  <li><strong>État en ligne et d'activation</strong> : Les appareils problématiques se noient dans « tous les appareils », la garde ne peut que fouiller à l'aveugle. Listes et détails affichent connexion, activation, heure d'activation et dernière mise en ligne — hors ligne et non activés remontent en priorité ; l'énergie ops se concentre d'abord sur les vrais anomalies</li>
  <li><strong>Enregistrement d'appareils par produit</strong> : Resélectionner protocole et auth à chaque extension est le plus grand frottement du go-live à l'échelle. À la création, lier le produit parent hérite protocole et scénario — l'enregistrement attache le bon modèle ; scaler en clonant le produit, sans rechoisir protocole ni re-remplir l'auth</li>
  <li><strong>Configuration d'accès collecte industrielle</strong> : Si compteurs et capteurs exigent encore un outil de collecte séparé, le terrain vit en double système. À l'enregistrement d'un appareil de collecte industrielle, configurer hôte, points et période — les points terrain sont archivés une fois ; plus besoin de basculer vers un autre outil, collecte industrielle et gouvernance plateforme en un geste</li>
  <li><strong>Fiche d'informations de base</strong> : Remplacement, responsabilité et rapprochement qui reposent sur un « qui est-ce ? » oral cassent la chaîne de responsabilité. Nom, identifiant, SN, produit, version, IP et autres champs un-appareil-une-fiche — ouvrir la fiche confirme l'identité ; moins de confirmation orale et de chasse sur site</li>
  <li><strong>Guide d'accès appareil</strong> : Si l'intégration terrain reste une chasse aux gros documents et aux experts, le cycle de mise en service s'allonge. Par type : commandes recommandées, paramètres d'intégration, auth, messages et notes d'acceptance ; commandes copiables après modification des paramètres — l'intégration passe de la doc à l'acceptance par copie de commandes ; go-live et PoC plus serrés</li>
  <li><strong>État d'exécution en temps réel</strong> : Si la garde doit se connecter à l'appareil et lire les trames brutes pour juger un point, le coût de surveillance explose. Les valeurs live des propriétés s'étalent selon le modèle d'objet ; vues tableau/carte et actualisation — sans se connecter ni lire le brut, juger d'un coup d'œil si les points clés sont normaux maintenant</li>
  <li><strong>Prédiction de données flottantes des capteurs</strong> : Si les points clés ne se consultent qu'a posteriori sur des courbes historiques, les anomalies restent souvent invisibles jusqu'au franchissement. La plateforme prédit les tendances des propriétés flottantes des capteurs, transformant les lectures passées en trajectoires anticipées — l'exploitation passe de « regarder les chiffres après coup » à « anticiper », pour gagner du temps d'action</li>
  <li><strong>Seuils des attributs d'état d'exécution</strong> : Si les frontières de santé vivent dans le code ou des accords oraux, chaque nouveau modèle ou scénario impose une reprise. Configurer des seuils haut/bas des attributs d'état selon le modèle d'objet — frontières définissables, réutilisables et affinables ; la « plage normale » de l'appareil devient un actif gouvernable, plus un savoir tribal dispersé</li>
  <li><strong>Alertes et règles de seuil</strong> : Des seuils sans alerte ni liaison ne sont que décoratifs. Le dépassement déclenche automatiquement une alerte et peut alimenter des règles d'action — « savoir dès le franchissement, pouvoir agir dès qu'on sait », pour boucler les frontières de santé en exploitation</li>
  <li><strong>Maîtrise sur un écran des sous-appareils liés à l'équipement central</strong> : Si la santé des subordonnés se consulte appareil par appareil, inspection et réponse aux incidents retardent toujours. Depuis l'équipement central, parcourir d'un coup d'œil l'état d'exécution des sous-appareils liés — sans bascule appareil par appareil ; inspection terrain et localisation d'anomalies nettement plus rapides, pour que le côté équipements boucle vraiment « voir les chiffres, gouverner les bornes, lever les alertes et saisir le global »</li>
  <li><strong>Comparaison d'ombre d'appareil</strong> : Le pire du diagnostic classique est de ne pas distinguer « ce qu'on veut » et « ce qui est ». État reporté, état désiré et écarts côte à côte, JSON complet conservé — le diagnostic passe du guesswork à la comparaison ; cohérence désir/réel d'un coup d'œil</li>
  <li><strong>Envoi des propriétés désirées</strong> : Se déplacer pour un seul paramètre est le gaspillage typique de l'ops à l'échelle. Modifier en lot les valeurs désirées des propriétés écrites et pousser en un clic ; suivre en cours/succès/échec — réglages à distance avec accusé de réception ; plus de déplacement pour un paramètre, moins de sorties inutiles</li>
  <li><strong>Invocation de services du modèle d'objet</strong> : Démarrer/arrêter ou reset sans confirmer l'exécution ne laisse que la réconciliation orale. Remplir les paramètres des services publiés et invoquer ; suivre les accusés — après l'ordre, confirmer l'exécution ; la disposition devient auditable, du « on a dit que c'était contrôlé » à une boucle avec réception</li>
  <li><strong>File d'attente hors ligne</strong> : Sur réseau faible ou brève déconnexion, les commandes perdues obligent à tout refaire. Hors ligne temporairement, les commandes écrivent l'ombre désirée ; à la reconnexion, tirage ou réception selon le protocole — l'intention de contrôle survit au jitter ; rattrapage à la reprise, une opération en moins à refaire</li>
  <li><strong>Contrôle proxy sous-appareils via passerelle</strong> : Exiger que chaque terminal edge se connecte directement à la plateforme fait exploser complexité d'accès et gestion des certificats. Le contrôle des sous-appareils passe par la passerelle parente — les terminaux edge sont télécommandés sans lien direct ; complexité d'accès réduite, la passerelle devient vraiment une face d'agrégation opérable</li>
  <li><strong>Caméras liées</strong> : Une alerte capteur sans vue du terrain force la garde à « écouter des chiffres et deviner ». Les appareils IoT peuvent lier des caméras du catalogue ; points de mesure et points vidéo se correspondent — dès l'anomalie, savoir quelle voie ouvrir ; du « un chiffre remonté » au « une image trouvée »</li>
  <li><strong>Supervision multi-écrans et liaison IA</strong> : Différence clé d'EasyAIoT face à l'IoT pur — l'IoT pur « voit les chiffres sans le terrain », la vidéo pure « voit le terrain sans piloter les appareils ». Dans l'invocation de fonctions, basculer en aperçu 1/4/9 des caméras liées et lancer l'analyse IA — paramétrer et commander en regardant le site ; « chiffres » et « images » vérifiés et traités sur le même écran ; moins de bascules de système, moins de ratés, vraie valeur de la fusion AI + IoT</li>
  <li><strong>Journaux d'événements</strong> : Un pop-up d'alerte disparaît, la rétrospective ne repose plus que sur la mémoire et les disputes. Info/avertissement/erreur remontés sont agrégés ; filtre par type, nom et heure — la rétrospective lit le flux d'événements bruts ; « que s'est-il passé sur site » a des preuves, pas seulement un flash</li>
  <li><strong>Journaux de commandes</strong> : Le pire de l'intégration est le « he-said-she-said » : la commande est-elle partie, l'appareil l'a-t-il acceptée ? En cours/succès/échec des réglages de propriétés et appels de services laissent une trace complète — fin de la réconciliation orale ; la chaîne de commande est vérifiable et imputable</li>
  <li><strong>Journaux d'appareils</strong> : Localiser firmware et anomalies métier en se connectant pour lire des fichiers locaux bloque l'efficacité derrière réseau et droits terrain. Les journaux multi-niveaux côté appareil remontent au cloud ; recherche par mot-clé et heure — localiser l'anomalie dans le cloud, sans se reconnecter pour fouiller les logs locaux</li>
  <li><strong>Liaison sous-appareils de passerelle</strong> : En industrie et bâtiment, « une passerelle porte des dizaines ou des centaines de sous-appareils » ; une topologie orale rend extension et isolation de panne incontrôlables. Liaison/déliaison en lot des sous-appareils — qui accroche qui est limpide ; frontières nettes lors d'extension, remplacement de passerelle ou isolation</li>
  <li><strong>Inventaire des capacités Topic</strong> : Si R&D et intégration ont chacun leur contrat de canaux, l'intégration se retouche pour divergences. Par appareil : canaux montée/descente config, ombre, propriétés, services, événements, OTA, sync d'horloge, etc. — s'intégrer contre le même catalogue ; moins de retouches liées aux contrats de canal divergents</li>
  <li><strong>Gestion des paquets OTA</strong> : Copier correctifs et firmwares clé USB par USB rend l'upgrade à l'échelle quasi impossible. Upload et archivage centralisés des paquets logiciels/firmware avec version, téléchargement, édition, suppression et double vue — correctifs et firmwares réutilisables au même endroit ; plus de copie de média appareil par appareil, le firmware devient un actif de livraison gouvernable</li>
  <li><strong>Stratégie de mise à niveau OTA</strong> : Manquer une montée laisse des failles ; monter n'importe comment crée des risques de compatibilité — dilemme classique de l'ops à l'échelle. Marquer les versions critiques ; mode forcé ou non forcé — les correctifs urgents atteignent la cible, les versions courantes ne se montent pas en chaos ; risques de manques et de compatibilité sous contrôle</li>
  <li><strong>Gestion des chaînes de règles</strong> : Des règles de liaison éparpillées, impossibles à activer/arrêter centralement, multiplient faux déclenchements et chaînes dormantes. Création, activation/arrêt, suppression en lot ; gestion liste/carte — interrupteur central des liaisons métier ; règles inutiles coupées à tout moment, moins de faux déclenchements</li>
  <li><strong>Orchestration visuelle des chaînes de règles</strong> : Le métier terrain change chaque jour — seuils à ajuster, liaisons à ajouter — attendre un développement figé retarde toujours d'un temps. Sur le canevas en chaîne, relier flux de données, conditions et actions aval selon l'intention — un changement de scénario se dépose en glisser-déposer ; plus d'attente de sprint, « que faire des données une fois entrées » se configure par le métier</li>
  <li><strong>Import/export de règles</strong> : Des règles matures qu'on ne peut pas emporter obligent chaque projet à tout réécrire. Import/export — migration multi-environnements et réutilisation multi-projets en partant avec ; les règles matures deviennent des actifs de livraison reproductibles</li>
  <li><strong>Configuration des messages</strong> : Changer de canal ou de compte en touchant encore le code métier bloque l'ops derrière le développement. Canaux de notification et réglages de base maintenus au même endroit — changer de canal ou de compte ne touche que la config, pas le code métier</li>
  <li><strong>Modèles de messages</strong> : Des formulations d'alerte improvisées se trompent et divergent. E-mail, SMS, Enterprise WeChat, DingTalk, Feishu, Webhook, etc. ont chacun leurs modèles — rédaction une fois, réutilisation partout ; formulations unifiées, moins d'erreurs de collage improvisé</li>
  <li><strong>Envoi de messages</strong> : La détection la plus juste et l'événement le plus complet valent zéro s'ils restent bloqués dans le système à attendre qu'on les ouvre. Créer des tâches de push par canal ; tester puis démarrer — alertes et événements métier atterrissent dans les outils quotidiens des responsables ; plus bloqués dans le système</li>
  <li><strong>Historique des envois</strong> : Sans trace d'émission ni d'atteinte, audit et optimisation ne sont que des conjectures. Revoir les enregistrements de push par canal — émis ou non, atteint ou non, preuves à l'appui ; audit et optimisation de la stratégie de touch ont un socle</li>
  <li><strong>Utilisateurs et groupes de notification</strong> : Diffuser les alertes critiques à tout le monde crée de la fatigue ; ne pas atteindre les bonnes personnes crée des manques. Maintenir utilisateurs et groupes pour un ciblage précis par rôle/équipe — les bonnes personnes reçoivent ; moins de fatigue d'alerte « à tous » ; la boucle « perception — jugement — notification — disposition » se ferme vraiment jusqu'à la personne</li>
  <li><strong>TRANSFORM — flux métier multidirectionnel</strong> : Si alertes, événements appareil et résultats métier restent enfermés dans EasyAIoT, brancher MES / ERP / CRM / WMS impose encore des API sur mesure par projet — délais et retouches explosent. TRANSFORM transforme « à qui envoyer, selon quelles règles, comment mapper les champs, est-ce arrivé » en capacité configurable : destinations, règles de transfert et modèles de mapping une fois, puis réutilisation ; la livraison est monitorable et rejouable — l'intégration multi-systèmes passe de « une API custom par partenaire » à « brancher par contrat, accepter par trace », pour que les données plateforme entrent vraiment dans la boucle métier du client</li>
</ul>

#### 📱 APP mobile

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Accès multi-canal</strong> : Disponible sur téléphone, mini-programme et App — l'exploitation et la gestion ne sont plus liées au poste de travail ; agir sur le terrain en temps réel</li>
  <li><strong>Parité des capacités</strong> : Les mêmes fonctions métier que la console PC ; changez d'appareil sans perdre le contrôle</li>
  <li><strong>Gestion des appareils</strong> : Tous les modes d'accès unifiés ; listes et canaux en un coup d'œil, aperçu en direct en un clic — restez informé en tournée</li>
  <li><strong>Relais de flux</strong> : Créez et arrêtez le relais à tout moment ; suivez nœuds et canaux ; le multi-canal brut peut monter efficacement à l’écran — même hors du bureau</li>
  <li><strong>Tâches algorithmiques</strong> : Démarrez et arrêtez les tâches temps réel et instantané en mobilité ; suivez les résultats sans attendre le retour au bureau</li>
  <li><strong>Centre d'alertes</strong> : Recherchez les alertes instantanément ; captures et enregistrements en un clic — vérifiez et suivez en astreinte mobile</li>
  <li><strong>Gestion des modèles</strong> : Statut de déploiement visible d'un coup d'œil ; progressez en toute confiance</li>
  <li><strong>Inférence de modèles</strong> : Envoyez une image sur le terrain et obtenez le résultat immédiatement — contrôles ponctuels sans retourner au PC</li>
  <li><strong>Entraînement de modèles</strong> : Suivez la progression à tout moment ; arrêtez à distance si besoin pour éviter le gaspillage de calcul</li>
  <li><strong>Centre personnel</strong> : Compte, locataire et préférences centralisés — pratique sur tous les terminaux</li>
  <li><strong>Visionnage fluide</strong> : Flux en direct et enregistrements d'alerte fluides sur mobile — faible latence, sans saccades, expérience d'astreinte préservée</li>
  <li><strong>Connexion continue</strong> : Session maintenue automatiquement, moins de reconnexions — le contrôle intelligent cloud-bord-périphérique atteint téléphone et mini-programme</li>
</ul>

### 📦 Modèles IA intégrés

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
La plateforme est prête à l'emploi, avec plusieurs modèles pré-entraînés intégrés pour la surveillance de sécurité, les sites industriels, les transports intelligents et d'autres scénarios. Sélectionnez-les directement dans les tâches d'algorithme pour un déploiement et une inférence rapides, sans formation à partir de zéro pour couvrir les besoins courants de détection visuelle.
</p>

| Nom du modèle | Format d'inférence | Modèle de base | Capacité |
| :-- | :--: | :--: | :-- |
| Modèle casque de sécurité | ONNX | YOLOv8 | Détecter si les travailleurs portent un casque de sécurité |
| Modèle sommeil en service | PyTorch | YOLOv8 | Détecter le sommeil en service, l'abandon de poste et autres comportements anormaux |
| Modèle détection de personnes | PyTorch | YOLOv8 | Détection humaine générale pour identifier et localiser les personnes dans l'image |
| Modèle de plaques | ONNX | YOLOv8 | Reconnaître les informations des plaques d'immatriculation |
| Modèle gilet réfléchissant | PyTorch | YOLOv8 | Détecter si les travailleurs portent un gilet réfléchissant |
| Modèle flamme | PyTorch | YOLOv8 | Détecter les flammes nues et les risques d'incendie |
| Modèle détection de tabagisme | PyTorch | YOLOv8 | Détecter le comportement de tabagisme |
| Modèle appel téléphonique | ONNX | YOLOv8 | Détecter les appels téléphoniques et l'utilisation du téléphone mobile |
| Modèle eau sur route | ONNX | YOLOv8 | Détecter l'accumulation d'eau sur la route et les inondations de surface |
| Modèle masque facial | ONNX | YOLOv8 | Détecter si les personnes portent correctement un masque |
| Modèle détection de chute | ONNX | YOLOv8 | Détecter les chutes et autres postures anormales |
| Modèle détection de visage | ONNX | YOLOv8 | Détecter les positions des visages dans l'image pour soutenir les flux de reconnaissance faciale |

### 💡 Philosophie technique

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Nous pensons qu'aucun langage de programmation n'excelle en toute chose, mais grâce à une intégration profonde de cinq langages de programmation, EasyAIoT exploite leurs avantages respectifs pour construire un écosystème technique puissant.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Java excelle pour construire une architecture de plateforme stable et fiable, mais convient mal à la programmation réseau et à l'IA ; Python excelle en programmation réseau et en algorithmes d'IA, mais bute sur le GIL et le coût multi-processus dès qu’il s’agit d’exécution frame haute densité / basse latence ; C++ excelle pour l'exécution haute performance, mais convient mal à l'architecture de plateforme et à l’orchestration algorithmique — la plateforme fait donc descendre <strong>pull/décodage, inférence, push à cadres et relais multi-canal brut</strong> dans <strong>RUNTIME</strong>, tandis que WEB/VIDEO gardent orchestration et surface métier. Go excelle en réseau à haute concurrence et en implémentation de protocoles, mais convient mal au plan de contrôle plateforme et aux algorithmes d'IA ; TypeScript excelle pour des interactions front-end complexes et des interfaces industrialisées à typage sûr, mais convient mal au calcul backend haute performance et à l'inférence IA. EasyAIoT adopte une architecture hybride cinq-en-un, où chaque langage occupe son terrain de jeu — une plateforme AIoT ambitieuse à réaliser, mais extrêmement simple à utiliser.
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
EasyAIoT n'est pas vraiment un seul projet, mais plusieurs sous-projets déployables indépendamment (WEB, DEVICE, VIDEO, RTC, AI, etc.).
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
EasyAIoT répond activement à la stratégie de localisation, prenant pleinement en charge les matériels et systèmes d'exploitation locaux, offrant aux utilisateurs des solutions AIoT sûres et contrôlables. Le déploiement et les paquets PANEL couvrent déjà des OS locaux tels que <strong>Kylin (麒麟) / openEuler (欧拉)</strong>.
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
  <li>Les cartes de développement ordinaires peuvent assurer la veille intelligente sur site</li>
  <li>Déploiement léger sur le terrain, sans empiler de lourds stockages à chaque site</li>
  <li>Intelligence prête à l'emploi, cycle de mise en service edge raccourci</li>
  <li>Puissance de calcul déployée point par point, alertes et preuves agrégées automatiquement vers le cloud</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🖱️ Support des systèmes d'exploitation</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Compatibilité avec <strong>Kylin (麒麟) / openEuler (欧拉)</strong></li>
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
EasyAIoT comprend notamment WEB, APP, DEVICE, NODE, VIDEO, RTC, AI, RUNTIME, VISUALIZE, TRANSFORM, PANEL et SITE, avec COMPILE pour le packaging et la livraison multiplateformes :
</p>

<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50; width: 20%;">Module</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50;">Description</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Module SITE</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Entrée officielle</strong> : Site officiel indépendant pour visiteurs, intégrateurs et clients finaux — expliquer clairement l'intégration cloud-bord-périphérie, puis guider vers le téléchargement et le déploiement</li>
    <li><strong>Parcours plus court</strong> : Fonctionnalités, trois niveaux matériels, installateurs et documentation sur un même site — moins de recherche dans le dépôt et d'explications orales</li>
    <li><strong>Aide au choix de niveau</strong> : mini / standard / full pour boxes edge, caméras IA et appliances full-stack — choisir le bon niveau dès le départ</li>
    <li><strong>De l'intérêt à l'installation</strong> : Site, démo, dépôts open source et Releases forment une boucle — comprendre → essayer → télécharger → installer</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Module WEB</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Interface unifiée</strong> : Frontend de gestion avec UX cohérente</li>
    <li><strong>Assistant multi-protocole</strong> : IPC / NVR / GB28181 / RTC ; ONVIF, scan inter-sous-réseaux, RTSP, live DJI, P2P grand public</li>
    <li><strong>Accès RTC</strong> : « Connecter caméra RTC » pour <strong>Tapo / Tuya / Ring / Nest / Xiaomi / Wyze / DoorBird / GoPro / Roborock</strong> ; OAuth via WebUI go2rtc</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Module APP</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Accès multi-canal</strong> : Un seul développement, plusieurs terminaux — téléphone, mini-programme et App</li>
    <li><strong>Parité des capacités</strong> : Mêmes fonctions métier que la console PC, avec changement de locataire</li>
    <li><strong>Gestion des appareils</strong> : Caméras directes, GB28181, NVR et caméras RTC grand public unifiés ; statut en ligne, navigation des canaux et aperçu en direct en un clic</li>
    <li><strong>Relais de flux</strong> : Création/démarrage/arrêt des tâches, état des nœuds et vision multi-canal ; bascule haute performance / compatibilité selon le site</li>
    <li><strong>Tâches algorithmiques</strong> : Liste temps réel/instantané, contrôle démarrage/arrêt et statistiques de détection/trames</li>
    <li><strong>Centre d'alertes</strong> : Recherche d'alertes, aperçu des captures et relecture VOD des enregistrements d'alerte</li>
    <li><strong>Modèles & IA</strong> : Liste et statut de déploiement, atelier d'inférence d'images mobile, suivi et arrêt des tâches d'entraînement</li>
    <li><strong>Profil</strong> : Informations personnelles, sécurité du compte, FAQ, retours et paramètres de l'application</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Module DEVICE</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Gestion des appareils</strong> : Enregistrement, authentification, surveillance d'état, gestion du cycle de vie des appareils.</li>
    <li><strong>Gestion des produits</strong> : Définition de produit, gestion des modèles d'appareils, configuration des produits.</li>
    <li><strong>Support des protocoles</strong> : MQTT, TCP, HTTP, Modbus-TCP, Modbus-RTU, OPC UA et autres protocoles IoT et industriels.</li>
    <li><strong>Authentification des appareils</strong> : Enregistrement dynamique, authentification d'identité, connexion sécurisée.</li>
    <li><strong>Moteur de règles</strong> : Règles de flux de données, routage des messages, transformation des données.</li>
    <li><strong>Collecte de données</strong> : Collecte, stockage, requête et analyse des données des appareils.</li>
    <li><strong>Ordonnancement des nœuds</strong> : Gestion des nœuds de calcul/média, tests de connectivité, ordonnancement des charges de travail et allocation du pool de nœuds média.</li>
    <li><strong>Backend de visualisation</strong> : Gestion unifiée des projets grands écrans/synoptiques de processus, modèles, ressources, sources de données et déploiements de services — métadonnées de projet et capacités de publication pour l'éditeur VISUALIZE et les synoptiques de processus Web.</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Module NODE</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Agent de nœud</strong> : Agent de nœud edge/distant ; installation en un clic, rejoignant automatiquement la plateforme une fois déployé sur les serveurs cibles.</li>
    <li><strong>Remontée d'état</strong> : Heartbeats périodiques, rapportant en temps réel l'utilisation CPU, mémoire, disque, GPU et l'état des charges de travail actives.</li>
    <li><strong>Charges de travail distantes</strong> : Reçoit les commandes de déploiement/arrêt de la plateforme, lançant localement sur le nœud les services de modèles IA, tâches algorithmiques, transcodage audio-vidéo et autres charges de travail.</li>
    <li><strong>Pool de nœuds média</strong> : Prend en charge le déploiement distant des capacités de streaming sur les nœuds, avec liaison appareil–nœud média et génération d'URL de flux.</li>
    <li><strong>Rôles de nœud</strong> : Rôles compute / media / hybrid pour l'ordonnancement inter-nœuds et l'échelle élastique ; les nœuds de calcul peuvent accueillir temps réel / capture / patrouille et relais haute performance dépêchés par le centre</li>
    <li><strong>Compatible hors ligne</strong> : Empaquetage hors ligne des dépendances et mise à jour à chaud de l'Agent, adapté à l'intégration en masse de nœuds dans des environnements sans accès Internet ou à réseau restreint.</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Module VIDEO</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Traitement des flux multimédias</strong> : Prend en charge le traitement et la transmission en temps réel des flux RTSP/RTMP.</li>
    <li><strong>Accès multi-protocole</strong> : GB28181, ONVIF, scan NVR, live DJI FlightHub et caméras RTC grand public</li>
    <li><strong>API intégration RTC</strong> : <code>/register/device/rtc-live</code> — enregistrement go2rtc et appareil ; nettoyage auto à la suppression</li>
    <li><strong>Gestion des tâches algorithmiques</strong> : Temps réel / capture / patrouille ; exécution haute performance par défaut avec vues de jugement à cadres ; mode compatibilité disponible</li>
    <li><strong>Orchestration du relais de flux</strong> : Mur multi-canal brut en haute performance par défaut ; sites particuliers en compatibilité ; démarrage/arrêt et politiques suivent automatiquement pour moins de retouches manuelles</li>
    <li><strong>Extracteurs d'images et Trieurs</strong> : Prend en charge des stratégies flexibles d'extraction d'images et des mécanismes de tri des résultats. Chaque tâche peut être liée à un extracteur et un trieur indépendants.</li>
    <li><strong>Plages horaires de surveillance</strong> : Prend en charge la configuration par périodes des modes de surveillance complète et partielle.</li>
    <li><strong>Orchestration vs exécution</strong> : VIDEO gère orchestration, aperçu brut, archivage d’alertes et démarrage/arrêt ; le lourd travail va à <strong>RUNTIME</strong> (inférence et relais haute performance) — « gouverné » et « rapide » séparés, pour que canaux et latence ne soient pas freinés par l’orchestration Python</li>
    <li><strong>Prévisualisation d’acceptance</strong> : Vue côte à côte brut vs jugement pour vérifier plus vite latence et qualité des cadres sur site</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Module RTC</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>go2rtc</strong> : Basé sur <a href="https://github.com/AlexxIT/go2rtc">go2rtc</a> ; vendor via script install</li>
    <li><strong>Pont P2P neuf marques</strong> : Tapo, Tuya, Ring, Nest, Xiaomi, Wyze, DoorBird, GoPro, Roborock</li>
    <li><strong>API de gestion unifiée</strong> : Registre plateformes, construction URL, proxy REST go2rtc ; ports 6100 / 1984 / 8554</li>
    <li><strong>Chaîne VIDEO complète</strong> : P2P → RTSP → SRS → Web + IA</li>
    <li><strong>Docker tout-en-un</strong> : go2rtc + service Python ; host network pour P2P LAN</li>
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
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Module RUNTIME</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
    <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Exécution native haute performance</strong> : Un binaire porte pull, décodage, inférence ONNX, callbacks alerte/heartbeat et push à cadres ; défaut <code>executor=cpp</code> — plus de canaux par boîtier, latence plus basse, ressources plus légères que les chemins Python</li>
    <li><strong>Quatre formes terrain</strong> : Surveillance temps réel, capture planifiée, patrouille rotative et relais brut seul — choisir selon le métier pour ne pas payer le coût IA complet quand on veut seulement regarder</li>
    <li><strong>Double vue brut + jugement</strong> : Les tâches temps réel sortent par défaut un flux de détection à cadres, présenté séparément de l’aperçu brut VIDEO — les chemins ne se volent pas la bande</li>
    <li><strong>Mur multi-canal brut économe</strong> : Le relais utilise par défaut le chemin haute performance pour que « beaucoup de canaux en brut, peu d’IA » coexiste sur sites NVR</li>
    <li><strong>Alertes &amp; état vers le centre</strong> : Alertes et état d’exécution agrégés vers VIDEO pour persistance et notification ; pas de données métier empilées sur le nœud</li>
    <li><strong>Préserver le temps réel sous charge</strong> : Quand le calcul est saturé, prioriser l’image courante et la fraîcheur des alertes — éviter « plus on est chargé, plus on rate »</li>
    <li><strong>Accélération d’abord, repli sans arrêt</strong> : Utiliser l’accélérateur s’il est là ; continuer automatiquement sinon — les tâches ne s’arrêtent pas</li>
    <li><strong>Distribution en un clic</strong> : WEB « distribution de runtime métier » ou scripts d’install en lot ; l’install VIDEO du centre monte automatiquement l’exécuteur local</li>
    <li><strong>Plan d’événements MQTT</strong> : Alertes/captures/post-traitement via le bus algo EMQX ; <strong>iot-sink</strong> persiste, archive et enrichit les notifications</li>
    <li><strong>Plan de gestion heartbeat HTTP</strong> : La vivacité des tâches remonte à VIDEO ; démarrage/arrêt et table des tâches gérés par VIDEO</li>
    <li><strong>Racine média NFS</strong> : Images d’alerte et DVR SRS unifiés vers la <strong>racine média NFS partagée</strong> (<code>EASYAIOT_MEDIA_ROOT</code>, défaut <code>/mnt/easyaiot-media</code> ; repli sur <code>$HOME/easyaiot/media</code> sans sudo) ; MQTT ne transporte que les chemins ; <strong>iot-sink</strong> lit le disque et archive vers MinIO</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Module VISUALIZE</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Éditeur de grands écrans glisser-déposer</strong> : Éditeur de visualisation low-code haute performance, centré sur l'édition et l'aperçu du canevas</li>
    <li><strong>Intégration avec WEB</strong> : Création de projet, modèles, ressources, sources de données, publication et diffusion dans le menu « Visualisation » de la console ; « Ouvrir l'éditeur » bascule vers le canevas</li>
    <li><strong>Livraison de grands écrans</strong> : Graphiques, indicateurs et mise en page par glisser-déposer ; composants raccordables aux sources de données plateforme et points IoT — situation de campus, KPI de ligne, exploitation d'équipements, énergie, etc.</li>
    <li><strong>Complémentarité avec les synoptiques de processus</strong> : Grands écrans (dashboard) via ce module ; synoptiques de processus via les capacités Web de synoptique ; métadonnées de projet unifiées sous le backend de visualisation DEVICE</li>
    <li><strong>Forme de déploiement</strong> : Capacité full comme APP ; mini / standard peuvent être omis selon le matériel terrain pour alléger le déploiement edge</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Module TRANSFORM</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Flux métier multidirectionnel</strong> : Livre alertes, événements appareil et résultats métier vers MES / ERP / CRM / WMS selon contrat, franchissant le dernier kilomètre « la plateforme a des données → les systèmes métier les utilisentent »</li>
    <li><strong>Intégration configurable</strong> : Destinations, règles de transfert et mappages de champs configurés une fois et réutilisables — moins de « API sur mesure pour chaque client »</li>
    <li><strong>Livraison vérifiable</strong> : Clusters d'exécution et traces de livraison monitorables et rejouables ; l'intégration et la recette répondent à « est-ce arrivé, où ça bloque » — moins de réconciliation orale</li>
    <li><strong>Extension horizontale</strong> : Avec le trafic, étendre consommation et livraison selon le contrat métier — multi-lignes, multi-usines, multi-systèmes en parallèle</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Module PANEL</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Entrée livraison & permanence</strong> : Indépendant de la console métier : installer, réceptionner et tenir dès l'arrivée — raccourcir la recette, réduire le coût de présence et de support distant</li>
    <li><strong>Boucle le jour même</strong> : Installation par niveau via interface, progrès et résultats visibles sur place ; monter et livrer l'appliance même avant la console métier</li>
    <li><strong>Diagnostic en autonomie</strong> : Santé des conteneurs, niveau des ressources, journaux de tâches et readiness des images d'un coup d'œil — start/stop, pull et nettoyage de cache courants sans attendre les commandes développeur</li>
    <li><strong>Réutilisation multi-sites</strong> : Une même entrée pour plusieurs appliances et salles machines — PoC et livraison série partagent le même référentiel</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Packaging COMPILE</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Artefacts multiplateformes</strong> : Empaqueter PANEL et capacités associées en installateurs ou binaires pour Ubuntu / Debian, CentOS / RHEL <strong>7–9</strong> (x86 + <strong>CentOS ARM</strong>, paquets el7/el8/el9), Windows, macOS et cibles ARM / <strong>Kylin (麒麟) / openEuler (欧拉)</strong> — installation client sans compilation source sur site</li>
    <li><strong>Chaîne de livraison courte</strong> : L'intégrateur prend le paquet adapté pour déployer et mettre à jour — chemins d'install, start/stop et désinstall unifiés, moins d'écarts cross-OS</li>
    <li><strong>Associé à PANEL</strong> : Les artefacts posent directement l'entrée d'ops terrain, reliant « empaqueter » et « installer et tenir à l'arrivée » sur une même chaîne</li>
  </ul>
</td>
</tr>
</table>

## 🖥️ Avantages du déploiement multiplateforme

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT prend en charge le déploiement sur les trois principaux systèmes d'exploitation : Linux, Mac et Windows, offrant aux utilisateurs des solutions de déploiement flexibles et pratiques dans différents environnements ; avec <strong>COMPILE</strong> pour produire installateurs et binaires par OS cible, et <strong>PANEL</strong> pour l'installation sur site et la permanence quotidienne :
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🐧 Avantages du déploiement Linux</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Adapté aux environnements de production, stable et fiable, faible consommation de ressources.</li>
  <li>Prend en charge le déploiement conteneurisé Docker, démarrage de tous les services en un clic.</li>
  <li>Adaptation parfaite aux serveurs et aux appareils de calcul edge (comme les appareils ARM RK3588).</li>
  <li>Fournit des scripts d'installation automatisés complets pour simplifier le processus de déploiement.</li>
  <li>Couvre les distributions serveur mainstream : Ubuntu, CentOS/RHEL <strong>7–9</strong> (dont <strong>CentOS ARM</strong>), <strong>Kylin (麒麟) / openEuler (欧拉)</strong></li>
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
La plateforme prend en charge les tâches algorithmiques en temps réel, de capture et de patrouille : les trois peuvent utiliser par défaut la <strong>couche d’exécution haute vitesse RUNTIME</strong> (<code>executor=cpp</code>) — binaire natif pour pull longue durée, décodage, inférence YOLO et callbacks ; temps réel avec <strong>push de flux AI à cadres par défaut</strong> ; capture Cron ; patrouille multi-flux ; le relais peut aussi emprunter le même chemin haute performance pour un mur brut économe. Face au backend Python de compatibilité, RUNTIME tient mieux la densité de canaux et la basse latence. Alertes et heartbeats reviennent à VIDEO. La gestion des tâches garde extraction/tri flexibles ; l’inférence cluster des services de modèles assure réponse millisecondes et haute disponibilité. Deux stratégies de surveillance (complète / partielle) permettent des règles précises par périodes.
</p>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
Concernant la gestion des appareils IoT, EasyAIoT fournit des capacités complètes de gestion du cycle de vie des appareils, prenant en charge plusieurs protocoles IoT et industriels (MQTT, TCP, HTTP, Modbus-TCP, Modbus-RTU, OPC UA), permettant une connexion rapide, une authentification sécurisée, une surveillance en temps réel et un contrôle intelligent des appareils. Le moteur de règles permet un flux et un traitement intelligents des données des appareils. Combiné aux capacités d'IA pour une analyse approfondie des données des appareils, il réalise une automatisation complète du processus allant de la connexion des appareils, la collecte de données, l'analyse intelligente à l'exécution des décisions, atteignant véritablement l'interconnexion et le contrôle intelligent de toutes choses.
</p>
</div>

<img src=".image/iframe1.jpg" alt="Architecture de la plateforme EasyAIoT" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">

## ⚠️ Clause de non-responsabilité

EasyAIoT est un projet d'apprentissage open source, sans lien avec des activités commerciales. Les utilisateurs doivent respecter les lois et règlements lors de l'utilisation de ce projet et ne pas mener d'activités illégales. Si EasyAIoT découvre que des utilisateurs ont des comportements illégaux, il coopérera avec les autorités concernées pour enquêter et signalera aux agences gouvernementales. Toute responsabilité légale découlant d'actes illégaux des utilisateurs sera assumée par l'utilisateur lui-même. En cas de dommages causés à des tiers par l'utilisation de l'utilisateur, l'utilisateur devra les indemniser conformément à la loi. L'utilisation de toutes les ressources associées à EasyAIoT est aux risques et périls de l'utilisateur.

## 📚 Documentation de déploiement

- [Documentation de déploiement de la plateforme](.doc/部署文档/平台部署文档_fr.md) — Guide Linux (Ubuntu / CentOS·RHEL **7–9** / **CentOS ARM** / ARM / **Kylin (麒麟) / openEuler (欧拉)**) / Mac / Windows
- [Déploiement image macOS](.doc/部署文档/平台macOS部署文档_fr.md) — Pull one-click d'images préconstruites (Docker Desktop)
- [Déploiement image Windows](.doc/部署文档/平台Windows部署文档_fr.md) — Entrée recommandée `install_windows.ps1`
- [Bonnes pratiques de déploiement](.doc/部署文档/部署最佳实践_fr.md) — Profils, prérequis, déploiement one-click (dont CentOS **7–9** / **CentOS ARM** / **Kylin (麒麟) / openEuler (欧拉)**), dépannage et production

## 🎮 Environnement de démonstration

- URL de démo : http://36.111.47.113:8888/
- Compte : admin
- Mot de passe : admin123

## ⚙️ Dépôts du projet

- Gitee: https://gitee.com/soaring-xiongkulu/easyaiot
- Github: https://github.com/soaring-xiongkulu/easyaiot

## 📸 Captures d'écran

<div>
  <img src=".image/banner/banner-video1000.gif" alt="Démo" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner-video1001.gif" alt="Démo" width="49%">
</div>

#### 🖥️ Grand écran de surveillance

| | | |
|:---:|:---:|:---:|
| ![Situation](.image/banner/banner1001.png) | ![Vue d'ensemble](.image/banner/banner1076.jpg) | ![Alertes](.image/banner/banner1074.jpg) |
| ![Tableau de bord](.image/banner/banner1075.jpg) | ![Multidimensionnel](.image/banner/banner1095.jpg) | ![Complet](.image/banner/banner1096.jpg) |
| ![Surveillance](.image/banner/banner1078.jpg) | ![Temps réel](.image/banner/banner1077.jpg) |  |

#### 📺 Visualisation des synoptiques de processus

| | | |
|:---:|:---:|:---:|
| ![Projet](.image/banner/banner1185.png) | ![Synoptique](.image/banner/banner1186.png) | ![Éditeur](.image/banner/banner1187.png) |
| ![Aperçu](.image/banner/banner1188.png) | ![Composants](.image/banner/banner1189.png) | ![Source de données](.image/banner/banner1190.png) |
| ![Publication](.image/banner/banner1191.png) | ![Exécution](.image/banner/banner1192.png) | ![Modèle](.image/banner/banner1193.png) |
| ![Actifs](.image/banner/banner1194.png) | ![Grand écran](.image/banner/banner1195.png) | ![Affichage](.image/banner/banner1196.png) |

#### 📹 Vidéosurveillance

| | | |
|:---:|:---:|:---:|
| ![Direct](.image/banner/banner1145.jpg) | ![Aperçu](.image/banner/banner1146.jpg) | ![Caméra](.image/banner/banner1051.jpg) |
| ![Liste](.image/banner/banner1053.jpg) | ![Push flux](.image/banner/banner1083.jpg) | ![Relais](.image/banner/banner1084.jpg) |
| ![Stockage](.image/banner/banner1121.png) | ![Capture](.image/banner/banner1122.png) | ![Enregistrement](.image/banner/banner1123.png) |
| ![Configuration](.image/banner/banner1124.png) | ![Capacité](.image/banner/banner1125.png) | ![Lecture](.image/banner/banner1126.png) |
| ![Capture](.image/banner/banner1117.png) | ![Fichiers](.image/banner/banner1118.png) | ![Politique](.image/banner/banner1119.png) |
| ![Quota](.image/banner/banner1120.png) | ![Galerie](.image/banner/banner1057.jpg) | ![Archive](.image/banner/banner1058.jpg) |
| ![Surveillance](.image/banner/banner1068.jpg) | ![Statistiques](.image/banner/banner1069.jpg) | ![Carte](.image/banner/banner1113.png) |
| ![Localisation](.image/banner/banner1114.png) | ![Distribution](.image/banner/banner1115.png) | ![Points](.image/banner/banner1116.png) |
| ![Vue live](.image/banner/banner1026.jpg) | ![Multi-flux](.image/banner/banner1028.jpg) | ![Push flux](.image/banner/banner1103.png) |
| ![Aperçu](.image/banner/banner1104.png) | ![Accès](.image/banner/banner1105.png) | ![NVR](.image/banner/banner1106.png) |
| ![Vue live](.image/banner/banner1183.jpg) | ![Carte](.image/banner/banner1184.jpg) |  |

#### 🧠 Modèles IA

| | | |
|:---:|:---:|:---:|
| ![Qwen](.image/banner/banner1093.jpg) | ![Modèle vision](.image/banner/banner1094.jpg) | ![Liste](.image/banner/banner1099.png) |
| ![Configuration](.image/banner/banner1100.png) | ![Détails](.image/banner/banner1101.png) | ![Appel](.image/banner/banner1102.png) |
| ![Entraînement](.image/banner/banner1019.jpg) | ![Tâche](.image/banner/banner1020.jpg) | ![Liste](.image/banner/banner1023.jpg) |
| ![Progression](.image/banner/banner1024.jpg) | ![Paramètres](.image/banner/banner1017.jpg) | ![Évaluation](.image/banner/banner1018.jpg) |
| ![Détails](.image/banner/banner1021.jpg) | ![Journaux](.image/banner/banner1022.jpg) | ![Gestion](.image/banner/banner1097.png) |
| ![Dépôt](.image/banner/banner1098.png) | ![Version](.image/banner/banner1039.jpg) | ![Actifs](.image/banner/banner1061.jpg) |
| ![Inférence](.image/banner/banner1040.jpg) | ![Configuration](.image/banner/banner1042.jpg) | ![Résultats](.image/banner/banner1043.jpg) |
| ![En ligne](.image/banner/banner1044.jpg) | ![Lot](.image/banner/banner1047.jpg) | ![Surveillance](.image/banner/banner1048.jpg) |
| ![Service](.image/banner/banner1045.jpg) | ![Déploiement](.image/banner/banner1046.jpg) | ![Cluster](.image/banner/banner1049.jpg) |
| ![Appel](.image/banner/banner1050.jpg) | ![Poids](.image/banner/banner1111.png) | ![Téléchargement](.image/banner/banner1112.png) |
| ![Pose](.image/banner/banner1147.jpg) | ![Reconnaissance](.image/banner/banner1148.jpg) | ![Tâche](.image/banner/banner1085.jpg) |
| ![Configuration](.image/banner/banner1086.jpg) | ![Détails](.image/banner/banner1087.jpg) | ![Exécution](.image/banner/banner1088.jpg) |
| ![Zone](.image/banner/banner1079.jpg) | ![Boîte de détection](.image/banner/banner1080.jpg) | ![Défense](.image/banner/banner1081.jpg) |
| ![Aperçu](.image/banner/banner1082.jpg) | ![Algorithme](.image/banner/banner1062.jpg) | ![Créer](.image/banner/banner1063.png) |
| ![Image](.image/banner/banner1064.jpg) | ![Analyse](.image/banner/banner1065.jpg) | ![Résultats](.image/banner/banner1066.jpg) |
| ![Relecture](.image/banner/banner1067.jpg) | ![Vue live](.image/banner/banner1052.jpg) | ![Intelligent](.image/banner/banner1054.jpg) |

#### 📦 Jeux de données

| | | |
|:---:|:---:|:---:|
| ![Gestion](.image/banner/banner1015.png) | ![Liste](.image/banner/banner1010.jpg) | ![Annotation](.image/banner/banner1027.png) |
| ![Tâche](.image/banner/banner1016.jpg) | ![Outils](.image/banner/banner1059.jpg) | ![Aperçu](.image/banner/banner1060.jpg) |
| ![Détails](.image/banner/banner1107.png) | ![Import](.image/banner/banner1108.png) | ![Projet](.image/banner/banner1109.png) |
| ![Revue](.image/banner/banner1110.png) | ![Créer](.image/banner/banner1007.jpg) | ![Échantillons](.image/banner/banner1008.jpg) |

#### 🔌 IoT

| | | |
|:---:|:---:|:---:|
| ![Modèle objet](.image/banner/banner1149.jpg) | ![Définition](.image/banner/banner1150.jpg) | ![Produit](.image/banner/banner1151.jpg) |
| ![Détails](.image/banner/banner1152.jpg) | ![Appareil](.image/banner/banner1153.jpg) | ![Détails](.image/banner/banner1154.jpg) |
| ![État](.image/banner/banner1155.jpg) | ![Propriétés](.image/banner/banner1156.jpg) | ![Service](.image/banner/banner1157.jpg) |
| ![Événements](.image/banner/banner1158.jpg) | ![Ombre](.image/banner/banner1159.jpg) | ![Topologie](.image/banner/banner1160.jpg) |
| ![Sous-appareils](.image/banner/banner1161.jpg) | ![Groupes](.image/banner/banner1162.jpg) | ![Contrôle](.image/banner/banner1163.jpg) |
| ![Télémétrie](.image/banner/banner1164.jpg) | ![Historique](.image/banner/banner1165.jpg) | ![Protocole](.image/banner/banner1166.jpg) |
| ![Connexion](.image/banner/banner1167.jpg) | ![Authentification](.image/banner/banner1168.jpg) | ![Débogage](.image/banner/banner1169.jpg) |
| ![Fonctions](.image/banner/banner1170.jpg) | ![Lecture/Écriture](.image/banner/banner1171.jpg) | ![Service](.image/banner/banner1172.jpg) |
| ![Abonnement](.image/banner/banner1173.jpg) | ![Journaux](.image/banner/banner1174.jpg) | ![En ligne](.image/banner/banner1175.jpg) |
| ![Statistiques](.image/banner/banner1176.jpg) | ![Vue d'ensemble](.image/banner/banner1177.jpg) | ![Tableau de bord](.image/banner/banner1178.jpg) |
| ![Produit](.image/banner/banner1006.jpg) | ![Appareil](.image/banner/banner1009.jpg) | ![OTA](.image/banner/banner1179.jpg) |
| ![Firmware](.image/banner/banner1180.jpg) | ![Tâche](.image/banner/banner1181.jpg) | ![Progression](.image/banner/banner1182.jpg) |
| ![Règles](.image/banner/banner1013.jpg) | ![Orchestration](.image/banner/banner1014.png) |  |

#### 🖥️ Cluster

| | | |
|:---:|:---:|:---:|
| ![Vue d'ensemble](.image/banner/banner1127.jpg) | ![Puissance de calcul](.image/banner/banner1128.jpg) | ![Nœud](.image/banner/banner1129.jpg) |
| ![Détails](.image/banner/banner1130.jpg) | ![Surveillance](.image/banner/banner1131.jpg) | ![Planification](.image/banner/banner1132.jpg) |
| ![Liste](.image/banner/banner1133.jpg) | ![État](.image/banner/banner1134.jpg) | ![Configuration](.image/banner/banner1135.jpg) |
| ![Allocation](.image/banner/banner1136.jpg) |  |  |

#### 🔔 Alertes

| | | |
|:---:|:---:|:---:|
| ![Événements](.image/banner/banner1089.jpg) | ![Traitement](.image/banner/banner1090.jpg) | ![Notification](.image/banner/banner1029.jpg) |
| ![Configuration](.image/banner/banner1030.jpg) | ![Liste](.image/banner/banner1072.jpg) | ![Détails](.image/banner/banner1031.jpg) |
| ![Traitement](.image/banner/banner1070.jpg) | ![Statistiques](.image/banner/banner1071.jpg) |  |

#### ⚙️ Système

| | | |
|:---:|:---:|:---:|
| ![Identité](.image/banner/banner1143.jpg) | ![Réinitialiser](.image/banner/banner1144.jpg) | ![Utilisateurs](.image/banner/banner1003.png) |
| ![Permissions](.image/banner/banner1004.png) | ![Menu](.image/banner/banner1005.png) | ![Configuration](.image/banner/banner1002.png) |

#### 📱 APP

| | | |
|:---:|:---:|:---:|
| ![Accueil](.image/banner/app/app_1000.jpg) | ![Surveillance](.image/banner/app/app_1001.jpg) | ![Aperçu](.image/banner/app/app_1002.jpg) |
| ![Alertes](.image/banner/app/app_1003.jpg) | ![Lecture](.image/banner/app/app_1004.jpg) | ![Appareil](.image/banner/app/app_1005.jpg) |
| ![Messages](.image/banner/app/app_1006.jpg) | ![Profil](.image/banner/app/app_1007.jpg) |  |

## 📞 Contact

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Veuillez d'abord suivre le compte officiel ci-dessous, puis nous contacter via le groupe d'échange technique ou WeChat.
</p>

## 👥 Compte officiel (WeChat)

<div>
  <img src=".image/公众号.jpg" alt="Compte officiel" width="30%">
</div>

## 💬 Groupe d'échange technique

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Après avoir suivi le compte officiel, scannez le code QR ci-dessous avec WeChat pour rejoindre le groupe d'échange technique EasyAIoT.
</p>

<div>
  <img src=".image/交流群3群.jpg" alt="Groupe d'échange technique EasyAIoT" width="30%">
</div>

## 💬 Contact WeChat

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Après avoir suivi le compte officiel, scannez le code QR ci-dessous pour nous ajouter en ami WeChat pour une communication individuelle.
</p>

<div>
  <img src=".image/微信联系方式.jpg" alt="Contact WeChat" width="200">
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

<table style="width: 100%; table-layout: fixed; border-collapse: collapse; margin: 20px 0; font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
<thead>
<tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
<th style="padding: 15px; text-align: left; font-weight: 600; border: 1px solid #e0e0e0; width: 32%; min-width: 9rem;">Contributeur</th>
<th style="padding: 15px; text-align: left; font-weight: 600; border: 1px solid #e0e0e0;">Contribution</th>
</tr>
</thead>
<tbody>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>℡夏别</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">A contribué à la documentation de déploiement Windows pour le projet EasyAIoT, fournissant un guide de déploiement complet pour les utilisateurs de la plateforme Windows, réduisant considérablement la difficulté de déploiement dans les environnements Windows et permettant à plus d'utilisateurs d'utiliser facilement la plateforme EasyAIoT.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>YiYaYiYaho</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">A contribué au script de déploiement en un clic de conteneurs Mac pour le projet EasyAIoT, fournissant une solution de déploiement automatisé pour les utilisateurs de la plateforme Mac, simplifiant considérablement le processus de déploiement dans les environnements Mac et améliorant l'expérience de déploiement pour les développeurs et les utilisateurs.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>山寒</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">A contribué au script de déploiement de conteneurs Linux pour le projet EasyAIoT, fournissant une solution de déploiement conteneurisé pour les utilisateurs de la plateforme Linux, réalisant un déploiement de conteneurs rapide et fiable, et fournissant des garanties importantes pour un fonctionnement stable dans les environnements de production.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>玖零。</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">A contribué au script de déploiement de conteneurs Linux pour le projet EasyAIoT, améliorant davantage la solution de déploiement conteneurisé pour les plateformes Linux, fournissant plus d'options pour les utilisateurs de différentes distributions Linux et promouvant les capacités de déploiement multiplateforme du projet.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>爱吃小柚子</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Pour faire progresser EasyAIoT vers un entraînement qui démarre vraiment, reste stable et reste simple à piloter, a systématiquement livré l'entraînement multi-GPU, la reprise sur point de contrôle et le déploiement côté nœud, afin que la puissance de calcul sur site soit pleinement utilisable et que les tâches d'entraînement restent maîtrisables : les serveurs détectent et utilisent automatiquement tous les GPU, et l'utilisateur peut choisir une ou plusieurs cartes sur la page d'entraînement au lieu d'être limité à une seule GPU visible ; formats et structures de jeux de données courants pris en charge, upload de grands jeux locaux, conservation des données d'origine après un échec pour réessayer rapidement — ce qui réduit fortement le coût de préparation et des allers-retours ; progression visible, tâches arrêtables et reprenables, évitant la perte de résultats après interruption ou un « stop » qui laisse encore tourner des processus en arrière-plan, avec repli et retour d'information clairs en cas d'échec d'ordonnancement local ou distant ; a aussi amélioré la sélection GPU, la reprise et l'affichage de l'état d'arrêt côté frontend, et corrigé les faux échecs de publication, l'écrasement des images d'aperçu personnalisées, la recherche de modèles par nom/version inopérante, ainsi que les timeouts et conflits de synchronisation des jeux de données — pour un cycle entraîner–publier–utiliser plus fluide et fiable. Auparavant, a également dirigé les tests d'intégration bout en bout GB28181 et flux métier IA ainsi que l'évaluation dédiée de la netteté d'image, fournissant une base solide pour un accès norme nationale fiable et une meilleure expérience visuelle.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>Dark</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">A contribué à l'intégration de bout en bout de GB28181 pour EasyAIoT en vidéosurveillance selon la norme nationale, avec lecture vidéo et commande PTZ (panoramique / inclinaison), rendant l'accès des équipements réellement exploitable pour la prévisualisation en direct et le pilotage à distance.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>machh</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">A contribué au projet EasyAIoT-Edge en menant à bien la validation de bout en bout de l'intégration des caméras et des fonctions IA, et en reliant ces capacités pour former une chaîne fonctionnelle sur l'edge.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>遗忘的星空</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">A contribué au développement de l'intégration directe des appareils EasyAIoT en fournissant un inventaire multi-marques des caméras IP et un scanner de sous-réseaux, avec découverte en masse des IPC et NVR Hikvision ; amélioration de la recherche en masse et de l'enregistrement en un clic pour les appareils connectés directement, sur le même sous-réseau ou entre sous-réseaux. L'accès s'effectue via les protocoles natifs des appareils, contournant le SDK Hikvision et réduisant la dépendance à la plateforme Hikvision — posant les bases d'une intégration ouverte et maîtrisée des caméras à grande échelle.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>阿龙</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Pour faire progresser EasyAIoT dans la visualisation cartographique et l'analyse spatiale, a contribué de manière indépendante à l'implémentation complète des capacités de visualisation spatiale Tianditu, couvrant l'intégration de la carte de base Tianditu nationale, le positionnement des caméras et des dispositifs d'alarme, les vues de répartition cartographique, la recherche de lieux et l'importation par lot de coordonnées, la cartographie automatique des événements d'alarme, la recherche de trajectoires par personne/véhicule et la relecture des trajectoires des appareils mobiles — faisant passer la capacité « visualisation spatiale Tianditu et analyse par carte » de la conception à une forme exploitable en production.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>雨落流殇</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Pour faire progresser EasyAIoT dans la diffusion multimédia à très grande échelle, a contribué aux idées de déploiement et d'ordonnancement de clusters de serveurs multimédia hétérogènes, proposant des solutions évolutives incluant la coordination multi-pools de nœuds, le découplage du plan de contrôle multimédia et de la couche métier, ainsi que l'enregistrement et l'ordonnancement des nœuds — posant des bases architecturales importantes pour permettre à la plateforme de prendre en charge l'accès concurrent à des dizaines de milliers de flux caméra avec une diffusion stable et une montée en charge élastique.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>常康</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Pour faire progresser EasyAIoT dans le transport intelligent et la gestion des véhicules, a contribué de manière indépendante à l'algorithme de reconnaissance de plaques d'immatriculation et à son implémentation complète, couvrant la détection et la localisation de plaques, la reconnaissance du numéro et de la couleur, la fusion de plaques à double rangée et la correction d'inclinaison/perspective, la gestion de bases de plaques et le matching séquentiel multi-bases, l'intégration en un clic aux tâches algorithmiques et la comparaison asynchrone — avec prise en charge des plaques bleues, jaunes, vertes, blanches et des véhicules à énergie nouvelle — faisant passer la capacité « reconnaissance de plaques et gestion de bases » de la planification à une application de production en boucle fermée.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>Li</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Pour faire progresser EasyAIoT dans la construction de la communauté de jeunes développeurs et l'écosystème collaboratif, a fait preuve d'un remarquable leadership organisationnel et d'un grand pouvoir de mobilisation en conduisant l'ensemble des étudiants du campus à participer activement à la co-construction du projet, rassemblant les talents de la jeunesse et la force collective du groupe pour insuffler à EasyAIoT un élan de développement continu et durable ; a également apporté une contribution majeure et irremplaçable à la promotion du projet, à sa mise en œuvre concrète et à la formation des futures générations de contributeurs.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>陈家林</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Pour faire progresser EasyAIoT dans l’interopérabilité IoT, l’accès aux protocoles industriels et la fusion vidéo air–sol, a rendu possible la boucle fermée commandes/état afin que la plateforme puisse réellement « envoyer, voir et contrôler » ; a contribué de façon systémique à l’accès Modbus-TCP, Modbus-RTU et OPC UA — acquisition unifiée des équipements industriels Ethernet et série et des nœuds OPC UA, lecture/écriture registres/points et mapping modèle d’objet — permettant d’agréger, surveiller et lier compteurs, capteurs, PLC, contrôleurs ; a également contribué à l’intégration dock/drone DJI FlightHub, intégrant l’inspection aérienne au système unifié vidéo/alarmes, élargissant la valeur pour l’acquisition industrielle, le pilotage de ligne, la patrouille large zone, la reconnaissance d’urgence et la perception ciel–terre.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>空空</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Pour faire progresser EasyAIoT dans la connexion directe des caméras, de « détectable » à « déployable en production », a comblé les lacunes critiques en authentification, synchronisation des canaux, modification de configuration et flux multi-marques, rendant la plateforme livrable sur des sites NVR / multi-fabricants réels : authentification fiable pour que les appareils en connexion directe puissent vraiment « se connecter et rester gérés » ; modèle de tirage de flux amélioré après synchronisation NVR pour que les flux synchronisés en masse soient lisibles et scalables ; paramètres d'accès maintenables dans la durée ; bibliothèque de règles d'URL pour les marques de vidéosurveillance courantes et règles de marque personnalisées ouvertes, permettant aux appareils hétérogènes d'assembler les flux en un clic sans essais manuels — faisant passer la connexion directe de « on peut scanner les appareils » à « on se connecte, la sync est exacte, on peut reconfigurer, et les flux multi-marques passent », posant une base solide pour les contrôles PTZ et zoom ultérieurs.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>狗娃</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Pour faire progresser EasyAIoT vers « des données IoT affichables en écran », a proposé en amont l'idée produit d'un module Board (tableau glisser-déposer) : les grands écrans traditionnels exigent souvent du SQL écrit à la main pour chaque écran et composant — livraison lente, modification coûteuse, quasi impossible pour le métier en autonomie. Le schéma Board confie graphiques, indicateurs et mise en page à un canevas glisser-déposer, avec variables de composants raccordées directement aux points IoT — valeurs temps réel et historiques depuis les appareils sans requête dédiée par tableau. Situation de campus, KPI de ligne, exploitation d'équipements, etc. passent de « l'écran nécessite du SQL développeur » à « choisir un point, glisser un composant, écran prêt » — cycle de livraison visualisation raccourci, « des chiffres en coulisse » devient « un écran en façade » opérable. Auparavant, a aussi contribué à la prédiction de données flottantes des capteurs, aux seuils haut/bas des attributs d'état, aux alertes et règles de seuil, et à l'affichage sur un écran de l'état des sous-appareils liés à l'équipement central — boucle « prédire — borner — alerter — régler — maîtriser sur un écran », pour que le côté équipements puisse « voir les chiffres, gouverner les bornes, lever les alertes et saisir le global ».</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>大老刘</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Pour faire progresser EasyAIoT dans la communication externe et la présentation de solutions, a contribué au support illustré <em>Plateforme d'analyse de vidéosurveillance IA</em>, structurant de façon systématique le panorama des capacités et la valeur terrain de la plateforme en scénarios d'analyse vidéo IA, afin que utilisateurs, intégrateurs et partenaires comprennent rapidement le positionnement et les points clés — améliorant nettement l'efficacité de la diffusion et des échanges commerciaux.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>刘兆中ᯤ⁵ᴳ</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Pour faire progresser EasyAIoT vers le déploiement en un clic sur macOS, a été parmi les premiers à contribuer une partie des scripts de déploiement Mac en un clic, ouvrant pour l'essentiel le chemin principal — tirage d'images, orchestration de conteneurs et contrôles préalables d'environnement — de sorte que le travail suivant n'avait plus qu'à combler le « dernier kilomètre ». Son exploration a clarifié pour l'équipe les nœuds critiques et les risques de la chaîne de déploiement Mac, raccourcissant nettement la voie vers la finalisation d'ingénierie ; contribution fondatrice indispensable pour faire passer le déploiement macOS de zéro à un état utilisable.</td>
</tr>
</tbody>
</table>

<p style="font-size: 14px; line-height: 1.8; color: #2c3e50; font-weight: 500; margin: 20px 0; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #3498db; border-radius: 4px;">
<strong>Remerciements spéciaux</strong> : Les contributeurs ci-dessus ont fait avancer EasyAIoT sur la documentation et les scripts de déploiement multiplateforme, les fondations et l'exploration du déploiement en un clic sur macOS, la mise en œuvre vidéo norme nationale et les tests d'intégration IA, l'utilisabilité de l'entraînement multi-GPU et la reprise sur point de contrôle, la découverte directe multi-marques et l'intégration en masse des caméras, la visualisation spatiale Tianditu complète, le déploiement et l'ordonnancement de clusters multimédia hétérogènes, la reconnaissance de plaques et son implémentation complète, l'intégration EasyAIoT-Edge de bout en bout, l'organisation de la communauté de jeunes développeurs, la boucle fermée IoT montante/descendante et l'accès vue aérienne DJI FlightHub, Modbus-TCP / Modbus-RTU / OPC UA, la connexion directe caméra de la découverte à la connexion/synchronisation/configuration/flux multi-marques, la conception Board avec intégration directe des points IoT temps réel/historique, la prédiction flottante des capteurs avec alertes de seuil et l'affichage sur un écran des sous-appareils, ainsi que les supports illustrés de présentation de la plateforme d'analyse de vidéosurveillance IA — leur professionnalisme et leur dévouement méritent respect et reconnaissance. Encore une fois, notre gratitude la plus sincère à ces contributeurs exceptionnels ! 🙏</p>

## 💝 Gardiens de l'open source

Le maintien d'un projet open source ne repose pas uniquement sur le code et la documentation. Dans les moments où les ressources de calcul d'EasyAIoT étaient les plus tendues et où le projet frôlait l'impasse, les personnes ci-dessous sont intervenues avec un soutien financier concret qui a permis au projet de garder le cap. Vous n'avez peut-être jamais soumis une seule ligne de code, mais chaque geste de confiance et de soutien a aidé EasyAIoT à franchir ses obstacles les plus difficiles et à continuer d'évoluer. Tant qu'il y aura des utilisateurs et des soutiens, l'écosystème open source mérite d'aller plus loin ; ce qu'EasyAIoT a accompli aujourd'hui n'aurait pas été possible sans ces compagnons de route venus en aide aux moments critiques. Nous leur adressons notre respect et notre gratitude les plus sincères ! Le classement suivant est établi sans ordre particulier :

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

## 🏆 Meilleurs praticiens

Ce sont les pionniers qui font passer EasyAIoT de « utilisable » à « facile à utiliser et bien utilisé » — les personnes suivantes ont déployé le projet EasyAIoT ou mis en œuvre des scénarios métier. Leurs explorations et réalisations constituent des références reproductibles pour la communauté. Nous leur adressons notre plus profond respect et nos félicitations les plus sincères ! L'ordre ci-dessous n'est pas hiérarchique :

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

## 🙏 Remerciements

Nous remercions les personnes suivantes pour leur soutien à ce projet, sous forme de contributions de code, de retours sur problèmes, de dons financiers, etc. ! L'ordre ci-dessous n'est pas hiérarchique :
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

## 💡 Attentes

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Vos suggestions pour améliorer EasyAIoT sont les bienvenues.
</p>

## 📄 Licence

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
翱翔的雄库鲁/easyaiot est publié sous la licence open source <a href="https://gitee.com/soaring-xiongkulu/easyaiot/blob/main/LICENSE" style="color: #3498db; text-decoration: none; font-weight: 600;">MIT LICENSE</a>. Nous nous engageons à promouvoir la diffusion et le développement de la technologie IA, afin que davantage de personnes puissent utiliser librement et bénéficier de cette technologie.
</p>

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
<strong>Licence d'utilisation</strong> : Particuliers et entreprises peuvent l'utiliser gratuitement à 100 %, sans obligation de conserver les informations sur l'auteur ou le copyright. Nous croyons que la valeur de la technologie réside dans son usage large et son innovation continue, et non dans les contraintes du droit d'auteur. Nous espérons que vous pourrez librement utiliser, modifier et distribuer ce projet, pour que la technologie IA profite réellement à chacun.
</p>

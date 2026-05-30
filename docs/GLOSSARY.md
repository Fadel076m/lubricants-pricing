# Glossaire Métier — Pricing & Lubricants

Ce document recense les acronymes **et les termes métier** utilisés dans le projet.
Il doit être mis à jour à chaque session dès qu'un nouveau terme est introduit.

---

## A — C

**API** *(Application Programming Interface)*
Interface qui permet à deux programmes de communiquer. Dans ce projet : FastAPI expose les données des modules (marges, PI, forecasts) sous forme d'endpoints REST que le dashboard ou un outil externe peut appeler.

**API REST** *(Representational State Transfer)*
Style d'architecture d'API web. Chaque ressource a une URL unique (ex. `/api/v1/margins/sku`). Le client envoie une requête HTTP (GET, POST) et reçoit une réponse JSON.

**Additifs**
Composants chimiques ajoutés à l'huile de base pour améliorer ses performances (anti-usure, détergents, viscosifiants). Représentent 20–28 % du COGS dans ce projet.

**B2B** *(Business to Business)*
Vente aux professionnels. Dans ce projet : B2B Industrie et B2B OEM sont deux canaux distincts avec des structures de marge très différentes (OEM ≈ 13,5 % de marge brute).

**B2C** *(Business to Consumer)*
Vente aux particuliers. Canaux : B2C GMS et B2C Réseau pétrolier. Marges plus élevées que le B2B (GMS ≈ 35,8 %).

**Benchmark Pricing**
Comparaison systématique de ses propres prix (NSP) avec ceux de la concurrence par canal et par région. Permet d'identifier les zones de sur- ou sous-positionnement.

**Brent / WTI**
Références mondiales du prix du pétrole brut (USD/baril). Le Brent est la référence pour l'Afrique et l'Europe. Corrélation R² = 0,98 avec le coût de l'huile de base dans ce projet.

**B2C Réseau pétrolier**
Canal de distribution via les stations-service et points de vente pétroliers. Marge moyenne ≈ 31,5 % dans le dataset.

---

## D — F

**Dash** *(Plotly Dash)*
Framework Python pour construire des dashboards web interactifs sans écrire de JavaScript. Tout se code en Python. Dans ce projet : dashboard M6 avec 3 pages (Executive View, Pricing View, Portfolio View).

**Docker**
Outil de conteneurisation : emballe une application et toutes ses dépendances dans un "conteneur" isolé. Garantit que le code tourne de manière identique sur ton PC et sur le serveur de prod. Commande : `docker-compose up` démarre tout le projet (Dash + API + BDD) en une ligne.

**Docker Compose**
Extension de Docker pour orchestrer plusieurs conteneurs ensemble (ex. : conteneur Dash + conteneur FastAPI + conteneur PostgreSQL qui démarrent et communiquent entre eux).

**DVC** *(Data Version Control)*
Outil de versioning pour les fichiers de données et les modèles ML (trop lourds pour Git). Fonctionne comme Git mais pour les datasets et les modèles entraînés. Utilisé en M4 pour versionner `transactions.parquet` et les modèles Prophet/XGBoost/LSTM.

**Dataset synthétique**
Jeu de données généré algorithmiquement (Python, NumPy) pour simuler des transactions réelles en l'absence de données propriétaires. Ce projet génère 14 400 lignes sur 36 mois.

**Devise locale**
Monnaie utilisée dans une région donnée. Dans ce projet : XOF (Sénégal, Côte d'Ivoire), XAF (Cameroun), MAD (Maroc).

**Élasticité-prix** *(Price Elasticity)*
Sensibilité du volume vendu à une variation de prix. Calculée en modèle log-log : `β = Δ% volume / Δ% prix`. Si |β| > 1 : marché très sensible au prix. Si |β| < 1 : marché peu sensible.

**Export** *(canal)*
Canal de vente vers des marchés hors zone principale. Marge structurellement plus faible à cause des coûts logistiques supplémentaires.

**Famille de produit**
Regroupement de SKUs par usage technique : Moteur · Hydraulique · Transmission · Marine · Graisse. Utilisé pour les analyses de positionnement régional.

---

## G — I

**FastAPI**
Framework Python pour construire des APIs REST à haute performance. Génère automatiquement une documentation Swagger interactive. Utilisé dans ce projet pour exposer les KPIs des modules (marges, PI recommandé, forecasts) à des consommateurs externes (dashboard, outils tiers).

**Forecast / Forecasting**
Prévision chiffrée d'une valeur future (volume, prix, marge) à partir de données historiques. M4 produit des forecasts à 30, 60 et 90 jours avec 3 modèles : Prophet, XGBoost, LSTM.

**GitHub Actions**
Service de CI/CD intégré à GitHub. Exécute automatiquement les tests et le déploiement à chaque `git push`. Dans ce projet : lance `pytest`, vérifie la qualité du code, puis déploie sur Render.com si les tests passent.

**Gap Analysis** *(Module 5)*
Comparaison entre une valeur prévue (forecast) et la valeur réelle observée. Formule : `Gap = Valeur réelle − Valeur prévue`. Permet d'alerter sur les dérives de performance.

**GMS** *(Grandes et Moyennes Surfaces)*
Canal de distribution supermarchés et hypermarchés. Forte visibilité consommateur, marges élevées (≈ 35,8 %) mais volumes unitaires faibles.

**Hold-out**
Période de données réservée exclusivement à la validation d'un modèle ML, non utilisée pendant l'entraînement. Dans ce projet : 6 derniers mois pour le walk-forward.

**Huile de base** *(Base Oil)*
Composant principal d'un lubrifiant (58–72 % du COGS). Son prix est indexé sur le Brent, ce qui en fait la principale variable de risque COGS du projet.

**Indice concurrentiel** *(indice_conc)*
Score de 0 à 1 mesurant la pression de la concurrence sur un SKU dans un canal donné. Calculé à partir de l'écart de prix et de l'intensité concurrentielle estimée.

**Inflation locale**
Taux d'inflation annuel par pays (source : World Bank API). Variable macro qui influence les coûts de stockage et la demande.

---

## J — L

**LSTM** *(Long Short-Term Memory)*
Architecture de réseau de neurones récurrents (Keras/TensorFlow) capable de capturer des dépendances à long terme dans les séries temporelles. Utilisé en M4 pour le forecasting.

---

## M — P

**MLflow**
Outil MLOps open-source pour tracker les expériences de Machine Learning : paramètres d'entraînement, métriques (MAPE, R²), versions des modèles. Permet de comparer "le Prophet de la semaine dernière vs celui d'aujourd'hui". Utilisé en M4.

**MLOps** *(Machine Learning Operations)*
Pratiques DevOps appliquées au ML : versioning des données (DVC), tracking des expériences (MLflow), déploiement automatisé des modèles. Assure que les modèles restent maintenables et reproductibles.

**Monte Carlo** *(Simulation Monte Carlo)*
Méthode statistique qui exécute N fois une simulation avec des paramètres tirés aléatoirement pour quantifier l'incertitude. Dans M3 : 500 itérations avec variation du choc Brent et des élasticités → intervalles de confiance P5/P50/P95 sur les marges.

**MAD** *(Dirham Marocain)*
Devise locale de la région Casablanca-MA. Taux de change flottant par rapport à l'USD.

**MAPE** *(Mean Absolute Percentage Error)*
Indicateur de précision des prévisions : `MAPE = moyenne(|réel − prévu| / réel) × 100`. Cible : < 8 % pour le prix base oil à 30 jours.

**Marge brute**
Différence entre le NSP et le COGS total : `Marge brute = NSP − COGS`. Exprimée en devise locale par litre.

**Marge brute %**
Ratio de rentabilité : `Marge brute % = Marge brute / NSP`. Zone alerte < 20 %, zone acceptable 20–30 %, zone saine ≥ 30 %. Dans le dataset : 24,8 % des transactions sont en zone alerte.

**NSP** *(Net Selling Price)*
Prix de vente net effectivement encaissé : `NSP = Prix vente brut × (1 − Remise %)`. C'est le prix de référence pour tous les calculs de marge.

**OEM** *(Original Equipment Manufacturer)*
Constructeur d'équipements d'origine (automobiles, machines industrielles). Canal B2B avec des remises très élevées → marge la plus faible du projet (≈ 13,5 %).

**Packaging**
Coût de l'emballage (bidon, fût, IBC). Représente 5–7 % du COGS. Variable selon le format et le marché.

**Parquet**
Format de fichier colonnaire Apache utilisé pour stocker les données analytiques. Plus rapide et plus compact que CSV pour les requêtes pandas.

**Part de marché**
Proportion des ventes d'un acteur sur le marché total d'une catégorie ou région. Estimée dans M1 à partir des données concurrentes et des volumes simulés.

**PI** *(Price Increase)*
Augmentation de prix tarifaire appliquée au prix liste. Simulée dans M3 selon trois scénarios : +3 %, +5 %, ou prix inchangé.

**Pipeline de données**
Séquence automatisée d'étapes de traitement : génération → validation → analyse → visualisation. Dans ce projet : `run_m1.py` orchestre les 4 étapes du Module 1.

**Positionnement prix**
Position relative de ses prix par rapport au marché (concurrent). Positif = on est plus cher. Négatif = on est moins cher. Analysé par région et famille dans la heatmap M1.

**Price Elasticity** → voir *Élasticité-prix*

**Prix de vente brut** *(Prix liste)*
Prix catalogue avant remise. Sert de base de négociation ; le NSP est toujours inférieur ou égal.

**Prophet**
Modèle de séries temporelles open-source développé par Meta. Gère automatiquement la saisonnalité et les jours fériés. Utilisé en M4 pour le forecasting de volume et de prix.

---

## Q — R

**PostgreSQL**
Système de gestion de base de données relationnelle open-source. Dans ce projet : utilisé en production via Supabase pour stocker les tables `transactions`, `margins`, `forecasts`, `alerts`. En dev local, les données restent en fichiers Parquet.

**pytest**
Framework de tests unitaires Python. Vérifie que les fonctions (calcul COGS, formule NSP, seuils d'alerte) retournent les bonnes valeurs. Chaque module a ses tests dans le dossier `tests/`.

**R²** *(Coefficient de détermination)*
Mesure la proportion de variance expliquée par un modèle de régression. Varie de 0 à 1. Dans ce projet : R² Brent vs coût huile de base = 0,98 → corrélation quasi parfaite.

**Remise** *(Discount)*
Réduction accordée sur le prix liste selon le canal ou le client. Exprimée en pourcentage (`remise_pct`). Plus élevée sur les canaux B2B (OEM, Industrie) que B2C.

**Réseau pétrolier** → voir *B2C Réseau pétrolier*

**Risque COGS**
Exposition de la marge à une hausse des coûts de production. Dans ce projet, les deux principaux risques sont : (1) hausse du Brent → hausse coût huile de base, (2) dépréciation du XOF → renchérissement des achats libellés en USD.

---

## S — U

**Scénario A / B / C**
Les trois options de pricing simulées dans M3 face à un choc COGS :
- **A (+3% PI)** : hausse modérée — préserve le volume mais ne couvre pas entièrement le choc.
- **B (+5% PI)** : hausse forte — meilleur équilibre marge/volume selon les simulations.
- **C (inchangé)** : pas de PI — perte de marge inévitable, aucune perte de volume.

**SQLite**
Base de données légère stockée dans un seul fichier. Utilisée optionnellement en développement local quand on a besoin de SQL sans serveur. Pas utilisée en production (remplacée par Supabase PostgreSQL).

**Supabase**
Plateforme cloud qui fournit un PostgreSQL hébergé avec une API REST auto-générée. Gratuit jusqu'à 500 MB. Dans ce projet : base de données de production pour stocker les tables analytiques accessibles par le dashboard Dash et l'API FastAPI.

**Swagger / OpenAPI**
Standard de documentation d'API REST. FastAPI génère automatiquement une interface Swagger à l'URL `/docs` — permet de tester tous les endpoints directement dans le navigateur sans écrire de code.

**Série temporelle** *(Time Series)*
Suite de valeurs numériques indexées dans le temps (mensuel ici). Les analyses de forecasting (M4) et d'évolution prix (M1) travaillent sur des séries temporelles.

**SKU** *(Stock Keeping Unit)*
Référence d'un article en stock. Dans ce projet : 20 SKUs couvrant 5 familles de lubrifiants (ex. : `SKU-5W30-1L` = Huile moteur 5W30 Full Syn, format 1 litre).

**Stockage** *(coût de stockage)*
Coût lié à l'entreposage des produits. Représente 4–5 % du COGS. Particulièrement élevé en Afrique de l'Ouest à cause des infrastructures logistiques.

---

## V — Z

**CI/CD** *(Continuous Integration / Continuous Deployment)*
Pratique DevOps : chaque modification de code déclenche automatiquement les tests (CI) puis le déploiement (CD). Dans ce projet : GitHub Actions exécute `pytest` à chaque push, puis déploie sur Render.com si tout passe.

**Callback** *(Dash Callback)*
Fonction Python dans Plotly Dash qui se déclenche quand l'utilisateur interagit avec un composant (slider, dropdown, bouton). Permet de mettre à jour les graphiques en temps réel sans recharger la page. Utilisé en M6 pour le simulateur de PI avec sliders.

**Conteneur** *(Docker Container)*
Environnement d'exécution isolé qui embarque une application et toutes ses dépendances. Garantit la reproducibilité : "tourne sur mon PC" = "tourne sur le serveur de prod".

**Walk-forward validation**
Méthode de validation des modèles de prévision qui respecte l'ordre temporel : on entraîne sur le passé, on teste sur le futur immédiat, puis on avance d'un pas. Évite le data leakage.

**XAF** *(Franc CFA d'Afrique Centrale)*
Devise de la région Douala-CM (Cameroun). Parité fixe avec l'euro (1 EUR = 655,957 XAF).

**XGBoost**
Algorithme de gradient boosting sur arbres de décision. Utilisé en M4 pour modéliser l'impact des drivers macro (Brent, inflation, taux de change) sur les volumes et marges.

**XOF** *(Franc CFA d'Afrique de l'Ouest)*
Devise des régions Dakar-SN et Abidjan-CI. Parité fixe avec l'euro (1 EUR = 655,957 XOF). Le taux USD/XOF est la variable de risque COGS centrale du projet car les achats d'huile de base sont libellés en USD.

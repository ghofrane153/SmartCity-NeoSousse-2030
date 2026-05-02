-- ============================================================
-- SMART CITY NEO-SOUSSE 2030
-- Script de création de la base de données
-- 
-- COMMENT ÇA MARCHE :
-- Ce script crée toutes les tables dans l'ordre correct.
-- L'ordre est important : une table "enfant" (avec FK) 
-- doit être créée APRÈS la table "parent" qu'elle référence.
-- ============================================================

-- Crée la base et sélectionne-la
DROP DATABASE IF EXISTS smart_city;
CREATE DATABASE smart_city CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smart_city;

-- ============================================================
-- TABLES INDÉPENDANTES (pas de FK, créées en premier)
-- ============================================================

-- Propriétaires de capteurs (entreprises ou particuliers)
CREATE TABLE PROPRIETAIRE (
    id_proprietaire INT AUTO_INCREMENT PRIMARY KEY,
    nom_proprietaire VARCHAR(100) NOT NULL,
    adresse VARCHAR(200),
    telephone VARCHAR(20),
    email VARCHAR(100),
    type_proprietaire VARCHAR(50)   -- ex: 'ENTREPRISE', 'MUNICIPALITE', 'PARTICULIER'
);

-- Citoyens de la ville
CREATE TABLE CITOYEN (
    id_citoyen INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    adresse VARCHAR(200),
    telephone VARCHAR(20),
    email VARCHAR(100),
    score_engagement INT DEFAULT 0,         -- Score écologique (0-100)
    preferences_mobilite VARCHAR(100)        -- ex: 'VELO', 'TRANSPORT_PUBLIC', 'VOITURE'
);

-- Techniciens de maintenance
CREATE TABLE TECHNICIEN (
    id_technicien INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    telephone VARCHAR(20),
    email VARCHAR(100),
    certification VARCHAR(100)               -- ex: 'ELEC_NIVEAU2', 'RESEAU_AVANCE'
);

-- Véhicules autonomes de la ville
CREATE TABLE VEHICULE_AUTONOME (
    id_vehicule INT AUTO_INCREMENT PRIMARY KEY,
    plaque_immatriculation VARCHAR(20) UNIQUE NOT NULL,
    type_vehicule VARCHAR(50),               -- ex: 'BUS', 'NAVETTE', 'CAMION'
    energie VARCHAR(50)                      -- ex: 'ELECTRIQUE', 'HYBRIDE', 'HYDROGENE'
);

-- Consultations citoyennes (sondages, votes, débats publics)
CREATE TABLE CONSULTATION_CITOYENNE (
    id_consultation INT AUTO_INCREMENT PRIMARY KEY,
    titre VARCHAR(200) NOT NULL,
    description TEXT,
    date_consultation DATE,
    theme VARCHAR(100)                       -- ex: 'MOBILITE', 'ENERGIE', 'SECURITE'
);

-- ============================================================
-- TABLES DÉPENDANTES (avec FK, créées après leurs parents)
-- ============================================================

-- Capteurs urbains (qualité air, bruit, trafic, etc.)
-- Dépend de : PROPRIETAIRE
CREATE TABLE CAPTEUR (
    id_capteur VARCHAR(20) PRIMARY KEY,      -- ex: 'C-001', 'C-452'
    type_capteur VARCHAR(50) NOT NULL,       -- ex: 'POLLUTION', 'BRUIT', 'TRAFIC', 'TEMPERATURE'
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    statut VARCHAR(20) DEFAULT 'INACTIF',    -- INACTIF | ACTIF | SIGNALE | EN_MAINTENANCE | HORS_SERVICE
    zone VARCHAR(50),                        -- ex: 'ZONE_NORD', 'CENTRE', 'ZONE_INDUSTRIELLE'
    id_proprietaire INT,
    FOREIGN KEY (id_proprietaire) REFERENCES PROPRIETAIRE(id_proprietaire),
    INDEX idx_statut (statut),               -- Index pour filtrer par statut rapidement
    INDEX idx_zone (zone)                    -- Index pour filtrer par zone
);

-- Mesures enregistrées par les capteurs (séries temporelles)
-- Dépend de : CAPTEUR
CREATE TABLE MESURE_CAPTEUR (
    id_mesure INT AUTO_INCREMENT PRIMARY KEY,
    timestamp_mesure DATETIME NOT NULL,
    valeur FLOAT NOT NULL,
    unite VARCHAR(20),                       -- ex: 'µg/m³', 'dB', 'véh/h', '°C'
    id_capteur VARCHAR(20) NOT NULL,
    FOREIGN KEY (id_capteur) REFERENCES CAPTEUR(id_capteur),
    INDEX idx_timestamp (timestamp_mesure),  -- Important pour les requêtes temporelles
    INDEX idx_capteur_time (id_capteur, timestamp_mesure)
);

-- Interventions de maintenance sur les capteurs
-- Dépend de : CAPTEUR
CREATE TABLE INTERVENTION (
    id_intervention INT AUTO_INCREMENT PRIMARY KEY,
    date_heure_debut DATETIME NOT NULL,
    date_heure_fin DATETIME,                 -- NULL si intervention encore en cours
    nature VARCHAR(100),                     -- ex: 'REMPLACEMENT', 'CALIBRATION', 'URGENCE'
    impact_co2 FLOAT DEFAULT 0,             -- Émissions CO2 de l'intervention (kg)
    commentaire TEXT,
    id_capteur VARCHAR(20) NOT NULL,
    FOREIGN KEY (id_capteur) REFERENCES CAPTEUR(id_capteur),
    INDEX idx_date_debut (date_heure_debut)
);

-- Trajets effectués par les véhicules autonomes
-- Dépend de : VEHICULE_AUTONOME
CREATE TABLE TRAJET (
    id_trajet INT AUTO_INCREMENT PRIMARY KEY,
    origine VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    date_heure_depart DATETIME NOT NULL,
    date_heure_arrivee DATETIME,
    duree INT,                               -- Durée en minutes
    economie_co2 FLOAT DEFAULT 0,           -- CO2 économisé vs voiture classique (kg)
    id_vehicule INT NOT NULL,
    FOREIGN KEY (id_vehicule) REFERENCES VEHICULE_AUTONOME(id_vehicule)
);

-- ============================================================
-- TABLES DE LIAISON (Many-to-Many)
-- ============================================================

-- Liaison Intervention <-> Technicien (un technicien peut faire plusieurs interventions)
CREATE TABLE INTERVENTION_TECHNICIEN (
    id_intervention INT NOT NULL,
    id_technicien INT NOT NULL,
    role_tech VARCHAR(50),                   -- ex: 'RESPONSABLE', 'ASSISTANT', 'VALIDATEUR'
    PRIMARY KEY (id_intervention, id_technicien),
    FOREIGN KEY (id_intervention) REFERENCES INTERVENTION(id_intervention),
    FOREIGN KEY (id_technicien) REFERENCES TECHNICIEN(id_technicien)
);

-- Liaison Citoyen <-> Consultation (un citoyen peut participer à plusieurs consultations)
CREATE TABLE PARTICIPATION (
    id_citoyen INT NOT NULL,
    id_consultation INT NOT NULL,
    PRIMARY KEY (id_citoyen, id_consultation),
    FOREIGN KEY (id_citoyen) REFERENCES CITOYEN(id_citoyen),
    FOREIGN KEY (id_consultation) REFERENCES CONSULTATION_CITOYENNE(id_consultation)
);

-- ============================================================
-- Vérification : affiche toutes les tables créées
-- ============================================================
SHOW TABLES;
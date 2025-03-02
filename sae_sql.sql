DROP TABLE IF EXISTS ligne_commande;
DROP TABLE IF EXISTS ligne_panier;
DROP TABLE IF EXISTS cle_usb;
DROP TABLE IF EXISTS type_cle_usb;
DROP TABLE IF EXISTS commande;
DROP TABLE IF EXISTS capacite;
DROP TABLE IF EXISTS etat;
DROP TABLE IF EXISTS utilisateur;

CREATE TABLE IF NOT EXISTS utilisateur (
    id_utilisateur INT AUTO_INCREMENT PRIMARY KEY,
    login VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    nom VARCHAR(50) NOT NULL,
    est_actif BOOLEAN
);

CREATE TABLE IF NOT EXISTS etat(
    id_etat INT AUTO_INCREMENT,
    libelle VARCHAR(50),
    PRIMARY KEY (id_etat)
);

CREATE TABLE IF NOT EXISTS commande (
    id_commande INT AUTO_INCREMENT,
    date_achat DATE,
    utilisateur_id INT,
    etat_id INT,
    adresse_livraison_id INT,
    adresse_facturation_id INT,
    PRIMARY KEY (id_commande),
    CONSTRAINT commande1_ibfk_1 FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id_utilisateur) ON DELETE CASCADE,
    CONSTRAINT commande1_ibfk_2 FOREIGN KEY (etat_id) REFERENCES etat(id_etat) ON DELETE CASCADE,
    CONSTRAINT fk_adresse_livraison FOREIGN KEY (adresse_livraison_id) REFERENCES adresse(id_adresse),
    CONSTRAINT fk_adresse_facturation FOREIGN KEY (adresse_facturation_id) REFERENCES adresse(id_adresse)
);

CREATE TABLE IF NOT EXISTS capacite (
    id_capacite INT AUTO_INCREMENT PRIMARY KEY,
    libelle_capacite VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS type_cle_usb (
    id_type_cle_usb INT AUTO_INCREMENT PRIMARY KEY,
    libelle_type_cle_usb VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS cle_usb (
    id_cle_usb INT AUTO_INCREMENT PRIMARY KEY,
    nom_cle_usb VARCHAR(50) NOT NULL,
    capacite_id INT NOT NULL,
    description TEXT NOT NULL,
    vitesse_transfert VARCHAR(20) NOT NULL,
    prix_cle_usb DECIMAL(10, 2) NOT NULL,
    couleur VARCHAR(20) NOT NULL,
    type_cle_usb_id INT NOT NULL,
    fournisseur VARCHAR(50) NOT NULL,
    marque VARCHAR(50) NOT NULL,
    photo_url VARCHAR(255) NOT NULL,
    utilisateur_id INT,
    CONSTRAINT cle_usb_ibfk_1 FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id_utilisateur),
    CONSTRAINT cle_usb_ibfk_2 FOREIGN KEY (capacite_id) REFERENCES capacite(id_capacite),
    CONSTRAINT cle_usb_ibfk_3 FOREIGN KEY (type_cle_usb_id) REFERENCES type_cle_usb(id_type_cle_usb)
);

CREATE TABLE IF NOT EXISTS ligne_panier (
    utilisateur_id INT,
    cle_usb_id INT,
    quantite INT,
    date_ajout DATE,
    CONSTRAINT ligne_panier_ibfk_1 FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id_utilisateur) ON DELETE CASCADE,
    CONSTRAINT ligne_panier_ibfk_2 FOREIGN KEY (cle_usb_id) REFERENCES cle_usb(id_cle_usb) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ligne_commande (
    commande_id INT,
    cle_usb_id INT,
    prix INT,
    quantite INT,
    CONSTRAINT ligne_commande_ibfk_1 FOREIGN KEY (commande_id) REFERENCES commande(id_commande) ON DELETE CASCADE,
    CONSTRAINT ligne_commande_ibfk_2 FOREIGN KEY (cle_usb_id) REFERENCES cle_usb(id_cle_usb) ON DELETE CASCADE
);


INSERT INTO utilisateur(id_utilisateur, login,email,password,role,nom,est_actif) VALUES
(1,'admin','admin@admin.fr',
    'pbkdf2:sha256:1000000$eQDrpqICHZ9eaRTn$446552ca50b5b3c248db2dde6deac950711c03c5d4863fe2bd9cef31d5f11988',
    'ROLE_admin','admin','1'),
(2,'client','client@client.fr',
    'pbkdf2:sha256:1000000$jTcSUnFLWqDqGBJz$bf570532ed29dc8e3836245f37553be6bfea24d19dfb13145d33ab667c09b349',
    'ROLE_client','client','1'),
(3,'client2','client2@client2.fr',
    'pbkdf2:sha256:1000000$qDAkJlUehmaARP1S$39044e949f63765b785007523adcde3d2ad9c2283d71e3ce5ffe58cbf8d86080',
    'ROLE_client','client2','1');

INSERT INTO capacite (libelle_capacite)
VALUES ('8GB'), ('16GB'), ('32GB'), ('64GB');

INSERT INTO type_cle_usb (libelle_type_cle_usb)
VALUES ('USB-C'), ('USB classique'), ('USB 3.0'), ('USB 2.0');

INSERT INTO cle_usb (nom_cle_usb, capacite_id, description, vitesse_transfert, prix_cle_usb, couleur, type_cle_usb_id, fournisseur, marque, photo_url, utilisateur_id)
VALUES
('Cle_USB_A', 1, 'Cle_USB compacte et rapide.', '100 Mo/s', 9.99, 'Noir', 1, 'Fournisseur 1', 'Marque A', 'cle_usb_A.jpg',1),
('Cle_USB_B', 2, 'Cle_USB resistante a eau.', '150 Mo/s', 14.99, 'Bleu', 2, 'Fournisseur 2', 'Marque B', 'cle_usb_B.jpg',2),
('Cle_USB_C', 3, 'Cle_USB ultra fine.', '120 Mo/s', 12.99, 'Rouge', 3, 'Fournisseur 3', 'Marque C', 'cle_usb_D.jpeg',3),
('Cle_USB_D', 4, 'Cle_USB avec protection antivirale.', '200 Mo/s', 19.99, 'Vert', 4, 'Fournisseur 4', 'Marque D', 'CLE_USB_C.jpg',1),
('Cle_USB_E', 1, 'Cle_USB en aluminium.', '90 Mo/s', 7.99, 'Gris', 2, 'Fournisseur 5', 'Marque E', 'cle_usb_E.jpeg',2),
('Cle_USB_F', 2, 'Cle_USB compatible tous appareils.', '130 Mo/s', 11.99, 'Blanc', 1, 'Fournisseur 6', 'Marque F', 'cle_usb.jpg',3),
('Cle_USB_G', 3, 'Cle_USB haute performance.', '250 Mo/s', 25.99, 'Noir', 3, 'Fournisseur 7', 'Marque G', 'finewish.jpg',1),
('Cle_USB_H', 4, 'Cle_USB design moderne.', '100 Mo/s', 9.49, 'Jaune', 4, 'Fournisseur 8', 'Marque H', 'hama.webp',2),
('Cle_USB_I', 1, 'Cle_USB economique.', '80 Mo/s', 5.99, 'Bleu', 2, 'Fournisseur 9', 'Marque I', 'idisk.jpg',3),
('Cle_USB_J', 2, 'Cle_USB ultra resistante.', '110 Mo/s', 10.99, 'Rouge', 1, 'Fournisseur 10', 'Marque J', 'images.jpeg',1),
('Cle_USB_K', 3, 'Cle_USB avec lecteur empreintes.', '300 Mo/s', 29.99, 'Noir', 3, 'Fournisseur 11', 'Marque K', 'integral-cle-usb-3-0-drive-noire-8gb.jpg',2),
('Cle_USB_L', 4, 'Cle_USB ultra legere.', '140 Mo/s', 13.99, 'Gris', 4, 'Fournisseur 12', 'Marque L', 'kingston-cle-usb-32-giga.jpg',3),
('Cle_USB_M', 1, 'Cle_USB avec double connecteur.', '200 Mo/s', 17.99, 'Noir', 1, 'Fournisseur 13', 'Marque M', 'LD0006025220.jpg',1),
('Cle_USB_N', 2, 'Cle_USB robuste et durable.', '150 Mo/s', 16.99, 'Blanc', 2, 'Fournisseur 14', 'Marque N', 'leica.jpeg',2),
('Cle_USB_O', 3, 'Cle_USB retractable.', '180 Mo/s', 19.49, 'Rouge', 3, 'Fournisseur 15', 'Marque O', 'pr_CLEUSB3016GB-43.jpg',3);

INSERT INTO etat(id_etat, libelle) VALUES
(1, 'En attente'),
(2, 'Expédiée'),
(3, 'Livrée');

SELECT 
    cle_usb.nom_cle_usb,
    capacite.libelle_capacite AS capacite,
    cle_usb.description,
    cle_usb.vitesse_transfert,
    cle_usb.prix_cle_usb,
    cle_usb.couleur,
    type_cle_usb.libelle_type_cle_usb AS type,
    cle_usb.fournisseur,
    cle_usb.marque,
    cle_usb.photo_url,
    cle_usb.utilisateur_id 
FROM 
    cle_usb
JOIN 
    capacite ON cle_usb.capacite_id = capacite.id_capacite
JOIN 
    type_cle_usb ON cle_usb.type_cle_usb_id = type_cle_usb.id_type_cle_usb;

SELECT 
    nom_cle_usb,
    description,
    prix_cle_usb,
    couleur
FROM 
    cle_usb
JOIN 
    capacite ON cle_usb.capacite_id = capacite.id_capacite
WHERE 
    capacite.libelle_capacite = '16GB';

SELECT 
    nom_cle_usb,
    prix_cle_usb,
    vitesse_transfert,
    couleur
FROM 
    cle_usb
WHERE 
    prix_cle_usb BETWEEN 9.99 AND 15;

SELECT 
    nom_cle_usb,
    vitesse_transfert,
    fournisseur,
    marque
FROM 
    cle_usb
JOIN 
    type_cle_usb ON cle_usb.type_cle_usb_id = type_cle_usb.id_type_cle_usb
WHERE 
    type_cle_usb.libelle_type_cle_usb = 'USB 3.0';

SELECT 
    nom_cle_usb,
    prix_cle_usb,
    description,
    marque
FROM 
    cle_usb
ORDER BY 
    prix_cle_usb DESC;

SELECT 
    type_cle_usb.libelle_type_cle_usb AS type,
    COUNT(cle_usb.id_cle_usb) AS nombre_cle_usb
FROM 
    cle_usb
JOIN 
    type_cle_usb ON cle_usb.type_cle_usb_id = type_cle_usb.id_type_cle_usb
GROUP BY 
    type_cle_usb.libelle_type_cle_usb;

SELECT 
    nom_cle_usb,
    capacite.libelle_capacite AS capacite,
    type_cle_usb.libelle_type_cle_usb AS type,
    prix_cle_usb
FROM 
    cle_usb
JOIN 
    capacite ON cle_usb.capacite_id = capacite.id_capacite
JOIN 
    type_cle_usb ON cle_usb.type_cle_usb_id = type_cle_usb.id_type_cle_usb
ORDER BY 
    capacite.libelle_capacite;

SELECT 
    nom_cle_usb,
    description,
    prix_cle_usb,
    couleur
FROM 
    cle_usb
WHERE 
    marque = 'Marque A';


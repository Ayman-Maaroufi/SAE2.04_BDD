#! /usr/bin/python
# -*- coding:utf-8 -*-
from flask import *
import datetime
from decimal import *
from connexion_db import get_db
from werkzeug.security import generate_password_hash

fixtures_load = Blueprint('fixtures_load', __name__,
                          template_folder='templates')


@fixtures_load.route('/base/init')
def fct_fixtures_load():
    mycursor = get_db().cursor()

    # Désactiver les vérifications de clés étrangères
    mycursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    sql = '''DROP TABLE IF EXISTS utilisateur, type_cle_usb, etat, cle_usb, commande, ligne_commande, ligne_panier, adresse, liste_envies, historique, declinaison, commentaire, declinaison_article'''
    mycursor.execute(sql)

    # Réactiver les vérifications de clés étrangères
    mycursor.execute("SET FOREIGN_KEY_CHECKS = 1")

    sql = '''
    CREATE TABLE utilisateur(
        id_utilisateur INT AUTO_INCREMENT PRIMARY KEY,
        login VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL,
        nom VARCHAR(255),
        est_actif TINYINT(1) DEFAULT 1
    ) DEFAULT CHARSET utf8;  
    '''
    mycursor.execute(sql)

    admin_password = generate_password_hash('admin', method='pbkdf2:sha256')
    client_password = generate_password_hash('client', method='pbkdf2:sha256')
    client2_password = generate_password_hash('client2', method='pbkdf2:sha256')

    sql = ''' 
    INSERT INTO utilisateur (login, email, password, role, nom, est_actif)
    VALUES 
    (%s, %s, %s, 'ROLE_admin', 'Admin', 1),
    (%s, %s, %s, 'ROLE_client', 'Client', 1),
    (%s, %s, %s, 'ROLE_client', 'Client2', 1)
    '''
    mycursor.execute(sql, ('admin', 'admin@admin.fr', admin_password,
                           'client', 'client@client.fr', client_password,
                           'client2', 'client2@client2.fr', client2_password))

    sql = ''' 
    CREATE TABLE type_cle_usb(
        id_type_cle_usb INT AUTO_INCREMENT PRIMARY KEY,
        libelle_type_cle_usb VARCHAR(255) NOT NULL
    ) DEFAULT CHARSET utf8;  
    '''
    mycursor.execute(sql)
    sql = ''' 
    INSERT INTO type_cle_usb (libelle_type_cle_usb)
    VALUES 
    ('USB 2.0'),
    ('USB 3.0'),
    ('USB-C')
    '''
    mycursor.execute(sql)

    sql = ''' 
    CREATE TABLE etat (
        id_etat INT AUTO_INCREMENT PRIMARY KEY,
        libelle VARCHAR(255) NOT NULL
    ) DEFAULT CHARSET=utf8;  
    '''
    mycursor.execute(sql)
    sql = ''' 
    INSERT INTO etat (libelle)
    VALUES 
    ('En cours de traitement'),
    ('Expédié'),
    ('Livré')
    '''
    mycursor.execute(sql)

    sql = '''
    CREATE TABLE declinaison (
        id_declinaison INT AUTO_INCREMENT PRIMARY KEY,
        libelle VARCHAR(50) NOT NULL
    );
    '''
    mycursor.execute(sql)

    sql = '''
    INSERT INTO declinaison (libelle) VALUES
    ('Rouge'), ('Vert'), ('Bleu'), ('Jaune');
    '''
    mycursor.execute(sql)

    sql = ''' 
    CREATE TABLE cle_usb (
        id_cle_usb INT AUTO_INCREMENT PRIMARY KEY,
        nom_cle_usb VARCHAR(255) NOT NULL,
        prix_cle_usb DECIMAL(10,2) NOT NULL,
        stock INT NOT NULL,
        description TEXT,
        photo_url VARCHAR(255),
        type_cle_usb_id INT,
        FOREIGN KEY (type_cle_usb_id) REFERENCES type_cle_usb(id_type_cle_usb)
    ) DEFAULT CHARSET=utf8;  
    '''
    mycursor.execute(sql)

    sql = '''
    CREATE TABLE adresse (
        id_adresse INT AUTO_INCREMENT PRIMARY KEY,
        nom VARCHAR(255) NOT NULL,
        rue VARCHAR(255) NOT NULL,
        code_postal VARCHAR(10) NOT NULL,
        ville VARCHAR(255) NOT NULL,
        utilisateur_id INT,
        FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id_utilisateur)
    );
    '''
    mycursor.execute(sql)

    sql = ''' 
    CREATE TABLE commande (
        id_commande INT AUTO_INCREMENT PRIMARY KEY,
        date_achat DATE NOT NULL,
        utilisateur_id INT,
        etat_id INT,
        adresse_livraison_id INT,
        adresse_facturation_id INT,
        FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id_utilisateur),
        FOREIGN KEY (etat_id) REFERENCES etat(id_etat),
        FOREIGN KEY (adresse_livraison_id) REFERENCES adresse(id_adresse),
        FOREIGN KEY (adresse_facturation_id) REFERENCES adresse(id_adresse)
    ) DEFAULT CHARSET=utf8;  
    '''
    mycursor.execute(sql)

    sql = ''' 
    CREATE TABLE ligne_commande(
        commande_id INT,
        cle_usb_id INT,
        prix DECIMAL(10,2) NOT NULL,
        quantite INT NOT NULL,
        PRIMARY KEY (commande_id, cle_usb_id),
        FOREIGN KEY (commande_id) REFERENCES commande(id_commande),
        FOREIGN KEY (cle_usb_id) REFERENCES cle_usb(id_cle_usb)
    );
    '''
    mycursor.execute(sql)

    sql = ''' 
    CREATE TABLE ligne_panier (
        utilisateur_id INT,
        cle_usb_id INT,
        quantite INT NOT NULL,
        date_ajout DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (utilisateur_id, cle_usb_id),
        FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id_utilisateur),
        FOREIGN KEY (cle_usb_id) REFERENCES cle_usb(id_cle_usb)
    );  
    '''
    mycursor.execute(sql)

    sql = '''
    CREATE TABLE liste_envies (
        utilisateur_id INT,
        cle_usb_id INT,
        date_ajout DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (utilisateur_id, cle_usb_id),
        FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id_utilisateur),
        FOREIGN KEY (cle_usb_id) REFERENCES cle_usb(id_cle_usb)
    );
    '''
    mycursor.execute(sql)

    sql = '''
    CREATE TABLE historique (
        utilisateur_id INT,
        cle_usb_id INT,
        date_consultation DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (utilisateur_id, cle_usb_id),
        FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id_utilisateur),
        FOREIGN KEY (cle_usb_id) REFERENCES cle_usb(id_cle_usb)
    );
    '''
    mycursor.execute(sql)

    sql = ''' 
    CREATE TABLE commentaire(
       utilisateur_id INT,
       cle_usb_id INT,
       date_publication DATETIME,
       commentaire VARCHAR(255),
       valider INT,
       note INT,
       PRIMARY KEY(utilisateur_id, cle_usb_id, date_publication),
       FOREIGN KEY(utilisateur_id) REFERENCES utilisateur(id_utilisateur),
       FOREIGN KEY(cle_usb_id) REFERENCES cle_usb(id_cle_usb)
    ) DEFAULT CHARSET=utf8;
    '''
    mycursor.execute(sql)

    sql = ''' 
    INSERT INTO cle_usb (nom_cle_usb, prix_cle_usb, stock, description, photo_url, type_cle_usb_id)
    VALUES 
    (%s, %s, %s, %s, %s, %s),
    (%s, %s, %s, %s, %s, %s),
    (%s, %s, %s, %s, %s, %s),
    (%s, %s, %s, %s, %s, %s),
    (%s, %s, %s, %s, %s, %s),
    (%s, %s, %s, %s, %s, %s),
    (%s, %s, %s, %s, %s, %s),
    (%s, %s, %s, %s, %s, %s),
    (%s, %s, %s, %s, %s, %s),
    (%s, %s, %s, %s, %s, %s),
    (%s, %s, %s, %s, %s, %s),
    (%s, %s, %s, %s, %s, %s),
    (%s, %s, %s, %s, %s, %s),
    (%s, %s, %s, %s, %s, %s),
    (%s, %s, %s, %s, %s, %s)
    '''
    cles_usb_data = [
        ('Clé USB 32Go', 19.99, 100, 'Clé USB 32Go haute performance', 'cle-usb-1.jpg', 1),
        ('Clé USB 64Go', 29.99, 75, 'Clé USB 64Go rapide', 'cle-usb-2.jpg', 2),
        ('Clé USB-C 128Go', 49.99, 50, 'Clé USB-C 128Go pour appareils modernes', 'cle-usb-3.jpg', 3),
        ('Clé USB 16Go', 14.99, 150, 'Clé USB 16Go compacte', 'cle-usb-4.jpg', 1),
        ('Clé USB 256Go', 79.99, 30, 'Clé USB 256Go haute capacité', 'cle-usb-5.jpg', 2),
        ('Clé USB-C 64Go', 39.99, 60, 'Clé USB-C 64Go polyvalente', 'cle-usb-6.jpg', 3),
        ('Clé USB 128Go', 59.99, 40, 'Clé USB 128Go fiable', 'cle-usb-7.jpg', 2),
        ('Clé USB 8Go', 9.99, 200, 'Clé USB 8Go économique', 'cle-usb-8.jpg', 1),
        ('Clé USB-C 32Go', 24.99, 80, 'Clé USB-C 32Go compacte', 'cle-usb-9.jpg', 3),
        ('Clé USB 512Go', 129.99, 20, 'Clé USB 512Go ultra-capacité', 'cle-usb-10.jpg', 2),
        ('Clé USB 4Go', 7.99, 250, 'Clé USB 4Go basique', 'cle-usb-11.jpg', 1),
        ('Clé USB-C 256Go', 89.99, 25, 'Clé USB-C 256Go haute performance', 'cle-usb-12.jpg', 3),
        ('Clé USB 1To', 199.99, 10, 'Clé USB 1To capacité maximale', 'cle-usb-13.jpg', 2),
        ('Clé USB 2Go', 5.99, 300, 'Clé USB 2Go pour petits fichiers', 'cle-usb-14.jpg', 1),
        ('Clé USB-C 512Go', 149.99, 15, 'Clé USB-C 512Go ultra-rapide', 'cle-usb-15.jpg', 3)
    ]
    mycursor.execute(sql, [item for sublist in cles_usb_data for item in sublist])

    sql = '''
    INSERT INTO commentaire (utilisateur_id, cle_usb_id, date_publication, commentaire, valider, note) VALUES
        (2, 1, '2024-01-01 10:00:00', 'Com 1 !', 1, 5),
        (3, 2, '2024-01-02 11:30:00', 'Com 2', 1, 4),
        (2, 3, '2024-01-03 14:15:00', 'Com 3', 0, 3);
    '''
    mycursor.execute(sql)

    get_db().commit()
    return redirect('/')
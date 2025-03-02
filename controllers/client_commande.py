#! /usr/bin/python
# -*- coding:utf-8 -*-
from flask import Blueprint
from flask import Flask, request, render_template, redirect, url_for, abort, flash, session, g
from datetime import datetime
from connexion_db import get_db

client_commande = Blueprint('client_commande', __name__,
                            template_folder='templates')

@client_commande.route('/client/commande/valide', methods=['GET', 'POST'])
def client_commande_valide():
    mycursor = get_db().cursor()
    id_client = session['id_user']

    sql = '''
    SELECT c.id_cle_usb, c.nom_cle_usb, c.prix_cle_usb, lp.quantite
    FROM ligne_panier lp
    JOIN cle_usb c ON lp.cle_usb_id = c.id_cle_usb
    WHERE lp.utilisateur_id = %s
    '''
    mycursor.execute(sql, (id_client,))
    articles_panier = mycursor.fetchall()

    if len(articles_panier) >= 1:
        sql = '''
        SELECT SUM(c.prix_cle_usb * lp.quantite) as prix_total
        FROM ligne_panier lp
        JOIN cle_usb c ON lp.cle_usb_id = c.id_cle_usb
        WHERE lp.utilisateur_id = %s
        '''
        mycursor.execute(sql, (id_client,))
        prix_total = mycursor.fetchone()['prix_total']
    else:
        prix_total = None

    sql = '''
    SELECT *
    FROM adresse
    WHERE utilisateur_id = %s
    '''
    mycursor.execute(sql, (id_client,))
    adresses = mycursor.fetchall()

    return render_template('client/boutique/panier_validation_adresses.html',
                           articles_panier=articles_panier,
                           prix_total=prix_total,
                           adresses=adresses,
                           validation=1
                           )

@client_commande.route('/client/commande/add', methods=['POST'])
def client_commande_add():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_adresse_livraison = request.form.get('id_adresse_livraison')
    id_adresse_facturation = request.form.get('id_adresse_facturation')
    adresse_identique = request.form.get('adresse_identique')

    if not id_adresse_livraison:
        flash(u'Veuillez choisir une adresse de livraison', 'warning')
        return redirect('/client/commande/valide')

    if adresse_identique == 'adresse_identique':
        id_adresse_facturation = id_adresse_livraison
    elif not id_adresse_facturation:
        flash(u'Veuillez choisir une adresse de facturation', 'warning')
        return redirect('/client/commande/valide')

    sql = '''
    SELECT cle_usb_id, quantite
    FROM ligne_panier
    WHERE utilisateur_id = %s
    '''
    mycursor.execute(sql, (id_client,))
    items_ligne_panier = mycursor.fetchall()
    if not items_ligne_panier:
        flash(u'Pas d\'articles dans le panier', 'warning')
        return redirect('/client/article/show')

    for item in items_ligne_panier:
        sql_check_stock = '''
        SELECT stock
        FROM cle_usb
        WHERE id_cle_usb = %s
        '''
        mycursor.execute(sql_check_stock, (item['cle_usb_id'],))
        stock = mycursor.fetchone()['stock']
        if stock < item['quantite']:
            flash(u'Stock insuffisant pour l\'article avec l\'ID ' + str(item['cle_usb_id']), 'danger')
            return redirect('/client/commande/valide')

    sql = '''
    INSERT INTO commande (date_achat, utilisateur_id, etat_id, adresse_livraison_id, adresse_facturation_id)
    VALUES (NOW(), %s, 1, %s, %s)
    '''
    mycursor.execute(sql, (id_client, id_adresse_livraison, id_adresse_facturation))
    get_db().commit()

    sql = '''SELECT LAST_INSERT_ID() as last_insert_id'''
    mycursor.execute(sql)
    id_commande = mycursor.fetchone()['last_insert_id']

    for item in items_ligne_panier:
        sql_insert = '''
        INSERT INTO ligne_commande (commande_id, cle_usb_id, prix, quantite)
        VALUES (%s, %s, (SELECT prix_cle_usb FROM cle_usb WHERE id_cle_usb = %s), %s)
        '''
        mycursor.execute(sql_insert, (id_commande, item['cle_usb_id'], item['cle_usb_id'], item['quantite']))

        sql_update_stock = '''
        UPDATE cle_usb
        SET stock = stock - %s
        WHERE id_cle_usb = %s
        '''
        mycursor.execute(sql_update_stock, (item['quantite'], item['cle_usb_id']))

    sql_empty_cart = '''
    DELETE FROM ligne_panier
    WHERE utilisateur_id = %s
    '''
    mycursor.execute(sql_empty_cart, (id_client,))

    get_db().commit()
    flash(u'Commande ajoutée', 'success')
    return redirect('/client/article/show')

@client_commande.route('/client/commande/show')
def client_commande_show():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_commande = request.args.get('id_commande')

    if id_commande:
        sql = '''
        SELECT c.nom_cle_usb, lc.prix, lc.quantite, (lc.prix * lc.quantite) as prix_ligne
        FROM ligne_commande lc
        JOIN cle_usb c ON lc.cle_usb_id = c.id_cle_usb
        WHERE lc.commande_id = %s
        '''
        mycursor.execute(sql, (id_commande,))
        articles_commande = mycursor.fetchall()

        sql = '''
        SELECT c.*, e.libelle as etat_libelle,
               al.nom as nom_livraison, al.rue as rue_livraison, al.code_postal as code_postal_livraison, al.ville as ville_livraison,
               af.nom as nom_facturation, af.rue as rue_facturation, af.code_postal as code_postal_facturation, af.ville as ville_facturation
        FROM commande c
        JOIN etat e ON c.etat_id = e.id_etat
        JOIN adresse al ON c.adresse_livraison_id = al.id_adresse
        LEFT JOIN adresse af ON c.adresse_facturation_id = af.id_adresse
        WHERE c.id_commande = %s AND c.utilisateur_id = %s
        '''
        mycursor.execute(sql, (id_commande, id_client))
        commande = mycursor.fetchone()

        if not commande:
            flash("Commande non trouvée", 'warning')
            return redirect(url_for('client_commande.client_commande_show'))

        adresse_identique = (commande['adresse_livraison_id'] == commande['adresse_facturation_id'])

    sql = '''
    SELECT c.id_commande, c.date_achat, 
           e.libelle, e.id_etat as etat_id,
           SUM(lc.quantite) as nbr_articles,
           SUM(lc.prix * lc.quantite) as prix_total
    FROM commande c
    JOIN etat e ON c.etat_id = e.id_etat
    JOIN ligne_commande lc ON c.id_commande = lc.commande_id
    WHERE c.utilisateur_id = %s
    GROUP BY c.id_commande
    ORDER BY c.date_achat DESC
    '''
    mycursor.execute(sql, (id_client,))
    commandes = mycursor.fetchall()

    return render_template('client/commandes/show.html',
                           articles_commande=articles_commande if id_commande else None,
                           commande=commande if id_commande else None,
                           commandes=commandes,
                           adresse_identique=adresse_identique if id_commande else None)

@client_commande.route('/client/commande/details/<int:id_commande>')
def client_commande_details(id_commande):
    return redirect(url_for('client_commande.client_commande_show', id_commande=id_commande))


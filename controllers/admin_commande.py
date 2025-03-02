#! /usr/bin/python
# -*- coding:utf-8 -*-
from flask import Blueprint
from flask import Flask, request, render_template, redirect, abort, flash, session

from connexion_db import get_db

admin_commande = Blueprint('admin_commande', __name__,
                           template_folder='templates')

@admin_commande.route('/admin/commande/index')
def admin_commande_index():
    return render_template('admin/layout_admin.html')

@admin_commande.route('/admin/commande/show')
def show_commande():
    mycursor = get_db().cursor()
    sql = '''
    SELECT c.id_commande, 
           c.date_achat, 
           u.login as username, 
           COUNT(lc.cle_usb_id) as nb_articles,
           SUM(lc.prix * lc.quantite) as prix_total,
           e.libelle as etat
    FROM commande c
    JOIN utilisateur u ON c.utilisateur_id = u.id_utilisateur
    JOIN etat e ON c.etat_id = e.id_etat
    JOIN ligne_commande lc ON c.id_commande = lc.commande_id
    GROUP BY c.id_commande, c.date_achat, u.login, e.libelle
    ORDER BY c.date_achat DESC
    '''
    mycursor.execute(sql)
    commandes = mycursor.fetchall()

    sql = '''
    SELECT id_etat, libelle
    FROM etat
    ORDER BY libelle
    '''
    mycursor.execute(sql)
    etats = mycursor.fetchall()

    id_commande = request.args.get('id_commande')
    commande_details = None
    articles_commande = None
    adresse_livraison = None
    adresse_facturation = None
    if id_commande:
        sql = '''
        SELECT c.id_commande, c.date_achat, u.login as username, e.libelle as etat,
               COUNT(lc.cle_usb_id) as nb_articles,
               SUM(lc.prix * lc.quantite) as prix_total
        FROM commande c
        JOIN utilisateur u ON c.utilisateur_id = u.id_utilisateur
        JOIN etat e ON c.etat_id = e.id_etat
        JOIN ligne_commande lc ON c.id_commande = lc.commande_id
        WHERE c.id_commande = %s
        GROUP BY c.id_commande, c.date_achat, u.login, e.libelle
        '''
        mycursor.execute(sql, (id_commande,))
        commande_details = mycursor.fetchone()

        sql = '''
        SELECT cl.nom_cle_usb, lc.prix, lc.quantite
        FROM ligne_commande lc
        JOIN cle_usb cl ON lc.cle_usb_id = cl.id_cle_usb
        WHERE lc.commande_id = %s
        '''
        mycursor.execute(sql, (id_commande,))
        articles_commande = mycursor.fetchall()

        sql = '''
        SELECT a.nom, a.rue, a.code_postal, a.ville
        FROM adresse a
        JOIN commande c ON c.adresse_livraison_id = a.id_adresse
        WHERE c.id_commande = %s
        '''
        mycursor.execute(sql, (id_commande,))
        adresse_livraison = mycursor.fetchone()

        sql = '''
        SELECT a.nom, a.rue, a.code_postal, a.ville
        FROM adresse a
        JOIN commande c ON c.adresse_facturation_id = a.id_adresse
        WHERE c.id_commande = %s
        '''
        mycursor.execute(sql, (id_commande,))
        adresse_facturation = mycursor.fetchone()

    return render_template('admin/commandes/show.html',
                           commandes=commandes,
                           etats=etats,
                           commande_details=commande_details,
                           articles_commande=articles_commande,
                           adresse_livraison=adresse_livraison,
                           adresse_facturation=adresse_facturation)

@admin_commande.route('/admin/commande/edit', methods=['POST'])
def edit_commande():
    mycursor = get_db().cursor()
    id_commande = request.form.get('id_commande', '')
    new_etat_id = request.form.get('new_etat_id', '')
    sql = '''
    UPDATE commande
    SET etat_id = %s
    WHERE id_commande = %s
    '''
    mycursor.execute(sql, (new_etat_id, id_commande))
    get_db().commit()
    flash(u'État de la commande modifié', 'success')
    return redirect('/admin/commande/show')
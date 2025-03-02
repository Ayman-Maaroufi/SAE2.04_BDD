#! /usr/bin/python
# -*- coding:utf-8 -*-
from flask import Blueprint
from flask import Flask, request, render_template, redirect, url_for, abort, flash, session, g

from connexion_db import get_db

client_coordonnee = Blueprint('client_coordonnee', __name__,
                              template_folder='templates')
# Sans le VCCD ayman
@client_coordonnee.route('/client/coordonnee/show')
def client_coordonnee_show():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    sql = '''
    SELECT *
    FROM utilisateur
    WHERE id_utilisateur = %s
    '''
    mycursor.execute(sql, (id_client,))
    utilisateur = mycursor.fetchone()

    sql = '''
    SELECT a.*, 
           (
               SELECT COUNT(DISTINCT id_commande)
               FROM (
                   SELECT id_commande, adresse_livraison_id AS adresse_id FROM commande
                   UNION
                   SELECT id_commande, adresse_facturation_id FROM commande
               ) c
               WHERE c.adresse_id = a.id_adresse
           ) AS nbr_commandes
    FROM adresse a
    WHERE a.utilisateur_id = %s
    '''
    mycursor.execute(sql, (id_client,))
    adresses = mycursor.fetchall()
    nb_adresses = len(adresses)
    nb_adresses_tot = len(adresses)

    return render_template('client/coordonnee/show_coordonnee.html',
                           utilisateur=utilisateur,
                           adresses=adresses,
                           nb_adresses=nb_adresses,
                           nb_adresses_tot=nb_adresses_tot)

@client_coordonnee.route('/client/coordonnee/edit', methods=['GET'])
def client_coordonnee_edit():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    sql = '''
    SELECT *
    FROM utilisateur
    WHERE id_utilisateur = %s
    '''
    mycursor.execute(sql, (id_client,))
    utilisateur = mycursor.fetchone()
    return render_template('client/coordonnee/edit_coordonnee.html',
                           utilisateur=utilisateur)

@client_coordonnee.route('/client/coordonnee/edit', methods=['POST'])
def client_coordonnee_edit_valide():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    nom = request.form.get('nom')
    login = request.form.get('login')
    email = request.form.get('email')

    sql = '''
    SELECT *
    FROM utilisateur
    WHERE (email = %s OR login = %s) AND id_utilisateur != %s
    '''
    mycursor.execute(sql, (email, login, id_client))
    utilisateur = mycursor.fetchone()
    if utilisateur:
        flash(u'Cet Email ou ce Login existe déjà pour un autre utilisateur', 'alert-warning')
        return render_template('client/coordonnee/edit_coordonnee.html',
                               utilisateur=utilisateur)

    sql = '''
    UPDATE utilisateur
    SET nom = %s, login = %s, email = %s
    WHERE id_utilisateur = %s
    '''
    mycursor.execute(sql, (nom, login, email, id_client))
    get_db().commit()
    return redirect('/client/coordonnee/show')

@client_coordonnee.route('/client/coordonnee/delete_adresse', methods=['POST'])
def client_coordonnee_delete_adresse():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_adresse = request.form.get('id_adresse')

    sql = '''
    SELECT COUNT(*) as count
    FROM commande
    WHERE adresse_livraison_id = %s OR adresse_facturation_id = %s
    '''
    mycursor.execute(sql, (id_adresse, id_adresse))
    result = mycursor.fetchone()

    if result['count'] > 0:
        flash(u'Cette adresse est utilisée dans une commande et ne peut pas être supprimée', 'alert-warning')
    else:
        sql = '''
        DELETE FROM adresse
        WHERE id_adresse = %s AND utilisateur_id = %s
        '''
        mycursor.execute(sql, (id_adresse, id_client))
        get_db().commit()
        flash(u'Adresse supprimée avec succès', 'alert-success')

    return redirect('/client/coordonnee/show')

@client_coordonnee.route('/client/coordonnee/add_adresse')
def client_coordonnee_add_adresse():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    sql = '''
    SELECT *
    FROM utilisateur
    WHERE id_utilisateur = %s
    '''
    mycursor.execute(sql, (id_client,))
    utilisateur = mycursor.fetchone()
    return render_template('client/coordonnee/add_adresse.html',
                           utilisateur=utilisateur)

@client_coordonnee.route('/client/coordonnee/add_adresse', methods=['POST'])
def client_coordonnee_add_adresse_valide():
    mycursor = get_db().cursor()
    id_client = session['id_user']

    sql = '''
    SELECT COUNT(*) as count
    FROM adresse
    WHERE utilisateur_id = %s
    '''
    mycursor.execute(sql, (id_client,))
    result = mycursor.fetchone()

    if result['count'] >= 4:
        flash(u'Vous avez déjà le nombre maximum d\'adresses (4)', 'alert-warning')
        return redirect('/client/coordonnee/show')

    nom = request.form.get('nom')
    rue = request.form.get('rue')
    code_postal = request.form.get('code_postal')
    ville = request.form.get('ville')
    sql = '''
    INSERT INTO adresse (nom, rue, code_postal, ville, utilisateur_id)
    VALUES (%s, %s, %s, %s, %s)
    '''
    mycursor.execute(sql, (nom, rue, code_postal, ville, id_client))
    get_db().commit()
    flash(u'Adresse ajoutée avec succès', 'alert-success')
    return redirect('/client/coordonnee/show')

@client_coordonnee.route('/client/coordonnee/edit_adresse')
def client_coordonnee_edit_adresse():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_adresse = request.args.get('id_adresse')
    sql = '''
    SELECT *
    FROM adresse
    WHERE id_adresse = %s AND utilisateur_id = %s
    '''
    mycursor.execute(sql, (id_adresse, id_client))
    adresse = mycursor.fetchone()

    sql = '''
    SELECT *
    FROM utilisateur
    WHERE id_utilisateur = %s
    '''
    mycursor.execute(sql, (id_client,))
    utilisateur = mycursor.fetchone()

    return render_template('/client/coordonnee/edit_adresse.html',
                           adresse=adresse,
                           utilisateur=utilisateur)

@client_coordonnee.route('/client/coordonnee/edit_adresse', methods=['POST'])
def client_coordonnee_edit_adresse_valide():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    nom = request.form.get('nom')
    rue = request.form.get('rue')
    code_postal = request.form.get('code_postal')
    ville = request.form.get('ville')
    id_adresse = request.form.get('id_adresse')

    sql = '''
    SELECT COUNT(*) as count
    FROM commande
    WHERE adresse_livraison_id = %s OR adresse_facturation_id = %s
    '''
    mycursor.execute(sql, (id_adresse, id_adresse))
    result = mycursor.fetchone()

    if result['count'] > 0:
        sql = '''
        INSERT INTO adresse (nom, rue, code_postal, ville, utilisateur_id)
        VALUES (%s, %s, %s, %s, %s)
        '''
        mycursor.execute(sql, (nom, rue, code_postal, ville, id_client))
        flash(u'Une nouvelle adresse a été créée car l\'ancienne est utilisée dans une commande', 'alert-info')
    else:
        sql = '''
        UPDATE adresse
        SET nom = %s, rue = %s, code_postal = %s, ville = %s
        WHERE id_adresse = %s AND utilisateur_id = %s
        '''
        mycursor.execute(sql, (nom, rue, code_postal, ville, id_adresse, id_client))
        flash(u'Adresse mise à jour avec succès', 'alert-success')

    get_db().commit()
    return redirect('/client/coordonnee/show')
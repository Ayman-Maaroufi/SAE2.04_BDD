#! /usr/bin/python
# -*- coding:utf-8 -*-
import os
from random import random

from flask import Blueprint
from flask import Flask, request, render_template, redirect, abort, flash, session, url_for

from connexion_db import get_db

admin_article = Blueprint('admin_article', __name__,
                          template_folder='templates')


@admin_article.route('/admin/article/show')
def show_article():
    mycursor = get_db().cursor()
    sql = '''
    SELECT c.id_cle_usb AS id_article, c.nom_cle_usb AS nom, c.prix_cle_usb AS prix, 
           c.stock, c.photo_url AS image, t.libelle_type_cle_usb AS libelle, 
           t.id_type_cle_usb AS type_article_id
    FROM cle_usb c
    LEFT JOIN type_cle_usb t ON c.type_cle_usb_id = t.id_type_cle_usb
    ORDER BY c.id_cle_usb DESC
    '''
    mycursor.execute(sql)
    articles = mycursor.fetchall()

    print(f"Nombre d'articles récupérés : {len(articles)}")
    for article in articles:
        article['nb_commentaires_nouveaux'] = 0
        article['nb_declinaisons'] = 1
        article['prix'] = float(article['prix']) if article['prix'] is not None else 0.0
        article['stock'] = int(article['stock']) if article['stock'] is not None else 0
        print(f"Article : {article}")

    return render_template('admin/article/show_article.html', articles=articles)


@admin_article.route('/admin/article/add', methods=['GET'])
def add_article():
    mycursor = get_db().cursor()
    sql = '''
    SELECT id_type_cle_usb AS id_type_article, libelle_type_cle_usb AS libelle
    FROM type_cle_usb
    ORDER BY libelle_type_cle_usb
    '''
    mycursor.execute(sql)
    types_article = mycursor.fetchall()

    print("Types d'articles récupérés :", types_article)

    return render_template('admin/article/add_article.html',
                           types_article=types_article)


@admin_article.route('/admin/article/add', methods=['POST'])
def valid_add_article():
    mycursor = get_db().cursor()
    nom = request.form.get('nom', '').strip()
    prix = request.form.get('prix', '')
    stock = request.form.get('stock', '')
    type_article_id = request.form.get('type_article_id', '')
    image = request.files.get('image')

    print(f"Données reçues : nom={nom}, prix={prix}, stock={stock}, type_article_id={type_article_id}")

    try:
        prix = float(prix) if prix else 0
        stock = int(stock) if stock else 0
        type_article_id = int(type_article_id) if type_article_id else None
    except ValueError:
        flash(u'Veuillez entrer des valeurs numériques valides pour le prix et le stock', 'error')
        return redirect(url_for('admin_article.add_article'))

    if image:
        filename = 'img_upload' + str(int(2147483647 * random())) + '.png'
        image.save(os.path.join('static/images/', filename))
        print(f"Image sauvegardée : {filename}")
    else:
        filename = None
        print("Pas d'image fournie")

    sql = '''
    INSERT INTO cle_usb (nom_cle_usb, prix_cle_usb, stock, photo_url, type_cle_usb_id)
    VALUES (%s, %s, %s, %s, %s)
    '''
    tuple_add = (nom, prix, stock, filename, type_article_id)
    print(f"SQL : {sql}")
    print(f"Données à insérer : {tuple_add}")

    try:
        mycursor.execute(sql, tuple_add)
        get_db().commit()
        print("Insertion réussie, transaction validée")
        flash(u'Article ajouté', 'success')
    except Exception as e:
        get_db().rollback()
        print(f"Erreur lors de l'insertion : {str(e)}")
        flash(f'Erreur lors de l\'ajout de l\'article : {str(e)}', 'error')
        return redirect(url_for('admin_article.add_article'))

    return redirect(url_for('admin_article.show_article'))


@admin_article.route('/admin/article/delete', methods=['GET'])
def delete_article():
    id_article = request.args.get('id_article', '')
    mycursor = get_db().cursor()

    sql_check = '''
    SELECT COUNT(*) as nb_lignes
    FROM ligne_commande
    WHERE cle_usb_id = %s
    '''
    mycursor.execute(sql_check, (id_article,))
    result = mycursor.fetchone()

    if result['nb_lignes'] > 0:
        flash(u'Impossible de supprimer cet article car il est associé à des commandes', 'warning')
    else:
        sql_image = '''
        SELECT photo_url
        FROM cle_usb
        WHERE id_cle_usb = %s
        '''
        mycursor.execute(sql_image, (id_article,))
        image = mycursor.fetchone()['photo_url']

        sql_delete = '''
        DELETE FROM cle_usb
        WHERE id_cle_usb = %s
        '''
        mycursor.execute(sql_delete, (id_article,))
        get_db().commit()

        if image and os.path.exists(os.path.join('static/images/', image)):
            os.remove(os.path.join('static/images/', image))

        flash(u'Article supprimé', 'success')

    return redirect(url_for('admin_article.show_article'))


@admin_article.route('/admin/article/edit', methods=['GET'])
def edit_article():
    id_article = request.args.get('id_article', '')
    mycursor = get_db().cursor()
    sql = '''
    SELECT id_cle_usb AS id_article, nom_cle_usb AS nom, prix_cle_usb AS prix, stock, 
           photo_url AS image, type_cle_usb_id AS type_article_id
    FROM cle_usb
    WHERE id_cle_usb = %s
    '''
    mycursor.execute(sql, (id_article,))
    article = mycursor.fetchone()

    sql = '''
    SELECT id_type_cle_usb AS id_type_article, libelle_type_cle_usb AS libelle
    FROM type_cle_usb
    ORDER BY libelle_type_cle_usb
    '''
    mycursor.execute(sql)
    types_article = mycursor.fetchall()

    return render_template('admin/article/edit_article.html',
                           article=article,
                           types_article=types_article)


@admin_article.route('/admin/article/edit', methods=['POST'])
def valid_edit_article():
    mycursor = get_db().cursor()
    id_article = request.form.get('id_article', '')
    nom = request.form.get('nom', '')
    prix = request.form.get('prix', '')
    stock = request.form.get('stock', '')
    type_article_id = request.form.get('type_article_id', '')
    image = request.files.get('image')

    try:
        prix = float(prix) if prix else 0
        stock = int(stock) if stock else 0
        type_article_id = int(type_article_id) if type_article_id else None
    except ValueError:
        flash(u'Veuillez entrer des valeurs numériques valides pour le prix et le stock', 'error')
        return redirect(url_for('admin_article.edit_article', id_article=id_article))

    if image:
        sql_old_image = '''
        SELECT photo_url
        FROM cle_usb
        WHERE id_cle_usb = %s
        '''
        mycursor.execute(sql_old_image, (id_article,))
        old_image = mycursor.fetchone()['photo_url']
        if old_image and os.path.exists(os.path.join('static/images/', old_image)):
            os.remove(os.path.join('static/images/', old_image))

        filename = 'img_upload' + str(int(2147483647 * random())) + '.png'
        image.save(os.path.join('static/images/', filename))
    else:
        filename = None

    sql = '''
    UPDATE cle_usb
    SET nom_cle_usb = %s, prix_cle_usb = %s, stock = %s, photo_url = COALESCE(%s, photo_url), 
        type_cle_usb_id = %s
    WHERE id_cle_usb = %s
    '''
    tuple_update = (nom, prix, stock, filename, type_article_id, id_article)
    mycursor.execute(sql, tuple_update)
    get_db().commit()
    flash(u'Article modifié', 'success')
    return redirect(url_for('admin_article.show_article'))


@admin_article.route('/admin/declinaison_article/edit', methods=['GET'])
def edit_declinaison_article():
    id_declinaison_article = request.args.get('id_declinaison_article', '')
    mycursor = get_db().cursor()

    sql = '''
    SELECT d.id_declinaison_article, d.article_id, d.stock, d.taille_id, d.couleur_id,
           c.nom_cle_usb AS nom, c.photo_url AS image_article,
           t.libelle AS libelle_taille, co.libelle AS libelle_couleur
    FROM declinaison_article d
    JOIN cle_usb c ON d.article_id = c.id_cle_usb
    LEFT JOIN taille t ON d.taille_id = t.id_taille
    LEFT JOIN couleur co ON d.couleur_id = co.id_couleur
    WHERE d.id_declinaison_article = %s
    '''
    mycursor.execute(sql, (id_declinaison_article,))
    declinaison_article = mycursor.fetchone()

    sql_tailles = "SELECT id_taille, libelle FROM taille ORDER BY libelle"
    mycursor.execute(sql_tailles)
    tailles = mycursor.fetchall()

    sql_couleurs = "SELECT id_couleur, libelle FROM couleur ORDER BY libelle"
    mycursor.execute(sql_couleurs)
    couleurs = mycursor.fetchall()

    return render_template('admin/article/edit_declinaison_article.html',
                           declinaison_article=declinaison_article,
                           tailles=tailles,
                           couleurs=couleurs)


@admin_article.route('/admin/declinaison_article/edit', methods=['POST'])
def valid_edit_declinaison_article():
    mycursor = get_db().cursor()
    id_declinaison_article = request.form.get('id_declinaison_article', '')
    id_article = request.form.get('id_article', '')
    stock = request.form.get('stock', '')
    id_taille = request.form.get('id_taille', '')
    id_couleur = request.form.get('id_couleur', '')

    try:
        stock = int(stock) if stock else 0
        id_taille = int(id_taille) if id_taille else None
        id_couleur = int(id_couleur) if id_couleur else None
    except ValueError:
        flash(u'Veuillez entrer des valeurs numériques valides', 'error')
        return redirect(
            url_for('admin_article.edit_declinaison_article', id_declinaison_article=id_declinaison_article))

    sql = '''
    UPDATE declinaison_article
    SET stock = %s, taille_id = %s, couleur_id = %s
    WHERE id_declinaison_article = %s
    '''
    tuple_update = (stock, id_taille, id_couleur, id_declinaison_article)
    mycursor.execute(sql, tuple_update)
    get_db().commit()
    flash(u'Déclinaison d\'article modifiée', 'success')
    return redirect(url_for('admin_article.edit_article', id_article=id_article))


@admin_article.route('/admin/article/commentaires')
def show_commentaires():
    id_article = request.args.get('id_article', '')
    return "Fonctionnalité non implémentée"


@admin_article.route('/admin/article/recreate_demo', methods=['GET'])
def recreate_demo_articles():
    mycursor = get_db().cursor()

    sql_check = "SELECT COUNT(*) as count FROM cle_usb"
    mycursor.execute(sql_check)
    result = mycursor.fetchone()

    if result['count'] == 0:
        demo_articles = [
            ("USB 3.0 16GB", 19.99, 100, "usb_16gb.jpg", 1),
            ("USB-C 32GB", 29.99, 75, "usb_c_32gb.jpg", 2),
            ("USB 3.1 64GB", 39.99, 50, "usb_64gb.jpg", 1)
        ]

        sql_insert = '''
        INSERT INTO cle_usb (nom_cle_usb, prix_cle_usb, stock, photo_url, type_cle_usb_id)
        VALUES (%s, %s, %s, %s, %s)
        '''

        for article in demo_articles:
            mycursor.execute(sql_insert, article)

        get_db().commit()
        flash(u'Articles de démonstration recréés', 'success')
    else:
        flash(u'Des articles existent déjà dans la base de données', 'info')

    return redirect(url_for('admin_article.show_article'))


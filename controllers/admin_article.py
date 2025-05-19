#! /usr/bin/python
# -*- coding:utf-8 -*-
from flask import Blueprint
from flask import Flask, request, render_template, redirect, url_for, abort, flash, session, g
import os
from werkzeug.utils import secure_filename
import datetime

from connexion_db import get_db

admin_article = Blueprint('admin_article', __name__,
                          template_folder='templates')


@admin_article.route('/admin/article/show')
def show_article():
    mycursor = get_db().cursor()

    # Récupérer les articles avec leurs informations de base
    sql = '''
    SELECT c.id_cle_usb as id_article, 
           c.nom_cle_usb as nom, 
           c.prix_cle_usb as prix, 
           c.stock, 
           c.description, 
           c.photo_url as image, 
           t.libelle_type_cle_usb as libelle,
           t.id_type_cle_usb as type_article_id
    FROM cle_usb c
    LEFT JOIN type_cle_usb t ON c.type_cle_usb_id = t.id_type_cle_usb
    ORDER BY nom_cle_usb
    '''
    mycursor.execute(sql)
    articles = mycursor.fetchall()

    # Pour chaque article, récupérer le nombre d'avis
    for article in articles:
        # Nombre total de commentaires
        sql_avis = '''
        SELECT COUNT(*) as nb_commentaires_total
        FROM commentaire
        WHERE cle_usb_id = %s
        '''
        mycursor.execute(sql_avis, (article['id_article'],))
        result = mycursor.fetchone()
        article['nb_commentaires_total'] = result['nb_commentaires_total'] if result else 0

        # Nombre de commentaires non lus
        sql_non_lus = '''
        SELECT COUNT(*) as nb_commentaires_nouveaux
        FROM commentaire
        WHERE cle_usb_id = %s AND valider = 0 AND utilisateur_id != 1
        '''
        mycursor.execute(sql_non_lus, (article['id_article'],))
        result = mycursor.fetchone()
        article['nb_commentaires_nouveaux'] = result['nb_commentaires_nouveaux'] if result else 0

        # Nombre de déclinaisons (si nécessaire)
        article['nb_declinaisons'] = 0  # Valeur par défaut

    return render_template('admin/article/show_article.html', articles=articles)


@admin_article.route('/admin/article/add', methods=['GET'])
def add_article():
    mycursor = get_db().cursor()
    sql = '''
    SELECT id_type_cle_usb as id_type_article, libelle_type_cle_usb as libelle
    FROM type_cle_usb
    ORDER BY libelle_type_cle_usb
    '''
    mycursor.execute(sql)
    types_article = mycursor.fetchall()

    return render_template('admin/article/add_article.html', types_article=types_article)


@admin_article.route('/admin/article/add', methods=['POST'])
def valid_add_article():
    mycursor = get_db().cursor()
    nom = request.form.get('nom', '')
    type_article_id = request.form.get('type_article_id', '')
    prix = request.form.get('prix', '')
    stock = request.form.get('stock', '0')  # Valeur par défaut 0
    description = request.form.get('description', '')

    # Gestion de l'image
    image = ""
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            # Pour simplifier, nous utilisons juste le nom du fichier
            image = secure_filename(file.filename)

    # Validation des données
    if not nom:
        flash(u'Erreur: Le nom de l\'article est obligatoire', 'alert-danger')
        return redirect(url_for('admin_article.add_article'))

    if not type_article_id:
        flash(u'Erreur: Le type d\'article est obligatoire', 'alert-danger')
        return redirect(url_for('admin_article.add_article'))

    # Conversion des valeurs numériques
    try:
        type_article_id = int(type_article_id)
        prix = float(prix) if prix else 0
        stock = int(stock) if stock else 0
    except ValueError:
        flash(u'Erreur: Valeurs numériques invalides', 'alert-danger')
        return redirect(url_for('admin_article.add_article'))

    sql = '''
    INSERT INTO cle_usb (nom_cle_usb, prix_cle_usb, stock, description, photo_url, type_cle_usb_id)
    VALUES (%s, %s, %s, %s, %s, %s)
    '''
    tuple_add = (nom, prix, stock, description, image, type_article_id)

    try:
        mycursor.execute(sql, tuple_add)
        get_db().commit()
        message = u'Article ajouté, nom: ' + nom + ', prix: ' + str(prix) + ' €'
        flash(message, 'alert-success')
    except Exception as e:
        flash(u'Erreur lors de l\'ajout de l\'article: ' + str(e), 'alert-danger')

    return redirect(url_for('admin_article.show_article'))


@admin_article.route('/admin/article/delete/<int:id_article>', methods=['GET'])
def delete_article(id_article):
    mycursor = get_db().cursor()

    # Vérifier si l'article existe
    sql = "SELECT nom_cle_usb FROM cle_usb WHERE id_cle_usb = %s"
    mycursor.execute(sql, (id_article,))
    article = mycursor.fetchone()

    if article is None:
        flash(u'Article non trouvé', 'alert-danger')
        return redirect(url_for('admin_article.show_article'))

    try:
        # Supprimer les commentaires associés à l'article
        sql_delete_commentaires = "DELETE FROM commentaire WHERE cle_usb_id = %s"
        mycursor.execute(sql_delete_commentaires, (id_article,))

        # Supprimer l'article
        sql_delete_article = "DELETE FROM cle_usb WHERE id_cle_usb = %s"
        mycursor.execute(sql_delete_article, (id_article,))
        get_db().commit()

        flash(u'Article supprimé, nom: ' + article['nom_cle_usb'], 'alert-success')
    except Exception as e:
        flash(u'Erreur lors de la suppression de l\'article: ' + str(e), 'alert-danger')

    return redirect(url_for('admin_article.show_article'))


@admin_article.route('/admin/article/edit/<int:id_article>', methods=['GET'])
def edit_article(id_article):
    mycursor = get_db().cursor()

    sql = '''
    SELECT id_cle_usb as id_article, nom_cle_usb as nom, prix_cle_usb as prix, stock, description, photo_url as image, type_cle_usb_id as id_type_article
    FROM cle_usb
    WHERE id_cle_usb = %s
    '''
    mycursor.execute(sql, (id_article,))
    article = mycursor.fetchone()

    if article is None:
        flash(u'Article non trouvé', 'alert-danger')
        return redirect(url_for('admin_article.show_article'))

    sql = '''
    SELECT id_type_cle_usb as id_type_article, libelle_type_cle_usb as libelle
    FROM type_cle_usb
    ORDER BY libelle_type_cle_usb
    '''
    mycursor.execute(sql)
    types_article = mycursor.fetchall()

    return render_template('admin/article/edit_article.html', article=article, types_article=types_article)


@admin_article.route('/admin/article/edit', methods=['POST'])
def valid_edit_article():
    mycursor = get_db().cursor()
    id_article = request.form.get('id_article', '')
    nom = request.form.get('nom', '')
    type_article_id = request.form.get('type_article_id', '')
    prix = request.form.get('prix', '')
    stock = request.form.get('stock', '0')
    description = request.form.get('description', '')

    # Gestion de l'image
    image = request.form.get('image_existing', '')  # Récupérer l'image existante si elle existe
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            # Pour simplifier, nous utilisons juste le nom du fichier
            image = secure_filename(file.filename)

    # Validation des données
    if not id_article:
        flash(u'Erreur: ID article manquant', 'alert-danger')
        return redirect(url_for('admin_article.show_article'))

    if not nom:
        flash(u'Erreur: Le nom de l\'article est obligatoire', 'alert-danger')
        return redirect(url_for('admin_article.edit_article', id_article=id_article))

    if not type_article_id:
        flash(u'Erreur: Le type d\'article est obligatoire', 'alert-danger')
        return redirect(url_for('admin_article.edit_article', id_article=id_article))

    # Conversion des valeurs numériques
    try:
        id_article = int(id_article)
        type_article_id = int(type_article_id)
        prix = float(prix) if prix else 0
        stock = int(stock) if stock else 0
    except ValueError:
        flash(u'Erreur: Valeurs numériques invalides', 'alert-danger')
        return redirect(url_for('admin_article.edit_article', id_article=id_article))

    sql = '''
    UPDATE cle_usb
    SET nom_cle_usb = %s, prix_cle_usb = %s, stock = %s, description = %s, photo_url = %s, type_cle_usb_id = %s
    WHERE id_cle_usb = %s
    '''
    tuple_update = (nom, prix, stock, description, image, type_article_id, id_article)

    try:
        mycursor.execute(sql, tuple_update)
        get_db().commit()
        flash(u'Article modifié, nom: ' + nom + ', prix: ' + str(prix) + ' €', 'alert-success')
    except Exception as e:
        flash(u'Erreur lors de la modification de l\'article: ' + str(e), 'alert-danger')

    return redirect(url_for('admin_article.show_article'))


# Alias pour la route show_commentaires (utilisée dans le template)
@admin_article.route('/admin/article/commentaires/<int:id_article>', methods=['GET'])
def show_commentaires(id_article):
    return show_article_commentaires(id_article)


@admin_article.route('/admin/article/commentaires/<int:id_article>', methods=['GET'])
def show_article_commentaires(id_article):
    mycursor = get_db().cursor()

    # Récupérer les informations de l'article
    sql = '''
    SELECT *
    FROM cle_usb
    WHERE id_cle_usb = %s
    '''
    mycursor.execute(sql, (id_article,))
    article = mycursor.fetchone()

    if article is None:
        flash(u'Article non trouvé', 'alert-danger')
        return redirect(url_for('admin_article.show_article'))

    # Récupérer les commentaires de l'article avec le login de l'utilisateur
    sql = '''
    SELECT c.*, u.login
    FROM commentaire c
    JOIN utilisateur u ON c.utilisateur_id = u.id_utilisateur
    WHERE c.cle_usb_id = %s
    ORDER BY c.date_publication DESC
    '''
    mycursor.execute(sql, (id_article,))
    commentaires = mycursor.fetchall()

    # Vérifier que les commentaires ont bien été récupérés
    if commentaires is None:
        commentaires = []  # Initialiser à une liste vide si aucun commentaire n'est trouvé

    # S'assurer que chaque commentaire a un champ 'valider' défini
    for c in commentaires:
        if 'valider' not in c or c['valider'] is None:
            c['valider'] = 0  # Définir à 0 (non lu) par défaut si le champ est manquant ou NULL

    # Calculer les statistiques
    nb_commentaires_total = len(commentaires)
    nb_non_valides = sum(1 for c in commentaires if c.get('valider', 0) == 0 and c['utilisateur_id'] != 1)
    nb_valides = sum(1 for c in commentaires if c.get('valider', 0) == 1 and c['utilisateur_id'] != 1)
    nb_admin_responses = sum(1 for c in commentaires if c['utilisateur_id'] == 1)

    stats = {
        'nb_commentaires_total': nb_commentaires_total,
        'nb_non_valides': nb_non_valides,
        'nb_valides': nb_valides,
        'nb_admin_responses': nb_admin_responses
    }

    # Récupérer les réponses de l'administrateur
    admin_responses = {}
    for c in commentaires:
        if c['utilisateur_id'] == 1:  # Si c'est une réponse d'admin
            # Trouver le commentaire parent (même date ou date antérieure)
            for parent in commentaires:
                if parent['utilisateur_id'] != 1 and parent['date_publication'] <= c['date_publication']:
                    timestamp = parent['date_publication'].strftime('%Y-%m-%d %H:%M:%S')
                    admin_responses[timestamp] = c
                    break

    return render_template('admin/article/show_article_commentaires.html',
                           article=article,
                           commentaires=commentaires,
                           stats=stats,
                           admin_responses=admin_responses,
                           id_article=id_article)


@admin_article.route(
    '/admin/article/commentaire/delete/<int:id_article>/<int:id_utilisateur>/<string:date_publication>',
    methods=['GET'])
def delete_commentaire(id_article, id_utilisateur, date_publication):
    mycursor = get_db().cursor()

    try:
        # Convertir la date_publication de string à datetime
        date_obj = datetime.datetime.strptime(date_publication, '%Y-%m-%d %H:%M:%S')

        # Supprimer le commentaire
        sql_delete = "DELETE FROM commentaire WHERE cle_usb_id = %s AND utilisateur_id = %s AND date_publication = %s"
        mycursor.execute(sql_delete, (id_article, id_utilisateur, date_obj))
        get_db().commit()
        flash(u'Commentaire supprimé', 'alert-success')
    except Exception as e:
        flash(u'Erreur lors de la suppression du commentaire: ' + str(e), 'alert-danger')

    return redirect(url_for('admin_article.show_article_commentaires', id_article=id_article))


@admin_article.route(
    '/admin/article/commentaire/valider/<int:id_article>/<int:id_utilisateur>/<string:date_publication>',
    methods=['GET'])
def valider_commentaire(id_article, id_utilisateur, date_publication):
    mycursor = get_db().cursor()

    try:
        # Convertir la date_publication de string à datetime
        date_obj = datetime.datetime.strptime(date_publication, '%Y-%m-%d %H:%M:%S')

        # Valider le commentaire
        sql_update = "UPDATE commentaire SET valider = 1 WHERE cle_usb_id = %s AND utilisateur_id = %s AND date_publication = %s"
        mycursor.execute(sql_update, (id_article, id_utilisateur, date_obj))
        get_db().commit()
        flash(u'Commentaire validé', 'alert-success')
    except Exception as e:
        flash(u'Erreur lors de la validation du commentaire: ' + str(e), 'alert-danger')

    return redirect(url_for('admin_article.show_article_commentaires', id_article=id_article))
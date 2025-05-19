#! /usr/bin/python
# -*- coding:utf-8 -*-
from flask import Blueprint
from flask import Flask, request, render_template, redirect, url_for, abort, flash, session, g
from datetime import datetime
from connexion_db import get_db

client_commentaire = Blueprint('client_commentaire', __name__,
                               template_folder='templates')


@client_commentaire.route('/client/article/details', methods=['GET'])
def client_article_details():
    mycursor = get_db().cursor()
    id_article = request.args.get('id_article', None)
    id_client = session['id_user']

    # Récupération des informations de l'article
    sql = '''
    SELECT c.*, t.libelle_type_cle_usb
    FROM cle_usb c
    JOIN type_cle_usb t ON c.type_cle_usb_id = t.id_type_cle_usb
    WHERE c.id_cle_usb = %s
    '''
    mycursor.execute(sql, (id_article,))
    article = mycursor.fetchone()

    # Récupération des statistiques sur les commentaires
    sql = '''
    SELECT 
        COUNT(CASE WHEN utilisateur_id = %s AND commentaire IS NOT NULL THEN 1 END) AS nb_commentaires_user,
        COUNT(CASE WHEN commentaire IS NOT NULL THEN 1 END) AS nb_commentaires_total,
        COUNT(CASE WHEN valider = 1 AND commentaire IS NOT NULL THEN 1 END) AS nb_commentaires_valides,
        COUNT(CASE WHEN utilisateur_id = %s AND valider = 1 AND commentaire IS NOT NULL THEN 1 END) AS nb_commentaires_user_valides,
        AVG(note) AS note_moyenne,
        COUNT(DISTINCT CASE WHEN note IS NOT NULL THEN utilisateur_id END) AS nb_notes
    FROM commentaire
    WHERE cle_usb_id = %s
    '''
    mycursor.execute(sql, (id_client, id_client, id_article))
    stats = mycursor.fetchone()

    # Récupération des commentaires ordonnés chronologiquement (du plus récent au plus ancien)
    sql = '''
    SELECT c.*, u.login, u.nom
    FROM commentaire c
    JOIN utilisateur u ON c.utilisateur_id = u.id_utilisateur
    WHERE c.cle_usb_id = %s AND c.commentaire IS NOT NULL
    ORDER BY c.date_publication DESC
    '''
    mycursor.execute(sql, (id_article,))
    commentaires = mycursor.fetchall()

    # Vérification si l'utilisateur a déjà acheté cet article
    sql = '''
    SELECT COUNT(*) as a_achete
    FROM ligne_commande lc
    JOIN commande c ON lc.commande_id = c.id_commande
    WHERE c.utilisateur_id = %s AND lc.cle_usb_id = %s
    '''
    mycursor.execute(sql, (id_client, id_article))
    achat = mycursor.fetchone()

    # Récupération de la note de l'utilisateur pour cet article
    sql = '''
    SELECT note
    FROM commentaire
    WHERE utilisateur_id = %s AND cle_usb_id = %s AND note IS NOT NULL
    '''
    mycursor.execute(sql, (id_client, id_article))
    note_result = mycursor.fetchone()
    note = note_result['note'] if note_result else None

    return render_template('client/article_info/article_details.html',
                           article=article,
                           commentaires=commentaires,
                           achat=achat,
                           note=note,
                           stats=stats)


@client_commentaire.route('/client/commentaire/add', methods=['POST'])
def client_comment_add():
    mycursor = get_db().cursor()
    commentaire = request.form.get('commentaire', None)
    id_client = session['id_user']
    id_article = request.form.get('id_article', None)

    # Validation du commentaire
    if commentaire == '':
        flash(u'Commentaire non prise en compte')
        return redirect('/client/article/details?id_article=' + id_article)
    if commentaire != None and len(commentaire) > 0 and len(commentaire) < 3:
        flash(u'Commentaire avec plus de 2 caractères', 'alert-warning')
        return redirect('/client/article/details?id_article=' + id_article)

    # Vérifier si l'utilisateur a acheté l'article
    sql = '''
    SELECT COUNT(*) as a_achete
    FROM ligne_commande lc
    JOIN commande c ON lc.commande_id = c.id_commande
    WHERE c.utilisateur_id = %s AND lc.cle_usb_id = %s
    '''
    mycursor.execute(sql, (id_client, id_article))
    achat = mycursor.fetchone()

    if not achat or achat['a_achete'] <= 0:
        flash(u'Vous devez acheter cet article avant de pouvoir le commenter', 'alert-danger')
        return redirect('/client/article/details?id_article=' + id_article)

    # Vérifier le quota de commentaires (max 3)
    sql = '''
    SELECT COUNT(*) AS nb_commentaires
    FROM commentaire
    WHERE utilisateur_id = %s AND cle_usb_id = %s AND commentaire IS NOT NULL
    '''
    mycursor.execute(sql, (id_client, id_article))
    quota = mycursor.fetchone()

    if quota and quota['nb_commentaires'] >= 3:
        flash(u'Vous avez atteint le quota maximum de 3 commentaires pour cet article', 'alert-warning')
        return redirect('/client/article/details?id_article=' + id_article)

    # Ajouter le commentaire
    tuple_insert = (commentaire, id_client, id_article)
    sql = '''
    INSERT INTO commentaire (commentaire, utilisateur_id, cle_usb_id, date_publication, valider)
    VALUES (%s, %s, %s, NOW(), 0)
    '''
    mycursor.execute(sql, tuple_insert)
    get_db().commit()
    flash(u'Commentaire ajouté avec succès', 'alert-success')
    return redirect('/client/article/details?id_article=' + id_article)


@client_commentaire.route('/client/commentaire/delete', methods=['POST'])
def client_comment_detete():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_article = request.form.get('id_article', None)
    date_publication = request.form.get('date_publication', None)

    # Vérifier que l'utilisateur est bien le propriétaire du commentaire
    sql = '''
    SELECT *
    FROM commentaire
    WHERE utilisateur_id = %s AND cle_usb_id = %s AND date_publication = %s
    '''
    mycursor.execute(sql, (id_client, id_article, date_publication))
    commentaire = mycursor.fetchone()

    if not commentaire:
        flash(u'Vous ne pouvez pas supprimer ce commentaire', 'alert-danger')
        return redirect('/client/article/details?id_article=' + id_article)

    # Supprimer le commentaire
    sql = '''
    DELETE FROM commentaire
    WHERE utilisateur_id = %s AND cle_usb_id = %s AND date_publication = %s
    '''
    tuple_delete = (id_client, id_article, date_publication)
    mycursor.execute(sql, tuple_delete)
    get_db().commit()
    flash(u'Commentaire supprimé avec succès', 'alert-success')
    return redirect('/client/article/details?id_article=' + id_article)


@client_commentaire.route('/client/note/add', methods=['POST'])
def client_note_add():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    note = request.form.get('note', None)
    id_article = request.form.get('id_article', None)

    # Vérifier si l'utilisateur a acheté l'article
    sql = '''
    SELECT COUNT(*) as a_achete
    FROM ligne_commande lc
    JOIN commande c ON lc.commande_id = c.id_commande
    WHERE c.utilisateur_id = %s AND lc.cle_usb_id = %s
    '''
    mycursor.execute(sql, (id_client, id_article))
    achat = mycursor.fetchone()

    if not achat or achat['a_achete'] <= 0:
        flash(u'Vous devez acheter cet article avant de pouvoir le noter', 'alert-danger')
        return redirect('/client/article/details?id_article=' + id_article)

    # Vérifier si l'utilisateur a déjà noté cet article
    sql = '''
    SELECT *
    FROM commentaire
    WHERE utilisateur_id = %s AND cle_usb_id = %s AND note IS NOT NULL
    '''
    mycursor.execute(sql, (id_client, id_article))
    existing_note = mycursor.fetchone()

    if existing_note:
        flash(u'Vous avez déjà noté cet article. Utilisez la fonction de modification.', 'alert-warning')
        return redirect('/client/article/details?id_article=' + id_article)

    # Ajouter la note
    tuple_insert = (note, id_client, id_article)
    sql = '''
    INSERT INTO commentaire (note, utilisateur_id, cle_usb_id, date_publication, valider)
    VALUES (%s, %s, %s, NOW(), 1)
    '''
    mycursor.execute(sql, tuple_insert)
    get_db().commit()
    flash(u'Note ajoutée avec succès', 'alert-success')
    return redirect('/client/article/details?id_article=' + id_article)


@client_commentaire.route('/client/note/edit', methods=['POST'])
def client_note_edit():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    note = request.form.get('note', None)
    id_article = request.form.get('id_article', None)

    # Vérifier si l'utilisateur a une note existante
    sql = '''
    SELECT *
    FROM commentaire
    WHERE utilisateur_id = %s AND cle_usb_id = %s AND note IS NOT NULL
    '''
    mycursor.execute(sql, (id_client, id_article))
    existing_note = mycursor.fetchone()

    if not existing_note:
        flash(u'Vous n\'avez pas encore noté cet article. Utilisez la fonction d\'ajout.', 'alert-warning')
        return redirect('/client/article/details?id_article=' + id_article)

    # Mettre à jour la note
    tuple_update = (note, id_client, id_article)
    sql = '''
    UPDATE commentaire
    SET note = %s
    WHERE utilisateur_id = %s AND cle_usb_id = %s AND note IS NOT NULL
    '''
    mycursor.execute(sql, tuple_update)
    get_db().commit()
    flash(u'Note mise à jour avec succès', 'alert-success')
    return redirect('/client/article/details?id_article=' + id_article)


@client_commentaire.route('/client/note/delete', methods=['POST'])
def client_note_delete():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_article = request.form.get('id_article', None)

    # Vérifier si l'utilisateur a une note existante
    sql = '''
    SELECT *
    FROM commentaire
    WHERE utilisateur_id = %s AND cle_usb_id = %s AND note IS NOT NULL
    '''
    mycursor.execute(sql, (id_client, id_article))
    existing_note = mycursor.fetchone()

    if not existing_note:
        flash(u'Vous n\'avez pas encore noté cet article.', 'alert-warning')
        return redirect('/client/article/details?id_article=' + id_article)

    # Supprimer la note
    tuple_delete = (id_client, id_article)
    sql = '''
    UPDATE commentaire
    SET note = NULL
    WHERE utilisateur_id = %s AND cle_usb_id = %s AND note IS NOT NULL
    '''
    mycursor.execute(sql, tuple_delete)
    get_db().commit()
    flash(u'Note supprimée avec succès', 'alert-success')
    return redirect('/client/article/details?id_article=' + id_article)
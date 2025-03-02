#! /usr/bin/python
# -*- coding:utf-8 -*-
from flask import Blueprint
from flask import Flask, request, render_template, redirect, url_for, abort, flash, session, g

from connexion_db import get_db

from controllers.client_liste_envies import client_historique_add

client_commentaire = Blueprint('client_commentaire', __name__,
                        template_folder='templates')


@client_commentaire.route('/client/article/details', methods=['GET'])
def client_article_details():
    mycursor = get_db().cursor()
    id_article =  request.args.get('id_article', None)
    id_client = session['id_user']

    ## partie 4

    sql = '''
    SELECT c.*, t.libelle_type_cle_usb
    FROM cle_usb c
    JOIN type_cle_usb t ON c.type_cle_usb_id = t.id_type_cle_usb
    WHERE c.id_cle_usb = %s
    '''
    mycursor.execute(sql, (id_article,))
    article = mycursor.fetchone()

    sql = '''
    SELECT u.login, com.date_publication, com.commentaire
    FROM commentaire com
    JOIN utilisateur u ON com.utilisateur_id = u.id_utilisateur
    WHERE com.cle_usb_id = %s
    ORDER BY com.date_publication DESC
    '''
    mycursor.execute(sql, (id_article,))
    commentaires = mycursor.fetchall()

    sql = '''
    SELECT COUNT(*) as nb_commandes
    FROM ligne_commande lc
    JOIN commande c ON lc.commande_id = c.id_commande
    WHERE c.utilisateur_id = %s AND lc.cle_usb_id = %s
    '''
    mycursor.execute(sql, (id_client, id_article))
    commandes_articles = mycursor.fetchone()

    sql = '''
    SELECT note
    FROM commentaire
    WHERE utilisateur_id = %s AND cle_usb_id = %s
    '''
    mycursor.execute(sql, (id_client, id_article))
    note = mycursor.fetchone()
    if note:
        note = note['note']

    sql = '''
    SELECT COUNT(*) as nb_commentaires
    FROM commentaire
    WHERE cle_usb_id = %s
    '''
    mycursor.execute(sql, (id_article,))
    nb_commentaires = mycursor.fetchone()['nb_commentaires']

    return render_template('client/article_info/article_details.html'
                           , article=article
                           , commentaires=commentaires
                           , commandes_articles=commandes_articles
                           , note=note
                           , nb_commentaires=nb_commentaires
                           )

@client_commentaire.route('/client/commentaire/add', methods=['POST'])
def client_comment_add():
    mycursor = get_db().cursor()
    commentaire = request.form.get('commentaire', None)
    id_client = session['id_user']
    id_article = request.form.get('id_article', None)
    if commentaire == '':
        flash(u'Commentaire non prise en compte')
        return redirect('/client/article/details?id_article='+id_article)
    if commentaire != None and len(commentaire)>0 and len(commentaire) <3 :
        flash(u'Commentaire avec plus de 2 caractères','alert-warning')
        return redirect('/client/article/details?id_article='+id_article)

    tuple_insert = (commentaire, id_client, id_article)
    print(tuple_insert)
    sql = '''
    INSERT INTO commentaire (commentaire, utilisateur_id, cle_usb_id, date_publication)
    VALUES (%s, %s, %s, NOW())
    '''
    mycursor.execute(sql, tuple_insert)
    get_db().commit()
    return redirect('/client/article/details?id_article='+id_article)


@client_commentaire.route('/client/commentaire/delete', methods=['POST'])
def client_comment_detete():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_article = request.form.get('id_article', None)
    date_publication = request.form.get('date_publication', None)
    sql = '''
    DELETE FROM commentaire
    WHERE utilisateur_id = %s AND cle_usb_id = %s AND date_publication = %s
    '''
    tuple_delete=(id_client,id_article,date_publication)
    mycursor.execute(sql, tuple_delete)
    get_db().commit()
    return redirect('/client/article/details?id_article='+id_article)

@client_commentaire.route('/client/note/add', methods=['POST'])
def client_note_add():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    note = request.form.get('note', None)
    id_article = request.form.get('id_article', None)
    tuple_insert = (note, id_client, id_article)
    print(tuple_insert)
    sql = '''
    INSERT INTO commentaire (note, utilisateur_id, cle_usb_id, date_publication)
    VALUES (%s, %s, %s, NOW())
    '''
    mycursor.execute(sql, tuple_insert)
    get_db().commit()
    return redirect('/client/article/details?id_article='+id_article)

@client_commentaire.route('/client/note/edit', methods=['POST'])
def client_note_edit():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    note = request.form.get('note', None)
    id_article = request.form.get('id_article', None)
    tuple_update = (note, id_client, id_article)
    print(tuple_update)
    sql = '''
    UPDATE commentaire
    SET note = %s
    WHERE utilisateur_id = %s AND cle_usb_id = %s
    '''
    mycursor.execute(sql, tuple_update)
    get_db().commit()
    return redirect('/client/article/details?id_article='+id_article)

@client_commentaire.route('/client/note/delete', methods=['POST'])
def client_note_delete():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_article = request.form.get('id_article', None)
    tuple_delete = (id_client, id_article)
    print(tuple_delete)
    sql = '''
    UPDATE commentaire
    SET note = NULL
    WHERE utilisateur_id = %s AND cle_usb_id = %s
    '''
    mycursor.execute(sql, tuple_delete)
    get_db().commit()
    return redirect('/client/article/details?id_article='+id_article)
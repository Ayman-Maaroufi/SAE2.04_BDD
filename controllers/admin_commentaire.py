#! /usr/bin/python
# -*- coding:utf-8 -*-
from flask import Blueprint
from flask import Flask, request, render_template, redirect, abort, flash, session

from connexion_db import get_db

admin_commentaire = Blueprint('admin_commentaire', __name__,
                              template_folder='templates')


@admin_commentaire.route('/admin/article/commentaires', methods=['GET'])
def admin_article_details():
    mycursor = get_db().cursor()
    id_article = request.args.get('id_article', None)
    sql = '''
    SELECT u.login, c.date_publication, c.commentaire, c.note
    FROM commentaire c
    JOIN utilisateur u ON c.utilisateur_id = u.id_utilisateur
    WHERE c.cle_usb_id = %s
    ORDER BY c.date_publication DESC
    '''
    mycursor.execute(sql, (id_article,))
    commentaires = mycursor.fetchall()

    sql = '''
    SELECT nom_cle_usb, description, prix_cle_usb
    FROM cle_usb
    WHERE id_cle_usb = %s
    '''
    mycursor.execute(sql, (id_article,))
    article = mycursor.fetchone()

    sql = '''
    SELECT COUNT(*) as nb_commentaires
    FROM commentaire
    WHERE cle_usb_id = %s
    '''
    mycursor.execute(sql, (id_article,))
    nb_commentaires = mycursor.fetchone()['nb_commentaires']

    return render_template('admin/article/show_article_commentaires.html'
                           , commentaires=commentaires
                           , article=article
                           , nb_commentaires=nb_commentaires
                           )


@admin_commentaire.route('/admin/article/commentaires/delete', methods=['POST'])
def admin_comment_delete():
    mycursor = get_db().cursor()
    id_utilisateur = request.form.get('id_utilisateur', None)
    id_article = request.form.get('id_article', None)
    date_publication = request.form.get('date_publication', None)
    sql = '''
    DELETE FROM commentaire
    WHERE utilisateur_id = %s AND cle_usb_id = %s AND date_publication = %s
    '''
    tuple_delete = (id_utilisateur, id_article, date_publication)
    mycursor.execute(sql, tuple_delete)
    get_db().commit()
    return redirect('/admin/article/commentaires?id_article=' + id_article)


@admin_commentaire.route('/admin/article/commentaires/repondre', methods=['POST', 'GET'])
def admin_comment_add():
    if request.method == 'GET':
        id_utilisateur = request.args.get('id_utilisateur', None)
        id_article = request.args.get('id_article', None)
        date_publication = request.args.get('date_publication', None)
        return render_template('admin/article/add_commentaire.html', id_utilisateur=id_utilisateur,
                               id_article=id_article, date_publication=date_publication)

    mycursor = get_db().cursor()
    id_utilisateur = session['id_user']  # 1 admin
    id_article = request.form.get('id_article', None)
    date_publication = request.form.get('date_publication', None)
    commentaire = request.form.get('commentaire', None)
    sql = '''
    INSERT INTO commentaire (utilisateur_id, cle_usb_id, date_publication, commentaire)
    VALUES (%s, %s, NOW(), %s)
    '''
    mycursor.execute(sql, (id_utilisateur, id_article, commentaire))
    get_db().commit()
    return redirect('/admin/article/commentaires?id_article=' + id_article)


@admin_commentaire.route('/admin/article/commentaires/valider', methods=['POST', 'GET'])
def admin_comment_valider():
    id_article = request.args.get('id_article', None)
    mycursor = get_db().cursor()
    sql = '''
    UPDATE commentaire
    SET est_valide = 1
    WHERE cle_usb_id = %s
    '''
    mycursor.execute(sql, (id_article,))
    get_db().commit()
    return redirect('/admin/article/commentaires?id_article=' + id_article)
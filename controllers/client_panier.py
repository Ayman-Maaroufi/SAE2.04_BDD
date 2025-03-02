#! /usr/bin/python
# -*- coding:utf-8 -*-
from flask import Blueprint
from flask import request, render_template, redirect, abort, flash, session, url_for

from connexion_db import get_db

client_panier = Blueprint('client_panier', __name__,
                          template_folder='templates')


@client_panier.route('/client/panier/add', methods=['POST'])
def client_panier_add():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_article = request.form.get('id_article')
    quantite = int(request.form.get('quantite', 1))

    sql = '''
    SELECT stock
    FROM cle_usb
    WHERE id_cle_usb = %s
    '''
    mycursor.execute(sql, (id_article,))
    stock_disponible = mycursor.fetchone()['stock']

    if stock_disponible < quantite:
        flash(f"Stock insuffisant. Il reste seulement {stock_disponible} unités.", 'warning')
        return redirect(url_for('client_article.client_article_show'))

    sql = '''
    SELECT *
    FROM ligne_panier
    WHERE utilisateur_id = %s AND cle_usb_id = %s
    '''
    mycursor.execute(sql, (id_client, id_article))
    article_panier = mycursor.fetchone()

    if article_panier is None:
        sql = '''
        INSERT INTO ligne_panier (utilisateur_id, cle_usb_id, quantite)
        VALUES (%s, %s, %s)
        '''
        mycursor.execute(sql, (id_client, id_article, quantite))
    else:
        sql = '''
        UPDATE ligne_panier
        SET quantite = quantite + %s
        WHERE utilisateur_id = %s AND cle_usb_id = %s
        '''
        mycursor.execute(sql, (quantite, id_client, id_article))

    sql = '''
    UPDATE cle_usb
    SET stock = stock - %s
    WHERE id_cle_usb = %s
    '''
    mycursor.execute(sql, (quantite, id_article))

    get_db().commit()
    flash("Article ajouté au panier avec succès", "success")
    return redirect('/client/article/show')


@client_panier.route('/client/panier/delete', methods=['POST'])
def client_panier_delete():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_article = request.form.get('id_article', '')
    quantite = 1

    sql = '''
    SELECT *
    FROM ligne_panier
    WHERE utilisateur_id = %s AND cle_usb_id = %s
    '''
    mycursor.execute(sql, (id_client, id_article))
    article_panier = mycursor.fetchone()

    if article_panier and article_panier['quantite'] > 1:
        sql = '''
        UPDATE ligne_panier
        SET quantite = quantite - 1
        WHERE utilisateur_id = %s AND cle_usb_id = %s
        '''
        mycursor.execute(sql, (id_client, id_article))
    else:
        sql = '''
        DELETE FROM ligne_panier
        WHERE utilisateur_id = %s AND cle_usb_id = %s
        '''
        mycursor.execute(sql, (id_client, id_article))

    sql = '''
    UPDATE cle_usb
    SET stock = stock + 1
    WHERE id_cle_usb = %s
    '''
    mycursor.execute(sql, (id_article,))

    get_db().commit()
    flash("Article retiré du panier", "success")
    return redirect('/client/article/show')


@client_panier.route('/client/panier/vider', methods=['POST'])
def client_panier_vider():
    mycursor = get_db().cursor()
    client_id = session['id_user']
    sql = '''
    SELECT cle_usb_id, quantite
    FROM ligne_panier
    WHERE utilisateur_id = %s
    '''
    mycursor.execute(sql, (client_id,))
    items_panier = mycursor.fetchall()
    for item in items_panier:
        sql = '''
        DELETE FROM ligne_panier
        WHERE utilisateur_id = %s AND cle_usb_id = %s
        '''
        mycursor.execute(sql, (client_id, item['cle_usb_id']))

        sql2 = '''
        UPDATE cle_usb
        SET stock = stock + %s
        WHERE id_cle_usb = %s
        '''
        mycursor.execute(sql2, (item['quantite'], item['cle_usb_id']))
        get_db().commit()
    flash("Panier vidé avec succès", "success")
    return redirect('/client/article/show')


@client_panier.route('/client/panier/delete/line', methods=['POST'])
def client_panier_delete_line():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_article = request.form.get('id_article')

    sql = '''
    SELECT quantite
    FROM ligne_panier
    WHERE utilisateur_id = %s AND cle_usb_id = %s
    '''
    mycursor.execute(sql, (id_client, id_article))
    ligne_panier = mycursor.fetchone()

    sql = '''
    DELETE FROM ligne_panier
    WHERE utilisateur_id = %s AND cle_usb_id = %s
    '''
    mycursor.execute(sql, (id_client, id_article))

    sql2 = '''
    UPDATE cle_usb
    SET stock = stock + %s
    WHERE id_cle_usb = %s
    '''
    mycursor.execute(sql2, (ligne_panier['quantite'], id_article))

    get_db().commit()
    flash("Ligne du panier supprimée", "success")
    return redirect('/client/article/show')


@client_panier.route('/client/panier/confirmer', methods=['GET'])
def confirmer_panier():
    mycursor = get_db().cursor()
    id_client = session['id_user']

    sql = '''
    SELECT c.id_cle_usb, c.nom_cle_usb, c.prix_cle_usb, lp.quantite
    FROM ligne_panier lp
    JOIN cle_usb c ON lp.cle_usb_id = c.id_cle_usb
    WHERE lp.utilisateur_id = %s
    '''
    mycursor.execute(sql, (id_client,))
    articles = mycursor.fetchall()

    total = sum(article['prix_cle_usb'] * article['quantite'] for article in articles)

    return render_template('client/panier/confirmer.html', articles=articles, total=total)


@client_panier.route('/client/panier/filtre', methods=['POST'])
def client_panier_filtre():
    filter_word = request.form.get('filter_word', None)
    filter_prix_min = request.form.get('filter_prix_min', None)
    filter_prix_max = request.form.get('filter_prix_max', None)
    filter_types = request.form.getlist('filter_types', None)

    session['filter_word'] = filter_word
    session['filter_prix_min'] = filter_prix_min
    session['filter_prix_max'] = filter_prix_max
    session['filter_types'] = filter_types

    return redirect('/client/article/show')


@client_panier.route('/client/panier/filtre/suppr', methods=['POST'])
def client_panier_filtre_suppr():
    session.pop('filter_word', None)
    session.pop('filter_prix_min', None)
    session.pop('filter_prix_max', None)
    session.pop('filter_types', None)
    flash("Filtres supprimés", "info")
    return redirect('/client/article/show')
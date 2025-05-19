#! /usr/bin/python
# -*- coding:utf-8 -*-
from flask import Blueprint
from flask import Flask, request, render_template, redirect, url_for, abort, flash, session, g

from connexion_db import get_db

admin_dataviz = Blueprint('admin_dataviz', __name__,
                          template_folder='templates')


@admin_dataviz.route('/admin/dataviz/etat1')
def show_dataviz_etat1():
    """
    Visualisation des données sur les commentaires par type d'article
    """
    mycursor = get_db().cursor()

    # Récupérer les statistiques par type d'article
    sql = '''
    SELECT 
        t.id_type_cle_usb as id_type_article,
        t.libelle_type_cle_usb as libelle,
        COUNT(DISTINCT c.id_cle_usb) as nbr_articles,
        COUNT(com.commentaire) as nb_commentaires,
        COUNT(com.note) as nb_notes,
        ROUND(AVG(com.note), 1) as note_moyenne
    FROM type_cle_usb t
    LEFT JOIN cle_usb c ON t.id_type_cle_usb = c.type_cle_usb_id
    LEFT JOIN commentaire com ON c.id_cle_usb = com.cle_usb_id
    GROUP BY t.id_type_cle_usb, t.libelle_type_cle_usb
    ORDER BY t.libelle_type_cle_usb
    '''
    mycursor.execute(sql)
    types_articles_nb = mycursor.fetchall()

    # Préparer les données pour les graphiques
    labels = []
    values = []  # Nombre de commentaires
    notes_moyennes = []
    nb_notes = []

    for stat in types_articles_nb:
        labels.append(stat['libelle'])
        values.append(stat['nb_commentaires'])
        notes_moyennes.append(float(stat['note_moyenne']) if stat['note_moyenne'] else 0)
        nb_notes.append(stat['nb_notes'])

    return render_template('admin/dataviz/dataviz_etat_1.html',
                           types_articles_nb=types_articles_nb,
                           labels=labels,
                           values=values,
                           notes_moyennes=notes_moyennes,
                           nb_notes=nb_notes,
                           mode='commentaires')


@admin_dataviz.route('/admin/dataviz/etat1/type/<int:id_type>')
def show_dataviz_etat1_by_type(id_type):
    """
    Visualisation détaillée des commentaires pour un type d'article spécifique
    """
    mycursor = get_db().cursor()

    # Récupérer le type sélectionné
    sql = '''
    SELECT id_type_cle_usb as id_type_article, libelle_type_cle_usb as libelle
    FROM type_cle_usb
    WHERE id_type_cle_usb = %s
    '''
    mycursor.execute(sql, (id_type,))
    selected_type = mycursor.fetchone()

    if not selected_type:
        flash(u'Type d\'article non trouvé', 'alert-danger')
        return redirect(url_for('admin_dataviz.show_dataviz_etat1'))

    # Récupérer tous les types pour le menu déroulant
    sql = '''
    SELECT id_type_cle_usb as id_type_article, libelle_type_cle_usb as libelle
    FROM type_cle_usb
    ORDER BY libelle_type_cle_usb
    '''
    mycursor.execute(sql)
    types = mycursor.fetchall()

    # Récupérer les statistiques par article pour le type sélectionné
    sql = '''
    SELECT 
        c.id_cle_usb as id_article,
        c.nom_cle_usb as libelle,
        COUNT(com.commentaire) as nb_commentaires,
        COUNT(com.note) as nb_notes,
        ROUND(AVG(com.note), 1) as note_moyenne
    FROM cle_usb c
    LEFT JOIN commentaire com ON c.id_cle_usb = com.cle_usb_id
    WHERE c.type_cle_usb_id = %s
    GROUP BY c.id_cle_usb, c.nom_cle_usb
    ORDER BY c.nom_cle_usb
    '''
    mycursor.execute(sql, (id_type,))
    articles_stats = mycursor.fetchall()

    # Préparer les données pour les graphiques
    labels = []
    values = []  # Nombre de commentaires
    notes_moyennes = []
    nb_notes = []

    for stat in articles_stats:
        labels.append(stat['libelle'])
        values.append(stat['nb_commentaires'])
        notes_moyennes.append(float(stat['note_moyenne']) if stat['note_moyenne'] else 0)
        nb_notes.append(stat['nb_notes'])

    return render_template('admin/dataviz/dataviz_etat_1.html',
                           selected_type=selected_type,
                           types=types,
                           types_articles_nb=articles_stats,
                           labels=labels,
                           values=values,
                           notes_moyennes=notes_moyennes,
                           nb_notes=nb_notes,
                           mode='commentaires_by_type')


@admin_dataviz.route('/admin/dataviz/etat2')
def show_dataviz_etat2():
    """
    Affiche la carte de France (fonctionnalité existante)
    """
    # Code existant pour la visualisation de la carte
    return render_template('admin/dataviz/dataviz_etat_map.html')
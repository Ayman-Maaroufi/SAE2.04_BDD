from flask import Blueprint, request, render_template, redirect, url_for, flash, session

from connexion_db import get_db

admin_commentaire = Blueprint('admin_commentaire', __name__,
                              template_folder='templates')


@admin_commentaire.route('/admin/comment/valider', methods=['POST'])
def admin_comment_valider():
    mycursor = get_db().cursor()
    id_utilisateur = request.form.get('id_utilisateur', '')
    id_article = request.form.get('id_article', '')
    date_publication = request.form.get('date_publication', '')

    # Mettre à jour le commentaire pour le marquer comme lu
    sql = '''
    UPDATE commentaire
    SET valider = 1
    WHERE utilisateur_id = %s AND cle_usb_id = %s AND date_publication = %s
    '''
    mycursor.execute(sql, (id_utilisateur, id_article, date_publication))
    get_db().commit()

    # Ajouter un message de confirmation
    flash("Le commentaire a été marqué comme lu avec succès.", "success")

    # Rediriger vers la page des commentaires de l'article
    return redirect(url_for('admin_article.show_article_commentaires', id_article=id_article))


@admin_commentaire.route('/admin/comment/delete', methods=['POST'])
def admin_comment_delete():
    mycursor = get_db().cursor()
    id_utilisateur = request.form.get('id_utilisateur', '')
    id_article = request.form.get('id_article', '')
    date_publication = request.form.get('date_publication', '')

    # Supprimer le commentaire
    sql = '''
    DELETE FROM commentaire
    WHERE utilisateur_id = %s AND cle_usb_id = %s AND date_publication = %s
    '''
    mycursor.execute(sql, (id_utilisateur, id_article, date_publication))
    get_db().commit()

    # Ajouter un message de confirmation
    flash("Le commentaire a été supprimé avec succès.", "success")

    # Rediriger vers la page des commentaires de l'article
    return redirect(url_for('admin_article.show_article_commentaires', id_article=id_article))


@admin_commentaire.route('/admin/comment/valider_tous', methods=['POST'])
def admin_comment_valider_tous():
    mycursor = get_db().cursor()
    id_article = request.form.get('id_article', '')

    # Mettre à jour tous les commentaires pour les marquer comme lus
    sql = '''
    UPDATE commentaire
    SET valider = 1
    WHERE cle_usb_id = %s AND utilisateur_id != 1
    '''
    mycursor.execute(sql, (id_article,))
    get_db().commit()

    # Ajouter un message de confirmation
    flash("Tous les commentaires ont été marqués comme lus avec succès.", "success")

    # Rediriger vers la page des commentaires de l'article
    return redirect(url_for('admin_article.show_article_commentaires', id_article=id_article))


@admin_commentaire.route('/admin/comment/add/<int:id_utilisateur>/<int:id_article>/<path:date_publication>',
                         methods=['GET'])
def admin_comment_add(id_utilisateur, id_article, date_publication):
    mycursor = get_db().cursor()

    # Récupérer le commentaire auquel on répond
    sql = '''
    SELECT c.utilisateur_id, u.login, c.date_publication, c.commentaire, c.note, c.valider
    FROM commentaire c
    JOIN utilisateur u ON c.utilisateur_id = u.id_utilisateur
    WHERE c.utilisateur_id = %s AND c.cle_usb_id = %s AND c.date_publication = %s
    '''
    mycursor.execute(sql, (id_utilisateur, id_article, date_publication))
    commentaire = mycursor.fetchone()

    # Récupérer l'article
    sql = '''
    SELECT id_cle_usb as id_article, nom_cle_usb as nom
    FROM cle_usb
    WHERE id_cle_usb = %s
    '''
    mycursor.execute(sql, (id_article,))
    article = mycursor.fetchone()

    return render_template('admin/article/add_commentaire.html',
                           commentaire=commentaire,
                           article=article,
                           id_utilisateur=id_utilisateur,
                           id_article=id_article,
                           date_publication=date_publication)


@admin_commentaire.route('/admin/comment/add', methods=['POST'])
def valid_comment_add():
    mycursor = get_db().cursor()

    id_utilisateur = request.form.get('id_utilisateur', '')
    id_article = request.form.get('id_article', '')
    date_publication = request.form.get('date_publication', '')
    commentaire = request.form.get('commentaire', '')

    # Insérer la réponse de l'administrateur
    sql = '''
    INSERT INTO commentaire (utilisateur_id, cle_usb_id, date_publication, commentaire, valider)
    VALUES (1, %s, NOW(), %s, 1)
    '''
    mycursor.execute(sql, (id_article, commentaire))
    get_db().commit()

    # Marquer le commentaire original comme lu
    sql = '''
    UPDATE commentaire
    SET valider = 1
    WHERE utilisateur_id = %s AND cle_usb_id = %s AND date_publication = %s
    '''
    mycursor.execute(sql, (id_utilisateur, id_article, date_publication))
    get_db().commit()

    # Ajouter un message de confirmation
    flash("Votre réponse a été ajoutée avec succès.", "success")

    # Rediriger vers la page des commentaires de l'article
    return redirect(url_for('admin_article.show_article_commentaires', id_article=id_article))
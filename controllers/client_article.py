from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from connexion_db import get_db

client_article = Blueprint('client_article', __name__, template_folder='templates')


@client_article.route('/client/index')
@client_article.route('/client/article/show')
def client_article_show():
    mycursor = get_db().cursor()
    id_client = session.get('id_user')

    if not id_client:
        flash(u'Veuillez vous connecter pour accéder à cette page', 'warning')
        return redirect(url_for('auth.login'))

    try:
        # Modifié pour inclure le nombre de commentaires et la note moyenne
        sql = '''
        SELECT c.id_cle_usb, c.nom_cle_usb, c.prix_cle_usb, c.photo_url, c.stock, c.description, 
               t.libelle_type_cle_usb, t.id_type_cle_usb,
               COUNT(DISTINCT CASE WHEN com.commentaire IS NOT NULL THEN com.date_publication END) AS nb_avis,
               COUNT(DISTINCT CASE WHEN com.note IS NOT NULL THEN com.date_publication END) AS nb_notes,
               AVG(com.note) AS moy_notes
        FROM cle_usb c
        LEFT JOIN type_cle_usb t ON c.type_cle_usb_id = t.id_type_cle_usb
        LEFT JOIN commentaire com ON c.id_cle_usb = com.cle_usb_id
        '''
        params = []

        filter_conditions = []
        if session.get('filter_word'):
            filter_conditions.append("c.nom_cle_usb LIKE %s")
            params.append(f"%{session['filter_word']}%")
        if session.get('filter_types'):
            filter_conditions.append(
                "t.id_type_cle_usb IN ({})".format(','.join(['%s'] * len(session['filter_types']))))
            params.extend(session['filter_types'])
        if session.get('filter_prix_min'):
            filter_conditions.append("c.prix_cle_usb >= %s")
            params.append(session['filter_prix_min'])
        if session.get('filter_prix_max'):
            filter_conditions.append("c.prix_cle_usb <= %s")
            params.append(session['filter_prix_max'])

        if filter_conditions:
            sql += " WHERE " + " AND ".join(filter_conditions)

        # Ajout du GROUP BY pour l'agrégation
        sql += " GROUP BY c.id_cle_usb, t.id_type_cle_usb"

        current_app.logger.info(f"SQL Query: {sql}")
        current_app.logger.info(f"SQL Parameters: {params}")

        mycursor.execute(sql, tuple(params))
        articles = mycursor.fetchall()

        current_app.logger.info(f"Nombre d'articles récupérés : {len(articles)}")

        if not articles:
            current_app.logger.warning("Aucun article trouvé dans la base de données.")
            flash(u'Aucun article disponible pour le moment.', 'info')

        sql = '''
        SELECT id_type_cle_usb, libelle_type_cle_usb
        FROM type_cle_usb
        '''
        mycursor.execute(sql)
        types_article = mycursor.fetchall()

        sql = '''
        SELECT c.id_cle_usb, c.nom_cle_usb, c.prix_cle_usb, lp.quantite
        FROM ligne_panier lp
        JOIN cle_usb c ON lp.cle_usb_id = c.id_cle_usb
        WHERE lp.utilisateur_id = %s
        '''
        mycursor.execute(sql, (id_client,))
        articles_panier = mycursor.fetchall()

        prix_total = sum(article['prix_cle_usb'] * article['quantite'] for article in articles_panier)

        return render_template('client/boutique/panier_article.html',
                               articles=articles,
                               articles_panier=articles_panier,
                               prix_total=prix_total,
                               items_filtre=types_article)
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des articles : {str(e)}")
        flash(u'Une erreur est survenue lors du chargement des articles.', 'error')
        return redirect(url_for('show_accueil'))  # Modifié de 'home' à 'show_accueil'


@client_article.route('/client/article/details/<int:id>', methods=['GET'])
def client_article_details(id):
    mycursor = get_db().cursor()
    id_client = session.get('id_user', 0)

    # Récupération des informations de l'article
    sql = '''
    SELECT c.*, t.libelle_type_cle_usb
    FROM cle_usb c
    LEFT JOIN type_cle_usb t ON c.type_cle_usb_id = t.id_type_cle_usb
    WHERE c.id_cle_usb = %s
    '''
    mycursor.execute(sql, (id,))
    article = mycursor.fetchone()

    # Récupération des statistiques sur les commentaires
    sql = '''
    SELECT 
        COUNT(CASE WHEN utilisateur_id = %s AND commentaire IS NOT NULL THEN 1 END) AS nb_commentaires_user,
        COUNT(CASE WHEN commentaire IS NOT NULL THEN 1 END) AS nb_commentaires_total,
        COUNT(CASE WHEN valider = 1 AND commentaire IS NOT NULL THEN 1 END) AS nb_commentaires_valides,
        COUNT(CASE WHEN utilisateur_id = %s AND valider = 1 AND commentaire IS NOT NULL THEN 1 END) AS nb_commentaires_user_valides,
        ROUND(AVG(note), 1) AS note_moyenne,
        COUNT(DISTINCT CASE WHEN note IS NOT NULL THEN utilisateur_id END) AS nb_notes
    FROM commentaire
    WHERE cle_usb_id = %s
    '''
    mycursor.execute(sql, (id_client, id_client, id,))
    stats = mycursor.fetchone()

    # Vérification si l'utilisateur a déjà acheté cet article
    sql = '''
    SELECT COUNT(*) AS a_achete
    FROM ligne_commande lc
    JOIN commande c ON lc.commande_id = c.id_commande
    WHERE c.utilisateur_id = %s AND lc.cle_usb_id = %s
    '''
    mycursor.execute(sql, (id_client, id,))
    achat = mycursor.fetchone()

    # Récupération des commentaires ordonnés chronologiquement (du plus récent au plus ancien)
    sql = '''
    SELECT c.*, u.login, u.nom
    FROM commentaire c
    JOIN utilisateur u ON c.utilisateur_id = u.id_utilisateur
    WHERE c.cle_usb_id = %s AND c.commentaire IS NOT NULL
    ORDER BY c.date_publication DESC
    '''
    mycursor.execute(sql, (id,))
    commentaires = mycursor.fetchall()

    # Récupération de la note de l'utilisateur pour cet article
    sql = '''
    SELECT note
    FROM commentaire
    WHERE utilisateur_id = %s AND cle_usb_id = %s AND note IS NOT NULL
    '''
    mycursor.execute(sql, (id_client, id,))
    note_result = mycursor.fetchone()
    note = note_result['note'] if note_result else None

    # Vérification du quota de commentaires de l'utilisateur
    sql = '''
    SELECT COUNT(*) AS nb_commentaires
    FROM commentaire
    WHERE utilisateur_id = %s AND cle_usb_id = %s AND commentaire IS NOT NULL
    '''
    mycursor.execute(sql, (id_client, id,))
    quota = mycursor.fetchone()

    return render_template('client/article_info/article_details.html',
                           article=article,
                           commentaires=commentaires,
                           stats=stats,
                           achat=achat,
                           quota=quota,
                           note=note)


@client_article.route('/client/panier/add', methods=['POST'])
def client_panier_add():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_article = request.form.get('id_article', None)
    quantite = request.form.get('quantite', None)
    if id_article and quantite:
        sql = "SELECT stock FROM cle_usb WHERE id_cle_usb = %s"
        mycursor.execute(sql, (id_article,))
        stock = mycursor.fetchone()['stock']
        if stock >= int(quantite):
            sql = "SELECT quantite FROM ligne_panier WHERE utilisateur_id = %s AND cle_usb_id = %s"
            mycursor.execute(sql, (id_client, id_article))
            result = mycursor.fetchone()
            if result:
                new_quantite = result['quantite'] + int(quantite)
                sql = "UPDATE ligne_panier SET quantite = %s WHERE utilisateur_id = %s AND cle_usb_id = %s"
                mycursor.execute(sql, (new_quantite, id_client, id_article))
            else:
                sql = "INSERT INTO ligne_panier (utilisateur_id, cle_usb_id, quantite) VALUES (%s, %s, %s)"
                mycursor.execute(sql, (id_client, id_article, quantite))
            get_db().commit()
            flash(u'Article ajouté au panier avec succès !', 'success')
        else:
            flash(u'Stock insuffisant !', 'danger')
    return redirect(url_for('client_article.client_article_show'))


@client_article.route('/client/panier/remove', methods=['POST'])
def client_panier_remove():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_article = request.form.get('id_article', None)
    if id_article:
        sql = "SELECT quantite FROM ligne_panier WHERE utilisateur_id = %s AND cle_usb_id = %s"
        mycursor.execute(sql, (id_client, id_article))
        result = mycursor.fetchone()
        if result and result['quantite'] > 1:
            new_quantite = result['quantite'] - 1
            sql = "UPDATE ligne_panier SET quantite = %s WHERE utilisateur_id = %s AND cle_usb_id = %s"
            mycursor.execute(sql, (new_quantite, id_client, id_article))
        else:
            sql = "DELETE FROM ligne_panier WHERE utilisateur_id = %s AND cle_usb_id = %s"
            mycursor.execute(sql, (id_client, id_article))
        get_db().commit()
        flash(u'Quantité mise à jour dans le panier', 'success')
    return redirect(url_for('client_article.client_article_show'))


@client_article.route('/client/panier/delete/line', methods=['POST'])
def client_panier_delete():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_article = request.form.get('id_article', None)
    if id_article:
        sql = "DELETE FROM ligne_panier WHERE utilisateur_id = %s AND cle_usb_id = %s"
        mycursor.execute(sql, (id_client, id_article))
        get_db().commit()
        flash(u'Article supprimé du panier avec succès !', 'success')
    return redirect(url_for('client_article.client_article_show'))


@client_article.route('/client/panier/vider', methods=['POST'])
def client_panier_vider():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    sql = "DELETE FROM ligne_panier WHERE utilisateur_id = %s"
    mycursor.execute(sql, (id_client,))
    get_db().commit()
    flash(u'Panier vidé avec succès !', 'success')
    return redirect(url_for('client_article.client_article_show'))


@client_article.route('/client/panier/filtre', methods=['POST'])
def client_panier_filtre():
    session['filter_word'] = request.form.get('filter_word', '')
    session['filter_types'] = request.form.getlist('filter_types')
    session['filter_prix_min'] = request.form.get('filter_prix_min', '')
    session['filter_prix_max'] = request.form.get('filter_prix_max', '')
    return redirect(url_for('client_article.client_article_show'))


@client_article.route('/client/panier/filtre/suppr', methods=['POST'])
def client_panier_filtre_suppr():
    session.pop('filter_word', None)
    session.pop('filter_types', None)
    session.pop('filter_prix_min', None)
    session.pop('filter_prix_max', None)
    flash(u'Tous les filtres ont été supprimés.', 'info')
    return redirect(url_for('client_article.client_article_show'))


@client_article.route('/client/article/refresh', methods=['GET'])
def client_article_refresh():
    return client_article_show()


@client_article.route('/debug')
def debug_info():
    mycursor = get_db().cursor()
    try:
        mycursor.execute("SELECT * FROM cle_usb")
        cle_usb_data = mycursor.fetchall()
        mycursor.execute("SELECT * FROM type_cle_usb")
        type_cle_usb_data = mycursor.fetchall()
        return f"Données cle_usb : {str(cle_usb_data)}<br><br>Données type_cle_usb : {str(type_cle_usb_data)}"
    except Exception as e:
        return f"Erreur lors de la récupération des données : {str(e)}"
#! /usr/bin/python
# -*- coding:utf-8 -*-
import os
from flask import Flask, request, render_template, redirect, url_for, abort, flash, session, g
from flask import Blueprint
# SAE Livrable 2
from controllers.auth_security import *
from controllers.client_article import *
from controllers.client_coordonnee import client_coordonnee
from controllers.client_liste_envies import client_liste_envies
from controllers.client_panier import *
from controllers.client_commande import *
from controllers.client_commentaire import *
from controllers.admin_article import *
from controllers.admin_commande import *
from controllers.admin_commentaire import *
from controllers.admin_dataviz import *
from controllers.admin_declinaison_article import *
from controllers.admin_type_article import *

from controllers.fixtures_load import fixtures_load

app = Flask(__name__)
app.secret_key = 'une cle(token) : grain de sel(any random string)'

# Configuration directe de la base de données (sans .env)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'amaarou3'
app.config['MYSQL_PASSWORD'] = 'mdp'
app.config['MYSQL_DB'] = 'BDD_amaarou3'

# Enregistrement des teardown pour fermer les connexions à la base de données
@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Enregistrement des blueprints
app.register_blueprint(auth_security)
app.register_blueprint(client_article)
app.register_blueprint(client_commande)
app.register_blueprint(client_commentaire)
app.register_blueprint(client_panier)
app.register_blueprint(admin_article)
app.register_blueprint(admin_commande)
app.register_blueprint(admin_commentaire)
app.register_blueprint(admin_dataviz)
app.register_blueprint(admin_declinaison_article)
app.register_blueprint(admin_type_article)
app.register_blueprint(fixtures_load)
app.register_blueprint(client_coordonnee)
app.register_blueprint(client_liste_envies)

@app.route('/')
def show_accueil():
    return render_template('auth/layout.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)


    
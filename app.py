#! /usr/bin/python
# -*- coding:utf-8 -*-
import os
from flask import Flask, request, render_template, redirect, url_for, abort, flash, session, g
from flask import Blueprint

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

from dotenv import load_dotenv

from controllers.fixtures_load import fixtures_load

app = Flask(__name__)
app.secret_key = 'une cle(token) : grain de sel(any random string)'

load_dotenv(".env")
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

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
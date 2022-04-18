#!/usr/bin/python
# -*- encoding:utf-8 -*-
import secrets
import pymongo

from oauth import OAuth
from flask import Flask, redirect, render_template, request, session
from flask_socketio import SocketIO, emit
from ratelimit import limits
from movies import MovieDB

app = Flask(__name__, template_folder='static')
app.secret_key = secrets.token_hex(32)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1
app.socketio = SocketIO(app)
app.address = "app_address"

app.matching = False

app.oauth = OAuth()
app.moviedb = MovieDB()

client = pymongo.MongoClient("mongodb_secret")
app.db = client['cvdb']
app.collection = app.db["users"]

_CALLS = 100
_PERIOD = 60

# MongoDB Functions


def create_user(email):
    dict = {
        "email": email,
        "friends": [],
        "seen": [],
        "watchlist": [],
        "not_interested": []
    }
    app.collection.insert_one(dict)


def user_exists(email):
    return app.collection.find_one({"email": email})

# SocketIO Functions


@app.socketio.on('add_friend')
def add_friend(data=None):
    if 'email' in session:
        if data:
            print("Adding friend", data)
            session['friends'].append(data['email'])
            app.collection.update_one({"email": session['email']}, {
                '$push': {'friends': data['email']}})
            emit('friend_added', {'email': data['email']})


@app.socketio.on('get_matches')
def get_matches(data=None):
    if 'email' in session:
        if data:
            app.matching = False
            print("Getting matches", data)
            info = app.collection.find_one({"email": session['email']})
            session['watchlist'] = info['watchlist']
            home = session['watchlist']
            away_list = app.collection.find_one({"email": data['email']})

            if not away_list:
                emit('match_info', {'count': '0', 'email': data['email']})
                return

            away = away_list['watchlist']
            matches = list(set(home).intersection(set(away)))
            app.matching = True

            emit('match_info', {'count': str(
                len(matches)), 'email': data['email']})

            for match in matches:
                if not app.matching:
                    break
                title, link = app.moviedb.get_movie_basic(match)
                emit('match', {'title': title, 'link': link})


# Flask Routes


@app.route("/")
@limits(calls=_CALLS, period=_PERIOD)
def index():
    if 'email' not in session:
        return redirect(app.address+'/login')
    marked = (session['watchlist'], session['seen'], session['not_interested'])
    id, title, cast, plot, rating, link, cover = app.moviedb.get_random_movie(
        marked)
    return render_template("index.html", id=id, title=title, cast=cast, plot=plot, rating=rating, link=link, cover=cover)


@app.route("/login")
@limits(calls=_CALLS, period=_PERIOD)
def login():
    return render_template("login.html")


@app.route("/profile")
@limits(calls=_CALLS, period=_PERIOD)
def profile():
    if 'email' not in session:
        return redirect(app.address+'/login')
    info = app.collection.find_one({"email": session['email']})
    session['seen'] = info['seen']
    session['watchlist'] = info['watchlist']
    session['not_interested'] = info['not_interested']
    return render_template("profile.html", email=session['email'], seen_count=len(session['seen']), watchlist_count=len(session['watchlist']), not_interested_count=len(session['not_interested']))


@app.route("/oauth_login")
@limits(calls=_CALLS, period=_PERIOD)
def oauth_redirect_url():
    return redirect(app.oauth.generate_url()[0])


@app.route("/oauth")
@limits(calls=_CALLS, period=_PERIOD)
def authorize():
    response = request.args
    if 'code' in response:
        user = app.oauth.fetch(response['code'])
        if 'email' in user:
            session['email'] = user['email']
            if not user_exists(session['email']):
                create_user(session['email'])

            info = app.collection.find_one({"email": session['email']})
            session['friends'] = info['friends']
            session['seen'] = info['seen']
            session['watchlist'] = info['watchlist']
            session['not_interested'] = info['not_interested']
            return redirect(app.address+"/")

    return {"status": response['error']}


@app.route("/add_to_watchlist")
@limits(calls=_CALLS, period=_PERIOD)
def add_to_watchlist():
    if 'email' not in session:
        return redirect(app.address+'/login')
    res = request.args
    if 'id' in res:
        session['watchlist'].append(res['id'])
        app.collection.update_one({"email": session['email']}, {
                                  '$push': {'watchlist': res['id']}})
    return redirect(app.address+"/")


@app.route("/seen")
@limits(calls=_CALLS, period=_PERIOD)
def add_to_seen():
    if 'email' not in session:
        return redirect(app.address+'/login')
    res = request.args
    if 'id' in res:
        session['seen'].append(res['id'])
        app.collection.update_one({"email": session['email']}, {
                                  '$push': {'seen': res['id']}})
    return redirect(app.address+"/")


@app.route("/not_interested")
@limits(calls=_CALLS, period=_PERIOD)
def add_to_not_interested():
    if 'email' not in session:
        return redirect(app.address+'/login')
    res = request.args
    if 'id' in res:
        session['not_interested'].append(res['id'])
        app.collection.update_one({"email": session['email']}, {
                                  '$push': {'not_interested': res['id']}})
    return redirect(app.address+"/")


@app.route("/delete_account")
@limits(calls=_CALLS, period=_PERIOD)
def delete_account():
    if 'email' not in session:
        return redirect(app.address+'/login')
    app.collection.delete_one({"email": session['email']})
    session.clear()
    return redirect(app.address+"/login")


@app.route("/stack")
@limits(calls=_CALLS, period=_PERIOD)
def stack():
    if 'email' not in session:
        return redirect(app.address+'/login')
    info = app.collection.find_one({"email": session['email']})
    session['friends'] = info['friends']
    return render_template("stack.html", data=session['friends'])

# Files


@app.route("/assets/img/favicon.svg")
@limits(calls=_CALLS, period=_PERIOD)
def favicon():
    return app.send_static_file("assets/img/favicon.svg")


@app.route("/assets/css/styles.css")
@limits(calls=_CALLS, period=_PERIOD)
def styles():
    return app.send_static_file("assets/css/styles.css")


@app.route("/assets/js/profile.js")
@limits(calls=_CALLS, period=_PERIOD)
def profile_script():
    return app.send_static_file("assets/js/profile.js")


@app.route("/assets/js/stack.js")
@limits(calls=_CALLS, period=_PERIOD)
def stack_script():
    return app.send_static_file("assets/js/stack.js")


@app.route("/assets/css/HemiHeadRg.css")
@limits(calls=_CALLS, period=_PERIOD)
def font_hemiheadrg():
    return app.send_static_file("assets/css/HemiHeadRg.css")


@app.route("/assets/css/Navigation-Clean.css")
@limits(calls=_CALLS, period=_PERIOD)
def font_navigation_clean():
    return app.send_static_file("assets/css/Navigation-Clean.css")


@app.route("/assets/fonts/HemiHeadRg-BoldItalic.woff")
@limits(calls=_CALLS, period=_PERIOD)
def font_woff():
    return app.send_static_file("assets/fonts/HemiHeadRg-BoldItalic.woff")


@app.route("/assets/fonts/HemiHeadRg-BoldItalic.woff2")
@limits(calls=_CALLS, period=_PERIOD)
def font_woff2():
    return app.send_static_file("assets/fonts/HemiHeadRg-BoldItalic.woff2")

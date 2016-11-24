from flask import Flask, redirect, url_for, session, request, jsonify, render_template
from flask_oauthlib.client import OAuth
from flask import Blueprint
import requests
import json
from config import CONSUMER_KEY, CONSUMER_SECRET

api = Blueprint('APIs', __name__)

oauth = OAuth()

google = oauth.remote_app(
    'google',
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    request_token_params={
        'scope': 'email'
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)

@api.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        if 'current_user' in session:
            me = google.get('userinfo')
            return render_template("index.html")
        return render_template("login.html")
    elif request.method == 'POST':
        lab_id = request.form.get("lab_id")
        lab_url = request.form.get("lab_src_url")
        tag = request.form.get("version")
        ads_url = "http://10.4.15.91:8080"
        data = {'lab_id': lab_id, 'lab_src_url': lab_url, 'version': tag}
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        r = requests.post(ads_url, data=json.dumps(data), headers=headers)
        if r.status_code !=200:
            return "Error Occured"
        else:
            data['url'] = r.text
            return render_template("success.html", data=data)

@api.route('/login')
def login():
    return google.authorize(callback=url_for('APIs.authorized', _external=True))


@api.route('/logout')
def logout():
    session.pop('current_user', None)
    return redirect("/")


@api.route('/login/authorized')
def authorized():
    resp = google.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['google_token'] = (resp['access_token'], '')
    me = google.get('userinfo')
    session['current_user'] = me.data['email']
    #return jsonify({"data": me.data})
    return redirect("/")

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

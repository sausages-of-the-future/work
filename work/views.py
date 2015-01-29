import os
import hashlib
import json
import requests
import jinja2
from flask_oauthlib.client import OAuth
from twilio.rest import TwilioRestClient
import work.forms as forms
from work import app, oauth
from decorators import registry_oauth_required
import dateutil.parser
from flask import (
    Flask,
    request,
    redirect,
    render_template,
    url_for,
    session,
    flash,
    abort,
    current_app
)

service = {
  "name": "Find work",
  "minister": "Minister for employment",
  "registers": ["Licences", "Organisations"],
  "slug": "start-organisation",
  "service_base_url_config": "WORK_BASE_URL",
  "policies": [],
  "legislation": [],
  "guides": [
    {"title": "Guide for Directors", "slug": "directors"},
    {"title": "Guide for Trustees", "slug": "trustees"},
    {"title": "Types of organisation", "slug": "types"}
  ]
}

licene_types = {'use_cctv': 'test'}

registry = oauth.remote_app(
    'registry',
    consumer_key=app.config['REGISTRY_CONSUMER_KEY'],
    consumer_secret=app.config['REGISTRY_CONSUMER_SECRET'],
    request_token_params={'scope': 'address:view income:view person:view'},
    base_url=app.config['REGISTRY_BASE_URL'],
    request_token_url=None,
    access_token_method='POST',
    access_token_url='%s/oauth/token' % app.config['REGISTRY_BASE_URL'],
    authorize_url='%s/oauth/authorize' % app.config['REGISTRY_BASE_URL']
)

def make_random_token():
    random =  hashlib.sha1(os.urandom(128)).hexdigest()
    random = random.upper()
    return "%s-%s-%s-%s" % (random[0:4], random[5:9], random[10:14], random[15:19])

#auth helper
@registry.tokengetter
def get_registry_oauth_token():
    return session.get('registry_token')

#views
@app.route("/")
def index():
    return redirect("%s/work" % app.config['WWW_BASE_URL'])

@app.route("/job-seeker")
@registry_oauth_required
def job_seeker_account():

    return render_template("job-seeker.html", service=service, selected_tab='overview')

@app.route('/verify')
def verify():
    _scheme = 'https'
    if os.environ.get('OAUTHLIB_INSECURE_TRANSPORT', False) == 'true':
        _scheme = 'http'
    return registry.authorize(callback=url_for('verified', _scheme=_scheme, _external=True))

@app.route('/verified')
def verified():
    resp = registry.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
        request.args['error_reason'],
        request.args['error_description']
        )

    session['registry_token'] = (resp['access_token'], '')
    if session.get('resume_url'):
        resume_url = session.get('resume_url')
        session.pop('resume_url', None)
        return redirect(resume_url)
    else:
        return redirect(url_for('index'))



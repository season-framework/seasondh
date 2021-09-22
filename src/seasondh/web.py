# -*- coding: utf-8 -*-

import os
import json
import flask
import logging
import traceback
import datetime
import urllib

from .util import randomstring, Storage, stdClass
from .workflow import workflow as seasondh_workflow

WORKSPACE_PATH = os.getcwd()
WEB_ROOT = os.path.dirname(os.path.realpath(__file__))
WEB_RESOURCE = os.path.join(WEB_ROOT, 'resources')
fs_workspace = Storage(WORKSPACE_PATH)

# build flask
app = flask.Flask(__name__, static_url_path='')
app.config['TEMPLATES_AUTO_RELOAD'] = True
log = logging.getLogger('werkzeug')
log.disabled = True

app.jinja_env.variable_start_string = "{$"
app.jinja_env.variable_end_string = "$}"       
app.jinja_env.add_extension('pypugjs.ext.jinja.PyPugJSExtension')

try:
    config = fs_workspace.read_json('seasondh.config.json')
except:
    config = dict()

if 'session_secret' in config:
    app.secret_key = config['session_secret']
else:
    app.secret_key = 'seasondh'

def json_default(value): 
    if isinstance(value, datetime.date): 
        return value.strftime('%Y-%m-%d %H:%M:%S') 
    raise str(value)

def message_builder(code, data):
    return flask.Response(
        response=json.dumps({ 'code': code, 'data': data }, default=json_default),
        status=200,
        mimetype='application/json'
    )

def build_dataset_args(app_id):
    kwargs = dict()
    return kwargs

def acl():
    if 'password' not in config:
        return

    if 'active' not in flask.session or flask.session['active'] != True:
        flask.abort(401)

@app.before_request
def make_session_permanent():
    flask.session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(minutes=14400)

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

# resource handler
@app.route('/resources/<path:path>')
def resources(path):
    resource_path = os.path.join(WEB_RESOURCE, path)
    return flask.send_file(resource_path)

# views
@app.route('/')
def index():
    if 'password' not in config:
        return flask.render_template("index.pug")
            
    if 'active' not in flask.session or flask.session['active'] != True:
        return flask.render_template("login.pug")

    return flask.render_template("index.pug")

@app.route('/workflow/<workflow_id>')
def workflow_(workflow_id):
    acl()
    return flask.render_template("workflow.pug", workflow_id=workflow_id)

@app.route('/app/<workflow_id>/<app_id>')
def app_(workflow_id, app_id):
    acl()
    return flask.render_template("app.pug", workflow_id=workflow_id, app_id=app_id)

# /api/auth
@app.route('/api/auth/login', methods=['POST'])
def api_auth_login():
    password = dict(flask.request.values)['password']
    if password == config['password']:
        flask.session['active'] = True
        return message_builder(200, True)
    return message_builder(401, 'fail')

@app.route('/api/auth/logout', methods=['GET'])
def api_auth_logout():
    flask.session.clear()
    return flask.redirect('/')

# /api actions
@app.route('/api/create')
def api_create():
    acl()
    files = fs_workspace.files()
    newid = randomstring(32)
    while newid in files:
        newid = randomstring(32)
    return flask.redirect(f'/workflow/{newid}')

@app.route('/api/delete/<workflow_id>')
def api_delete(workflow_id):
    acl()
    if workflow_id is None or len(workflow_id) == 0:
        return flask.redirect('/')

    fs_workspace.delete(workflow_id)
    return flask.redirect('/')

@app.route('/api/iframe/<workflow_id>/<app_id>')
def api_iframe(workflow_id, app_id):
    acl()
    workflow_path = os.path.join(WORKSPACE_PATH, workflow_id)
    workflow = seasondh_workflow(basepath=workflow_path)
    app = workflow.app(app_id)
    config = {}
    config['API_URL'] = '/api/view/function'
    view = app.view(config)
    return flask.render_template("iframe.pug", workflow_id=workflow_id, app_id=app_id, view=view)

@app.route('/api/exports/<workflow_id>')
def api_exports(workflow_id):
    acl()
    workflow_path = os.path.join(WORKSPACE_PATH, workflow_id)
    workflow = seasondh_workflow(basepath=workflow_path)
    info = workflow.get()
    
    updated = datetime.datetime.now()
    try:
        if 'updated' in info: 
            updated = datetime.datetime.strptime(info['updated'], '%Y-%m-%d %H:%M:%S')
    except:
        pass
    updated = updated.strftime('%Y%m%d_%H%M%S')

    title = info['title']
    title = urllib.parse.quote(title) + '_' + updated
    return flask.Response(json.dumps(info, indent=4, sort_keys=True), 
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment;filename={title}.json'})

@app.route('/api/export/<workflow_id>/<app_id>')
def api_export(workflow_id, app_id):
    acl()
    workflow_path = os.path.join(WORKSPACE_PATH, workflow_id)
    workflow = seasondh_workflow(basepath=workflow_path)
    app = workflow.app(app_id)
    appinfo = app.to_dict()
    title = app_id
    if 'title' in appinfo: title = appinfo['title']
    title = urllib.parse.quote(title)
    return flask.Response(app.json(), 
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment;filename={title}.json'})

@app.route('/api/update/<workflow_id>', methods = ['POST'])
def api_update(workflow_id):
    acl()
    info = json.loads(dict(flask.request.values)['data'])
    info['id'] = workflow_id
    info['updated'] = datetime.datetime.now()
    
    workflow_path = os.path.join(WORKSPACE_PATH, workflow_id)
    workflow = seasondh_workflow(basepath=workflow_path)

    workflow.update(info)
    return message_builder(200, True)

# /api/workflow
@app.route('/api/workflow/info/<workflow_id>', methods = ['POST'])
def api_workflow_info(workflow_id):
    acl()
    workflow_path = os.path.join(WORKSPACE_PATH, workflow_id)
    workflow = seasondh_workflow(basepath=workflow_path)
    info = workflow.get()
    info['id'] = workflow_id
    return message_builder(200, info)

@app.route('/api/workflow/list', methods=['GET', 'POST'])
def api_workflow_list():
    acl()
    files = fs_workspace.files()
    result = []
    for item in files:
        try:
            d = fs_workspace.read_json(f"{item}/seasondh.json")
            if d is not None:
                tmp = dict()
                tmp['id'] = item
                if 'title' in d:
                    tmp['title'] = d['title']
                    if 'description' in d: tmp['description'] = d['description']
                    if 'updated' in d: tmp['updated'] = d['updated']
                result.append(tmp)
        except:
            pass
    return message_builder(200, result)

# api view
@app.route('/api/view/function/<workflow_id>/<app_id>/<fnname>', methods=['GET', 'POST'])
def api_dataset_functions(workflow_id, app_id, fnname):
    acl()
    
    workflow_path = os.path.join(WORKSPACE_PATH, workflow_id)
    workflow = seasondh_workflow(basepath=workflow_path)
    app = workflow.app(app_id)

    framework = stdClass()
    framework['request'] = flask.request
    framework['query'] = dict(flask.request.values)
    framework['files'] = flask.request.files.getlist('file[]')
    framework['response'] = message_builder

    result = app.view_api(fnname, framework)
    return result
# -*- coding: utf-8 -*-

import os
import json
import flask
import logging
import traceback

from .base import randomstring
from .dataset import dataset as seasondh_dataset
from .storage import FileSystem

WORKSPACE_PATH = os.getcwd()

WEB_ROOT = os.path.dirname(os.path.realpath(__file__))
WEB_RESOURCE = os.path.join(WEB_ROOT, 'resources')

fs_workspace = FileSystem(WORKSPACE_PATH)

# build flask
app = flask.Flask(__name__, static_url_path='')
app.config['TEMPLATES_AUTO_RELOAD'] = True
log = logging.getLogger('werkzeug')
log.disabled = True
app.jinja_env.add_extension('pypugjs.ext.jinja.PyPugJSExtension')

try:
    config = fs_workspace.read_json('seasondh.config.json')
except:
    config = dict()

if 'session_secret' in config:
    app.secret_key = config['session_secret']
else:
    app.secret_key = 'seasondh'

def message_builder(code, data, log=None):
    return { 'code': code, 'data': data, 'log': log }

def build_dataset_args(app_id):
    kwargs = dict()
    return kwargs

def ng(name):
    return '{{' + str(name) + '}}'

def acl():
    if 'password' not in config:
        return

    if 'active' not in flask.session or flask.session['active'] != True:
        flask.abort(401)

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
        return flask.render_template("index.pug", ng=ng)
            
    if 'active' not in flask.session or flask.session['active'] != True:
        return flask.render_template("login.pug", ng=ng)

    return flask.render_template("index.pug", ng=ng)


@app.route('/dataset/<dataset_id>')
def dataset_(dataset_id):
    acl()
    return flask.render_template("dataset.pug", ng=ng, dataset_id=dataset_id)


@app.route('/app/<dataset_id>/<app_id>')
def app_(dataset_id, app_id):
    acl()
    return flask.render_template("app.pug", ng=ng, dataset_id=dataset_id, app_id=app_id)

# api
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

@app.route('/api/create')
def api_create():
    acl()
    files = fs_workspace.files()
    newid = randomstring(32)
    while newid in files:
        newid = randomstring(32)
    return flask.redirect(f'/dataset/{newid}')

@app.route('/api/delete/<dataset_id>')
def api_delete(dataset_id):
    acl()
    if dataset_id is None or len(dataset_id) == 0:
        return flask.redirect('/')

    fs_workspace.delete(dataset_id)
    return flask.redirect('/')

@app.route('/api/iframe/<dataset_id>/<app_id>')
def api_iframe(dataset_id, app_id):
    acl()
    info = fs_workspace.read_json(f"{dataset_id}/seasondh.json")
    app = None
    if 'dataloader' in info:
        if info['dataloader']['id'] == app_id:
            app = info['dataloader']
    if app is None and 'apps' in info:
        for _app in info['apps']:
            if _app['id'] == app_id:
                app = _app

    return flask.render_template("iframe.pug", ng=ng, dataset_id=dataset_id, app_id=app_id, info=app)


@app.route('/api/export/<dataset_id>/<app_id>')
def api_export(dataset_id, app_id):
    acl()
    info = fs_workspace.read_json(f"{dataset_id}/seasondh.json")
    app = None
    if 'dataloader' in info:
        if info['dataloader']['id'] == app_id:
            app = info['dataloader']
    if app is None and 'apps' in info:
        for _app in info['apps']:
            if _app['id'] == app_id:
                app = _app

    app_mode = app['mode']
    return flask.Response(json.dumps(app), 
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment;filename={app_mode}.{app_id}.json'})


@app.route('/api/update/<dataset_id>', methods = ['POST'])
def api_update(dataset_id):
    acl()
    info = json.loads(dict(flask.request.values)['data'])
    info['id'] = dataset_id
    fs_workspace.write_json(f"{dataset_id}/seasondh.json", info)
    return message_builder(200, True)


@app.route('/api/dataset/info/<dataset_id>', methods = ['POST'])
def api_dataset_info(dataset_id):
    acl()
    try:
        info = fs_workspace.read_json(f"{dataset_id}/seasondh.json")
    except:
        info = dict()
    info['id'] = dataset_id
    return message_builder(200, info)


@app.route('/api/dataset/list', methods = ['POST'])
def api_dataset_list():
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
                result.append(tmp)
        except:
            pass
    return message_builder(200, result)


@app.route('/api/view/function/<dataset_id>/<app_id>/<fnname>', methods=['GET', 'POST'])
def api_dataset_functions(dataset_id, app_id, fnname):
    acl()

    logs = []
    try:
        info = fs_workspace.read_json(f"{dataset_id}/seasondh.json")
        app = None
        if 'dataloader' in info:
            if info['dataloader']['id'] == app_id:
                app = info['dataloader']
        if app is None and 'apps' in info:
            for _app in info['apps']:
                if _app['id'] == app_id:
                    app = _app

        if app is None:
            return message_builder(404, 'App Not Found')

        view = app['view']
        view_api = view['api']
        fn = {}
        exec(view_api, fn)
        if fnname not in fn: return message_builder(404, 'Not Found', f'Function {fnname} Not Exists')

        dataset = seasondh_dataset(os.path.join(WORKSPACE_PATH, dataset_id))
        kwargs = {}

        if 'mode' in app and app['mode'] == 'dataloader': kwargs['storage'] = dataset.get_storage(app_id='dataloader')
        else: kwargs['storage'] = dataset.get_storage(app_id=app_id)

        kwargs['app_id'] = app_id
        kwargs['dataset_id'] = dataset_id
        kwargs['storage_path'] = WORKSPACE_PATH
        kwargs['dataset'] = dataset
        kwargs['request'] = flask.request
        kwargs['query'] = dict(flask.request.values)
        kwargs['files'] = flask.request.files.getlist('file[]')

        def _print(*args):
            data = []
            for arg in args:
                data.append(str(arg))
            data = " ".join(data)
            logs.append(data)

        fn['print'] = _print
        dataset.set_print(_print)

        result = None
        try:
            result = fn[fnname](**kwargs)
        except Exception as e:
            logs.append("<pre style='color: red; margin: 0 !important; padding: 0 !important; display: block;'>" + traceback.format_exc() + "</pre>")
            return message_builder(500, None, "\n".join(logs))

        return message_builder(200, result, "\n".join(logs))
    except Exception as e:
        logs.append("<pre style='color: red; margin: 0 !important; padding: 0 !important; display: block;'>" + traceback.format_exc() + "</pre>")
        return message_builder(500, None, "\n".join(logs))
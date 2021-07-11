# -*- coding: utf-8 -*-
import os
import sys

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.realpath(os.path.join(ROOT_PATH, '..')))
__package__ = "seasondh"

from .base import randomstring
from .storage import FileSystem
from .version import VERSION_STRING

VERSION = __version__ = version = VERSION_STRING
WORKSPACE_PATH = os.getcwd()
fs_workspace = FileSystem(WORKSPACE_PATH)

import argh
from argh import arg, expects_obj

# commands
@arg('--host', default='0.0.0.0', help='host')
@arg('--port', default=3000, help='port')
@arg('--password', default=None, help='password')
@expects_obj
def web(args):
    print('')
    print(f"run web server via http://{args.host}:{args.port}")
    if args.password is not None:
        conf = dict()
        conf['password'] = args.password
        fs_workspace.write_json('seasondh.config.json', conf)
    print('')

    from .web import app
    app.run(host=args.host, port=args.port)

def main():
    epilog = "Copyright 2021 proin <proin@season.co.kr>. Licensed under the terms of the MIT license. Please see LICENSE in the source code for more information."
    parser = argh.ArghParser()
    parser.add_commands([
        web
    ])
    parser.add_argument('--version',
                    action='version',
                    version='%(prog)s ' + VERSION_STRING)
    parser.dispatch()

# start web server
if __name__ == '__main__':
    main()

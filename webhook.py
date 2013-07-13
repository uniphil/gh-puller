#!/usr/bin/env python2

import os, json

try:
    import yaml
    from sh import pwd, cd, ErrorReturnCode_128
    from flask import Flask, request, abort
except ImportError as e:
    e.message = "Could not import the required libraries. Have you `pip install -r requirements.txt`d them?"
    """last-ditch: is there a virtualenv to activate?"""
    activated = False
    import os, glob
    venv_shots = glob.glob(os.path.join('*', 'bin', 'activate_this.py'))
    for shot in venv_shots:
        try:
            import imp
            imp.load_source('activate_this', shot)
            activated = True
            break
        except IOError:
            pass
    if activated:
        try:
            import yaml
            from sh import pwd, cd, ErrorReturnCode_128
            from flask import Flask, request, abort
        except ImportError:
            raise e
    else:
        raise e

try:
    from sh import git
except ImportError as e:
    e.message = "You need to have git installed to use this tool"
    raise e


def load_config(config_file='config.yaml'):
    try:
        with open(config_file) as f:
            config = yaml.load(f)
    except IOError as e:
        e.message = "could not read config file `config.yaml`. ... ... ??"
        raise e

    try:
        host, port = config['listen']['host'], config['listen']['port']
        repositories = config['repositories']
        if not all('path' in r for r in repositories.values()):
            raise KeyError('at least one repository is missing a url')
    except KeyError as e:
        e.message = 'bad config format'
        raise e
    
    return (host, port), repositories


def pull(url, path):
    here = str(pwd()).strip()
    try:
        cd(path)
    except OSError:
        print "path does not exist? {}".format(path)
        cd(here)
        return
    try:
        git.status()
    except ErrorReturnCode_128:
        print "{} is not a git repository!".format(path)
        cd(here)
        return
    git.pull(url, 'master')
    git.checkout('-f')
    cd(here)


def hookify(app, repositories):
    @app.route('/', methods=['GET', 'POST'])
    def hook():
        try:
            payload = json.loads(request.form['payload'])
            url = payload['repository']['url']
        except KeyError:
            print "Bad Request!"
            abort(400)
        print 'heyheyhey'
        try:
            repo_config = repositories[url]
        except KeyError:
            print "Repository not in config"
            abort(404)
        pull(url, **repo_config)
        return 'cool cool'
    return app


def gunicornify(app, host, port):
    return glapp


def run_flask(app, host, port):
    app.run(host=host, port=port)


def run_gunicorn(app, host, port):
    try:
        from gunicorn.app.base import Application
        from gunicorn.config import Config
    except:
        print "warning: couldn't import gunicorn -- running flask dev server"
        run_flask(app, host, port)
        return
    class Glapp(Application):
        def init(self, *start):
            pass
        def load(self):
            return app
    glapp = Glapp()
    gonfig = Config()
    gonfig.set('bind', '{}:{}'.format(host, port))
    glapp.cfg = gonfig
    glapp.run()



if __name__ == '__main__':
    import sys
    (host, port), repositories = load_config()
    flapp = Flask(__name__)
    hookify(flapp, repositories)

    server = sys.argv[1] if len(sys.argv) > 1 else 'gunicorn'

    if server == 'gunicorn':
        run_gunicorn(flapp, host, port)
    elif server == 'debug':
        flapp.debug = True
        run_flask(flapp, host, port)
    else:
        run_flask(flapp, host, port)

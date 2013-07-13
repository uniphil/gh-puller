#!/usr/bin/env python2

try:
    import yaml
    from flask import Flask
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
            from flask import Flask
        except ImportError:
            raise e
    else:
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
        if not all('url' in r and 'path' in r for r in repositories):
            raise KeyError('at least one repository is missing a url and/or path')
    except KeyError as e:
        e.message = 'bad config format'
        raise e
    
    return (host, port), repositories


def hookify(app, base=''):
    @app.route(base + '/', methods=['GET', 'POST'])
    def hook():
        print 'heyheyhey'
        return 'woo hoo hoo hoo'    
    return app


def gunicornify(app, host, port):
    from gunicorn.app.base import Application
    from gunicorn.config import Config
    class Glapp(Application):
        def init(self, *start):
            pass
        def load(self):
            return app
    glapp = Glapp()
    gonfig = Config()
    gonfig.set('bind', '{}:{}'.format(host, port))
    glapp.cfg = gonfig
    return glapp

if __name__ == '__main__':
    (host, port), repositories = load_config()

    flapp = Flask(__name__)
    hookify(flapp)

    try:
        glapp = gunicornify(flapp, host, port)
        glapp.run()
    except ImportError:
        print "warning: couldn't import gunicorn -- running flask dev server"
        flapp.run(host=host, port=port)

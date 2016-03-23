from .core.models import update_schemas

from flask import Flask, Blueprint
from flask.helpers import get_root_path
import jinja2
import os

def cmf(app: Flask):
    for blueprint in app.blueprints.values():
        blueprint.jinja_loader = jinja2.ChoiceLoader([
            jinja2.FileSystemLoader(os.path.join(get_root_path('flask_cmf'), 'templates')),
            blueprint.jinja_loader,
        ])
    app.register_blueprint(Blueprint('flask_cmf', __name__, static_folder='static', static_url_path='/cmf'))
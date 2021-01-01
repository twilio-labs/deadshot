from deadshot.configurations.api_server_config_data import config_map
from flask import Flask
import os
'''
Method to initiate the Flask API server
'''


def create_app(config_object_name=None,
               config_dict=None,
               **kwargs):
    app = Flask(__name__)
    if config_object_name is None:
        config_object_name = os.environ.get("DEADSHOT_CONFIG", "default")
    app.config.from_object(config_map.get(config_object_name))

    if config_dict is not None:
        app.config.from_mapping(config_dict)

    from deadshot.blueprints.blueprints import api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')

    return app

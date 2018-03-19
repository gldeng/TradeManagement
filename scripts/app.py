import os
import sys
from flask import jsonify

dirname = os.path.abspath(os.path.dirname(__file__))

sys.path.insert(0, os.path.join(dirname, '..'))

from trademan import create_app

configfile = os.path.join(dirname, 'app.cfg')

app = create_app(configfile)


@app.route("/site-map")
def site_map():
    links = []
    for rule in app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            links.append((url, rule.endpoint))
    return jsonify(links)

if __name__ == '__main__':
    app.run()

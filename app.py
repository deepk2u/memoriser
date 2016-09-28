from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
import re
import nltk
from collections import Counter
from flask_nav import Nav
from flask_nav.elements import Navbar, View

import logging
from logging.handlers import RotatingFileHandler

from xml.dom.minidom import parseString
import requests
import json

app = Flask(__name__)
Bootstrap(app)

nav = Nav()

@nav.navigation()
def mynavbar():
    return Navbar(
        'Memoriser',
        View('Home', 'home'),
        View('Text', 'text'),
        View('About', 'about'),
    )

nav.init_app(app)

@app.route("/")
@app.route("/<path:url>")
def home(url='/'):
    #return "This is the home page. Your URL is: %s " % url
    return render_template('index.html', title="Home")

@app.route("/add/<int:a>/<int:b>")
def add(a, b):
    return "%s + %s = %s" % (a, b, a + b)

@app.route('/about')
def about():
    return render_template('about.html', title="About")

def deep_search(needles, haystack):
    found = {}
    if type(needles) != type([]):
        needles = [needles]

    if type(haystack) == type(dict()):
        for needle in needles:
            if needle in haystack.keys():
                found[needle] = haystack[needle]
            elif len(haystack.keys()) > 0:
                for key in haystack.keys():
                    result = deep_search(needle, haystack[key])
                    if result:
                        for k, v in result.items():
                            found[k] = v
    elif type(haystack) == type([]):
        for node in haystack:
            result = deep_search(needles, node)
            if result:
                for k, v in result.items():
                    found[k] = v
    return found

@app.route('/text', methods=['GET', 'POST'])
def text():
    results = {}
    url = 'https://content.googleapis.com/dictionaryextension/v1/knowledge/search'
    headers = {'x-origin': 'chrome-extension://mgijmajocgfcbeboacabfgobmjgjcoja'}
    para = ""
    if request.method == 'POST':
        raw = request.form.get('text')
        app.logger.info(raw)
        
        nltk.data.path.append('./nltk_data/')  # set the path
        tokens = nltk.word_tokenize(raw)
        text = nltk.Text(tokens)
        nonPunct = re.compile('.*[A-Za-z0-9].*')
        filtered = [w for w in text if nonPunct.match(w)]
        results = Counter(filtered).items()
        for result in results:
                app.logger.info(result[0])
                payload = {'term': result[0], 'language': 'en', 'key': 'AIzaSyC9PDwo2wgENKuI8DSFOfqFqKP2cKAxxso'}
                resp = requests.get(url, headers=headers, params=payload)
                app.logger.info(resp.text)
                json_data = json.loads(resp.text)
                dic = deep_search(["examples"], json.loads(resp.text))
                para += str(dic["examples"][0])
                para += ". "
        
    return render_template('text.html', title="Text", results=results, para=para)
    


if __name__ == "__main__":
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(debug=True, host="0.0.0.0")
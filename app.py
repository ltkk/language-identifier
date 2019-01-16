from flask import Flask, request, render_template
import fastText as ft
import json
import traceback
import regex as re

app = Flask(__name__)

EMAIL = re.compile(r"([\w0-9_\.-]+)(@)([\d\w\.-]+)(\.)([\w\.]{2,6})")
URL = re.compile(r"https?:\/\/(?!.*:\/\/)\S+")
NUMBER = re.compile(r"\d+.?\d*")

RE_HTML_TAG = re.compile(r'<[^>]+>')
RE_CLEAR_1 = re.compile("[^\s\p{Latin}]")
RE_CLEAR_3 = re.compile("\s+")


class TextPreprocess:
    @staticmethod
    def replace_common_token(txt):
        txt = re.sub(EMAIL, ' ', txt)
        txt = re.sub(URL, ' ', txt)
        txt = re.sub(NUMBER, ' ', txt)
        return txt

    @staticmethod
    def remove_emoji(txt):
        txt = re.sub(':v', '', txt)
        txt = re.sub(':D', '', txt)
        txt = re.sub(':3', '', txt)
        txt = re.sub(':\(', '', txt)
        txt = re.sub(':\)', '', txt)
        return txt

    @staticmethod
    def remove_html_tag(txt):
        return re.sub(RE_HTML_TAG, ' ', txt)

    def preprocess(self, txt):
        txt = self.remove_html_tag(txt)
        txt = re.sub('&.{3,4};', ' ', txt)
        txt = txt.lower()
        txt = self.replace_common_token(txt)
        txt = self.remove_emoji(txt)
        txt = re.sub(RE_CLEAR_1, ' ', txt)
        txt = re.sub(RE_CLEAR_3, ' ', txt)
        return txt.strip()


class LanguageIdentify:
    def __init__(self, model_file='model/lid.176.ftz', language_code_file='language_code.json'):
        self.model = ft.load_model(model_file)
        self.id2lang = json.load(open(language_code_file, encoding='utf8'))
        self.tp = TextPreprocess()

    @staticmethod
    def preprocess(txt):
        txt = re.sub('\n+', ' ', txt)
        txt = txt.lower()
        return txt

    def pred(self, txt):
        txt = self.tp.preprocess(txt)
        res = self.model.predict(txt)
        language_code = res[0][0][9:]
        language = self.id2lang.get(language_code)
        return {'language_code': language_code, 'language': language, 'score': round(res[1][0], 2)}


li = LanguageIdentify()


@app.route('/')
def ping():
    return 'ok'


@app.route('/check', methods=['GET', 'POST'])
def check():
    if request.method == 'GET':
        return render_template('index.html')
    else:
        try:
            txt = request.form['txt']
            if not txt or len(txt) <= 20:
                return render_template('index.html', error='Please type more than 20 characters!')
            _pred = li.pred(txt)
            return render_template('index.html', language=_pred['language'], language_code=_pred['language_code'],
                                   score=+_pred['score'], txt=txt)
        except:
            traceback.print_exc()
            return render_template('index.html', error='Unknown error has occurred, please try again!')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

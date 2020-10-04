from flask import Flask, render_template, request, url_for, flash, redirect, jsonify
import os
from werkzeug.utils import secure_filename

from caption_generator import generate_caption
from ocr import ocr
from color_analyzer import analyze_color
import requests
import json

app = Flask(__name__)
app.debug = False
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.secret_key = 'sopiro'

do_translation = False
remain_upload_image = True
KAKAO_API_KEY = '1b9ef11c3bdeaa8cb71013c0e2ecb9f9'

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

ai_program = {'color': analyze_color, 'ocr': ocr, 'caption': generate_caption}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/rest/<mode>', methods=['POST'])
def rest(mode):
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file', 500

        f = request.files['file']

        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = os.path.abspath('static/uploads/' + filename)

            result = ai_program[mode](image_path)

            if not remain_upload_image:
                os.remove(image_path)

            return json.dumps({'result': result}, ensure_ascii=False), 200
        else:
            return 'Not allowed file format', 500


@app.route('/fileUpload', methods=['POST'])
def file_upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect('/')

        f = request.files['file']

        if f.filename == '':
            flash('파일을 선택해 주세요')
            return redirect('/')

        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            image_path = os.path.abspath('static/uploads/' + filename)
            caption = generate_caption(image_path)
            pre = 'it seems like '

            if do_translation:
                headers = {'Authorization': 'KakaoAK {}'.format(KAKAO_API_KEY)}
                params = {'query': pre + caption, 'src_lang': 'en', 'target_lang': 'kr'}
                res = requests.post(url='https://dapi.kakao.com/v2/translation/translate', headers=headers, data=params)
                korean_caption = res.json()['translated_text'][0][0]

                return render_template('result.html', filename=filename, en_caption=caption, kr_caption=korean_caption)
            else:
                return render_template('result.html', filename=filename, en_caption=caption)
        else:
            return redirect('/')


@app.route('/display/<filename>')
def display_image(filename):
    return redirect(url_for('static', filename='uploads/' + filename), code=301)


@app.route('/delete/<filename>')
def delete_file(filename):
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    except FileNotFoundError:
        pass
    return redirect(url_for('index'))


# @app.teardown_request
# def teardown_request(ex):
#     for f in os.listdir(app.config['UPLOAD_FOLDER']):
#         os.remove(f)


if __name__ == '__main__':
    if not os.path.exists("static"):
        os.mkdir('static')
        os.mkdir('static/uploads')

    # print(os.path.abspath('static/uploads/image.jpg'))
    # print(generate_caption(os.path.abspath('static/uploads/image.jpg')))
    # print(generate_caption(os.path.abspath('static/uploads/elephant.jpg')))

    app.run(host='0.0.0.0')

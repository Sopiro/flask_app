from flask import Flask, render_template, request, url_for, flash, redirect, jsonify
import os
from werkzeug.utils import secure_filename
import json

from caption_generator import generate_caption
from ocr import kakao_ocr
from color_analyzer import analyze_color
from translator import kakao_translator

app = Flask(__name__)
app.debug = False
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.secret_key = 'sopiro'

translate_enabled = False
remain_upload_image = True
KAKAO_API_KEY = '1b9ef11c3bdeaa8cb71013c0e2ecb9f9'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


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

        form_data = dict(request.form)

        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = os.path.abspath('static/uploads/' + filename)

            do_translate = False
            if 'translate' in form_data:
                do_translate = True if form_data['translate'] == 'true' else False

            do_translate = do_translate and translate_enabled

            if mode == 'color':
                if 'count' in form_data:
                    count = int(form_data['count'])
                else:
                    count = 1

                if 'detail' in form_data:
                    detail_color_name_print = True if form_data['detail'] == 'true' else False
                else:
                    detail_color_name_print = False

                color_res = analyze_color(image_path, count)

                result = ''
                for i in range(count):
                    target = color_res[i][1] if detail_color_name_print else color_res[i][3]

                    if do_translate:
                        if detail_color_name_print is not True:
                            target = color_res[i][2]
                        else:
                            target = kakao_translator(target, KAKAO_API_KEY)
                            target = target[:-1] if target[-1] == '.' else target
                            target = target + ' 색'
                    else:
                        if detail_color_name_print:
                            target = target + ' color'

                    result = result + target + '\n'

                result = result[:-1]

            elif mode == 'ocr':
                result = kakao_ocr(image_path, KAKAO_API_KEY)

                if result == -1:
                    if do_translate:
                        result = '문자를 찾을 수 없습니다.'
                    else:
                        result = 'No words found'

            elif mode == 'caption':
                result = generate_caption(image_path)

                if do_translate:
                    result = kakao_translator(result, KAKAO_API_KEY)
            else:
                return 'Mode error: ' + mode, 500

            if not remain_upload_image:
                os.remove(image_path)

            print(result)

            return json.dumps({'result': result}, ensure_ascii=False), 200
        else:
            return 'Not allowed file format', 500


@app.route('/fileUpload', methods=['POST'])
def file_upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect('/')

        f = request.files['file']

        option = request.form['radio_grp']

        if f.filename == '':
            flash('파일을 선택해 주세요')
            return redirect('/')

        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            image_path = os.path.abspath('static/uploads/' + filename)

            result = ''

            if option == 'caption':
                result = generate_caption(image_path)
            elif option == 'color':
                result = analyze_color(image_path)
            elif option == 'text':
                result = kakao_ocr(image_path, KAKAO_API_KEY)

            if translate_enabled:
                korean_caption = kakao_translator(result, KAKAO_API_KEY)

                return render_template('result.html', filename=filename, en_caption=result, kr_caption=korean_caption)
            else:
                return render_template('result.html', filename=filename, en_caption=result)
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


if __name__ == '__main__':
    if not os.path.exists("static"):
        os.mkdir('static')
        os.mkdir('static/uploads')

    # print(os.path.abspath('static/uploads/image.jpg'))
    # print(generate_caption(os.path.abspath('static/uploads/image.jpg')))
    # print(generate_caption(os.path.abspath('static/uploads/elephant.jpg')))

    app.run(host='0.0.0.0')

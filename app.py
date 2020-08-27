from flask import Flask, render_template, request, url_for, flash, redirect
import os
from werkzeug.utils import secure_filename

from caption_generator import generate_caption

app = Flask(__name__)
app.debug = False
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.secret_key = 'sopiro'

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template("index.html")


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

            return render_template('result.html', filename=filename, caption=caption)
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

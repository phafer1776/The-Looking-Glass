import os
from flask import Flask, request, Response, json, jsonify, render_template, redirect, url_for, session, \
    send_from_directory
import sqlite3 as sql
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'png', 'tga', 'tiff', 'gif'])

app = Flask(__name__, template_folder='static')
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'Something hard to guess!'


@app.route('/')
def home():
    return render_template('/index.html')


@app.route('/Login', methods=['GET', 'POST'])
def login_user():
    try:
        username = request.form['username']
        password = request.form['password']
        con = connect('looking_glass.db')
        cur = con.cursor()
        cur.execute("""SELECT * FROM user WHERE username=?""", (username,))
        row = cur.fetchone()
        cur.close()
        con.close()
        print(row)
        if row:
            # Compare username and password to those values in the DB
            if username == row[3] and check_password_hash(str(row[4]), password):
                session['user_id'] = row[0]
                session['firstName'] = row[1]
                session['username'] = username
                print(session)
                json_data = jsonify({
                    'authenticated': True,
                    'user': {
                        'username': username,
                        'firstName': row[1],
                        'lastName': row[2],
                    }
                })
                print(json_data)
                return json_data
                # return redirect('/Dashboard')
            else:
                redirect('/')
                return jsonify({
                    'authenticated': False
                })
    except Exception as e:
        print(e)


@app.route('/SignupUser', methods=['POST'])
def register_user():
    first_name = request.form['firstName']
    last_name = request.form['lastName']
    username = request.form['username']
    password = request.form['password']
    confirmed_password = request.form['passwordConfirmed']
    if first_name and last_name and username and password and confirmed_password:
        if password == confirmed_password:
            password = generate_password_hash(password)
        con = connect('looking_glass.db')
        cur = con.cursor()
        try:
            cur.execute("""INSERT INTO user(firstName, lastName, username, password, contributor, downloads) VALUES """
                        """(?,?,?,?,?,?)""", (first_name, last_name, username, password, False, 0))
            con.commit()
            cur.close()
            con.close()
            return jsonify({
                'registered': True
            })
        except Exception as e:
            print(e)
    return jsonify({
        'formData': 'missing'
    })


@app.route('/Logout')
def logout_user():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('firstName', None)
    return redirect('/')


@app.route('/UploadPhoto')
def show_upload_page():
    return render_template('/Upload.html')


@app.route('/Upload', methods=['GET', 'POST'])
def upload_photo():
    try:
        if request.method == 'POST':
            if 'photo_file' not in request.files:
                print('No file part')
                return redirect(request.url)
            file = request.files['photo_file']
            if file.filename == '':
                print('No file chosen')
                return redirect(request.url)
            if file and file_allowed(file.filename):
                filename = secure_filename(file.filename)
                user_folder = str(session['user_id'])
                user_path = os.path.dirname(os.path.abspath(__file__)) + '/uploads/' + user_folder
                if not os.path.exists(user_path):
                    os.makedirs(user_path)
                app.config['UPLOAD_FOLDER'] = user_path
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                print('Saved file')
                return redirect(url_for('uploaded_photo', filename=filename))
        return
    except Exception as e:
        print(e)


@app.route('/Uploads/<filename>')
def uploaded_photo(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/PopularPhotos')
def load_popular_photos_page():
    return render_template('/Popular.html')


@app.route('/Photos')
def show_user_photos():
    user_path = os.path.dirname(os.path.abspath(__file__)) + '/uploads/' + str(session['user_id'])
    if not os.path.exists(user_path):
        os.makedirs(user_path)
    app.config['UPLOAD_FOLDER'] = user_path
    # server_path = '/static/uploads/' + str(session['user_id']) + '/'
    all_images = []
    file_list = os.listdir(app.config['UPLOAD_FOLDER'])
    print(file_list)
    for image in file_list:
        if file_allowed(image):
            all_images.append('<img src="/Uploads/' + image + '">')
    return str(all_images)


@app.route('/PrivateGallery')
def load_private_photos_page():
    return render_template('/Private.html')


@app.route('/Photo/<int:image_id>', methods=['GET'])
def load_single_photo_page(image_id):
    # Get the image file name from the db, and load it into the html iFrame.
    return render_template('/SinglePhoto.html')


@app.route('/MissionStatement')
def load_mission_statement_page():
    return render_template('/MissionStatement.html')


@app.route('/Dashboard')
def load_dashboard_page():
    if 'username' in session:
        first_name = session['firstName']
        return render_template('/Dashboard.html', first_name=first_name)


# This route is only for DB testing, and will be removed before it is submitted
@app.route('/db')
def db_work():
    """
    The CREATE TABLE commands should only have to be run once. The cursor is how
    database queries are executed using the execute method. You can put your SQL
    statement directly in the parameter. To use python variables in the queries,
    use a comma after the query, and use a python tuple. Use a '?' as a placeholder
    in the query. If you only need one variable, you still need to use a 1 item tuple.
    eg. (username,)
    """
    con = connect('looking_glass.db')
    cur = con.cursor()  # Get cursor

    # Create user table
    cur.execute('CREATE TABLE IF NOT EXISTS user(id integer PRIMARY KEY AUTOINCREMENT, firstName text, lastName text, '
                'username text, password text, contributor boolean, downloads integer)')
    # Create image table
    cur.execute('CREATE TABLE IF NOT EXISTS image(id integer PRIMARY KEY AUTOINCREMENT, title text, userID integer, '
                'rating float, description text, filename text, public boolean, '
                'FOREIGN KEY (userID) REFERENCES user (id))')
    # Create tag table
    cur.execute('CREATE TABLE IF NOT EXISTS tag(id integer PRIMARY KEY AUTOINCREMENT, imageID integer, tag text, '
                'FOREIGN KEY (imageID) REFERENCES image (id))')
    # Create comment table
    cur.execute('CREATE TABLE IF NOT EXISTS comment(id integer PRIMARY KEY AUTOINCREMENT, userID integer, '
                'imageID integer, FOREIGN KEY (userID) REFERENCES user (id), '
                'FOREIGN KEY (imageID) REFERENCES image (id))')
    # Create rating table				 
    cur.execute('CREATE TABLE IF NOT EXISTS rating(id integer PRIMARY KEY AUTOINCREMENT, userID integer, '
                'imageID integer, rating integer, FOREIGN KEY (userID) REFERENCES user (id), '
                'FOREIGN KEY (imageID) REFERENCES image (id))')

    # EXAMPLE EXECUTION OF QUERY
    #
    # cur.execute("""INSERT INTO user(firstName, lastName, username, password, contributor, downloads) VALUES
    # (?,?,?,?,?,?);""", ('Billy', 'Idol', 'theBman', 'password', True, 5))
    # print('Added')
    # cur.execute('SELECT * FROM user')
    # print(cur.fetchall())

    con.commit()


def connect(db_filename):
    """
    This function is used to connect to the database, and display an error to the console
    if unsuccessful. Use this function whenever you need to access the database.
    :param db_filename:
    :return a sqlite db connection:
    """
    try:
        print('Connected to: {}'.format(db_filename))
        return sql.connect(db_filename, timeout=10)
    except Exception as e:
        print(e)


def file_allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_helper(user_id):
    # Check if user uploads folder already exists, and create if necessary.
    if not os.path.join(os.path.dirname(UPLOAD_FOLDER), str(user_id)):
        os.mkdir(os.path.join(os.path.dirname(UPLOAD_FOLDER), str(user_id)))
    return os.path.join(app.config['UPLOAD_FOLDER'], str(user_id) + '/')


if __name__ == '__main__':
    app.run(port=5000)

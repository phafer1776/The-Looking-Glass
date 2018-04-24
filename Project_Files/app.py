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
                # Insert data into DB
                image_title = request.form['title']
                tag_field = request.form['tags']
                image_description = request.form['description']
                con = connect('looking_glass.db')
                cur = con.cursor()
                try:
                    # Check if it already exists for that user
                    cur.execute("""select * from image i where i.filename = ? and i.userid = ?;""",
                                (file.filename, str(session['user_id'])))
                    if cur.fetchone():
                        print('Image is already in your collection')
                        cur.close()
                        con.close()
                        return redirect('/UploadPhoto')
                    cleaned_tags = [tag.strip() for tag in tag_field.split(',') if tag != '']
                    # Call function to insert tags
                    # Save file to user upload folder
                    filename = secure_filename(file.filename)
                    user_folder = str(session['user_id'])
                    user_path = os.path.dirname(os.path.abspath(__file__)) + '/uploads/' + user_folder
                    if not os.path.exists(user_path):
                        os.makedirs(user_path)
                    app.config['UPLOAD_FOLDER'] = user_path
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(image_path)
                    print('Saved file')
                    cur.execute("""insert into image(title, userid, rating, description, filename, path, public) 
                                values (?,?,?,?,?,?,?);""", (image_title, str(session['user_id']), 3,
                                image_description, file.filename, image_path, True))
                    con.commit()
                    cur.execute("""select * from image i where i.filename = ? and i.userid = ?;""",
                                (file.filename, str(session['user_id'])))
                    inserted_image = cur.fetchone()
                    add_tags(cleaned_tags, inserted_image[0])
                    cur.close()
                    con.close()
                    return redirect(url_for('uploaded_photo', filename=filename))
                except Exception as e:
                    print(e)
        return redirect(request.url)
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


@app.route('/Search', methods=['POST'])
def show_resulting_photos():
    if request.method == 'POST':
        print('Post')
    search_value = jsonify({
        'received': True
    })
    print(search_value)
    value = request.form['search']
    results = []
    con = connect('looking_glass.db')
    cur = con.cursor()
    cur.execute("""select * from image i INNER JOIN tag t where i.id = t.imageID and t.tag = ?;""", (value,))
    results.append(cur.fetchall())
    cur.execute("""select * from image i where i.title = ?;""", (value,))
    results.append(cur.fetchall())
    cur.execute("""select * from image i INNER JOIN user u where i.userID = u.id and u.username = ?;""", (value,))
    results.append(cur.fetchall())
    print(results)
    flattened_results = [image for table_results in results for image in table_results]
    print(flattened_results)
    # image path is [i][6], title is [i][1], rating is [i][3]
    return render_template('/Photos.html')
    # return render_template('/Photos.html', flattened_results=flattened_results)


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


@app.route('/Error/<error>', methods=['GET'])
def show_error_page(error):
    return render_template('/error.html', error_message=error)


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
                'rating float, description text, filename text, path text, public boolean, '
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


def add_tags(list_of_tags, image_id):
    con = connect('looking_glass.db')
    cur = con.cursor()
    for image_tag in list_of_tags:
        cur.execute("""insert into tag(imageID, tag) values (?,?);""", (image_id, image_tag))
    con.commit()
    cur.close()
    con.close()


if __name__ == '__main__':
    app.run(port=5000)

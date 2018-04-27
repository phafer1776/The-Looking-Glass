# ---------------------------------------------------------------------------------------------------------------------
# Flask Web Application for The Looking Glass
# Filename: app.py
# Advanced Python - Spring 2018 - University of South Florida
# Group 2: Paul Hafer, Conner Wulf, Timothy Carney, Denis Saez Rodriguez, Joshua Imarhiagbe
# ---------------------------------------------------------------------------------------------------------------------
import os
import sqlite3 as sql
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'png', 'tga', 'tiff', 'gif'])

app = Flask(__name__, template_folder='static')
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'Something hard to guess!'


@app.route('/')
def home():
    """Show the homepage."""
    return render_template('/index.html')


@app.route('/Login', methods=['GET', 'POST'])
def login_user():
    """Authenticate user login information. If the username already exists, check the entered password against the one
    stored in the DB. If it's a match, authenticate the user and send the response to the client. Else the user is not
    authenticated.
    """
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
            else:
                redirect('/')
                return jsonify({
                    'authenticated': False
                })
    except Exception as e:
        print(e)


@app.route('/SignupUser', methods=['POST'])
def register_user():
    """Register a new user. Verify the form data, and if all cells are filled with data, insert the new user data into
    the DB. Send a response to the client.
    """
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
    """Log the user out of the application. Pop the session data for the user, and redirect to the home page."""
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('firstName', None)
    return redirect('/')


@app.route('/UploadPhoto')
def show_upload_page():
    """Show the upload page."""
    return render_template('/upload.html')


@app.route('/Upload', methods=['GET', 'POST'])
def upload_photo():
    """Upload a photo to the server. If the user chooses a valid file to upload, get the form data and connect to the
    DB. If the user has not previously uploaded that file, upload the file to that user's folder on the server. If it is
    the first time that user has uploaded, it creates a folder for that user's ID and uploads the file to that folder.
    Add all relevant information to the DB.
    """
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
                    # Check if the file already exists for that user.
                    cur.execute("""select * from image i where i.filename = ? and i.userid = ?;""",
                                (file.filename, str(session['user_id'])))
                    if cur.fetchone():
                        print('Image is already in your collection')
                        cur.close()
                        con.close()
                        return redirect('/UploadPhoto')
                    # Separate the tags and put them in a list to be added to the DB.
                    cleaned_tags = [tag.strip() for tag in tag_field.split(',') if tag != '']
                    filename = secure_filename(file.filename)  # OS safe filename
                    # Locate the path to the user's folder.
                    user_folder = str(session['user_id'])
                    user_path = os.path.dirname(os.path.abspath(__file__)) + '/static/uploads/' + user_folder
                    if not os.path.exists(user_path):
                        os.makedirs(user_path)
                    app.config['UPLOAD_FOLDER'] = user_path  # Set user's upload folder.
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(image_path)  # Save file to user upload folder
                    print('Saved file')
                    cur.execute("""insert into image(title, userid, rating, description, filename, path, public) 
                                values (?,?,?,?,?,?,?);""", (image_title, str(session['user_id']), 3,
                                image_description, file.filename, image_path, True))
                    con.commit()
                    cur.execute("""select * from image i where i.filename = ? and i.userid = ?;""",
                                (file.filename, str(session['user_id'])))
                    inserted_image = cur.fetchone()
                    add_tags(cleaned_tags, inserted_image[0])  # Add tags to tag table in DB for that image.
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
    """Show uploaded file."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/ShowPhotos')
def show_photos_page():
    try:
        if session['user_id']:
            return redirect('/Photos/' + str(session['user_id']))
        else:
            return render_template('/error.html')
    except Exception as e:
        print(e)


@app.route('/Photos/<user_id>')
def show_user_photos(user_id):
    """Show the photos page for that user. Send the list of images to the HTML for display."""
    try:
        if user_id:
            greeting = session['username'] + '\'s Photos'
            images = []
            user_path = os.path.relpath('static/uploads/' + str(user_id))
            contents = os.listdir(user_path)
            for image in contents:
                images.append(user_path + '\\' + image)
            con = connect('looking_glass.db')
            cur = con.cursor()
            cur.execute("""SELECT i.id, title, rating, username, filename FROM image i INNER JOIN user u WHERE 
                          i.userID = u.id AND u.id = ?;""", (user_id,))
            results = cur.fetchall()
            print(results)
            images = [{'image_id': row[0], 'title': row[1], 'filepath': user_path + '\\' + row[4]}
                      for row in results if row[2] >= 3.0]
            print(images)
            return render_template('/photos.html', user_photos=images, greeting=greeting)
        else:
            return redirect('/PopularPhotos')
    except Exception as e:
        print(e)


@app.route('/PopularPhotos')
def load_popular_photos_page():
    """Show popular photos page if the user is logged in."""
    try:
        if 'username' in session:
            greeting = 'Popular Photos'
            base_path = os.path.relpath('static/uploads/')
            con = connect('looking_glass.db')
            cur = con.cursor()
            cur.execute("""SELECT i.id, title, rating, username, userID, filename FROM image i INNER JOIN user u WHERE 
                                      i.userID = u.id AND i.public = 1;""")
            public_photos = cur.fetchall()
            print(public_photos)
            images = [{'image_id': row[0], 'title': row[1], 'filepath': base_path + '\\' + str(row[4]) + '\\' + row[5]}
                      for row in public_photos if row[2] >= 3.0]
            print(images)
            return render_template('/photos.html', popular_photos=images, greeting=greeting)
    except Exception as e:
        print(e)
    return render_template('/popular.html')


@app.route('/Search/<value>', methods=['GET'])
def search_for_photos(value):
    """Search for photos in the DB by the search value. It searches the DB by tag, title, and username. It then
    converts a list of lists of tuples to a single list of tuples, and sends those to the HTML for display.
    """
    results = []
    base_path = os.path.relpath('static/uploads/')
    con = connect('looking_glass.db')
    cur = con.cursor()
    cur.execute("""SELECT i.id, title, rating, userID, filename FROM image i INNER JOIN tag t WHERE i.id = t.imageID 
                AND t.tag = ?;""", (value,))
    results.append(cur.fetchall())
    cur.execute("""SELECT i.id, title, rating, userID, filename FROM image i WHERE i.title = ?;""", (value,))
    results.append(cur.fetchall())
    cur.execute("""SELECT i.id, title, rating, userID, filename FROM image i INNER JOIN user u WHERE i.userID = u.id 
                AND u.username = ?;""", (value,))
    results.append(cur.fetchall())
    print(results)
    flattened_results = [image for table_results in results for image in table_results]
    print(flattened_results)
    duplicates_removed = list(dict((photo[0], photo) for photo in flattened_results).values())
    print(duplicates_removed)
    images = [{'image_id': row[0], 'title': row[1], 'rating': row[2], 'filepath': base_path + '\\' + str(row[3]) + '\\'
              + row[4]} for row in duplicates_removed]
    return render_template('/photos.html', resulting_photos=images)


@app.route('/PrivateGallery')
def load_private_photos_page():
    """Show the private photo page."""
    return render_template('/private.html')


@app.route('/Photo/<image_id>', methods=['GET'])
def load_single_photo_page(image_id):
    """Show the page for displaying a single photo"""
    try:
        base_path = os.path.relpath('static/uploads/')
        con = connect('looking_glass.db')
        cur = con.cursor()
        cur.execute("""SELECT i.id, title, rating, description, userID, filename, username FROM image i INNER JOIN user u
                    WHERE i.userID = u.id AND i.id = ?;""", (image_id,))
        photo = cur.fetchone()
        print(photo)
        photo_info = {'image_id': photo[0], 'title': photo[1], 'rating': photo[2], 'description': photo[3],
                      'username': photo[6], 'filepath': base_path + '\\' + str(photo[4]) + '\\' + photo[5]}
        print(photo_info['filepath'])
        return render_template('/singlephoto.html', photo=photo_info)
    except Exception as e:
        print(e)


@app.route('/MissionStatement')
def load_mission_statement_page():
    """Show the mission statement page."""
    return render_template('/missionstatement.html')


@app.route('/Error/<error>', methods=['GET'])
def show_error_page(error):
    """Show the error page and send the error to the HTML."""
    return render_template('/error.html', error_message=error)


@app.route('/Dashboard')
def load_dashboard_page():
    """Show the dashboard page only if the user is logged in. Send the user's first name to the HTML
    for a greeting.
    """
    if 'username' in session:
        first_name = session['firstName']
        return render_template('/dashboard.html', first_name=first_name)


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
    """This function is used to connect to the database, and display an error to the console
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
    """This checks the filename to ensure it has an allowed file extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def add_tags(list_of_tags, image_id):
    """Add the list of tags to the tag table in the DB."""
    con = connect('looking_glass.db')
    cur = con.cursor()
    for image_tag in list_of_tags:
        cur.execute("""INSERT INTO tag(imageID, tag) VALUES (?,?);""", (image_id, image_tag))
    con.commit()
    cur.close()
    con.close()


if __name__ == '__main__':
    app.run(port=5000)

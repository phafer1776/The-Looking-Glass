from flask import Flask, request, Response, json, jsonify, render_template, redirect, url_for, session
import sqlite3 as sql
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='static')
app.config['DEBUG'] = True

# Do we need this line???
app.config['SECRET_KEY'] = 'Something hard to guess!'


@app.route('/')
def home():
    return render_template('/index.html')


@app.route('/Login', methods=['POST'])
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
                # redirect('/Dashboard')
                return jsonify({
                    'authenticated': True,
                    'user': {
                        'username': username,
                        'firstName': row[1],
                        'lastName': row[2],
                    }
                })
                # return load_dashboard_page(row[0])
            else:
                redirect('/Dashboard')
                return jsonify({
                    'authenticated': False
                })
    except Exception as e:
        print(e)

#
# @app.route('/Signup')
# def show_signup_overlay():
#     return render_template('SignUp.html')


@app.route('/SignupUser', methods=['POST'])
def register_user():
    first_name = request.form['firstName']
    last_name = request.form['lastName']
    username = request.form['username']
    password = request.form['password']
    confirmed_password = request.form['passwordConfirmed']
    if password == confirmed_password:
        password = generate_password_hash(password)
    con = connect('looking_glass.db')
    cur = con.cursor()
    try:
    #     # Check if username is already taken.
    #     cur.execute("""SELECT * FROM user WHERE username = """ + username + """;""")
    #     duplicate_user = cur.fetchone()
    #     print(duplicate_user)
    # except Exception as e:
    #     print(e)
        # print('Username {} has already been taken. Please choose a different one'.format(duplicate_user))
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


@app.route('/Logout')
def logout_user():
    session.pop('user_id', None)
    return render_template('/')


@app.route('/Upload')
def upload_photo():
    pass


@app.route('/PopularPhotos')
def load_popular_photos_page():
    return render_template('/Popular.html')


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


# This route is temporary.
@app.route('/Dashboard')
def basic_dashboard():
    return render_template('/Dashboard.html')


@app.route('/Dashboard/<int:uid>', methods=['GET', 'POST'])
def load_dashboard_page(uid):
    con = connect('looking_glass.db')
    cur = con.cursor()
    return render_template('/Dashboard.html', user=cur.execute("""SELECT username FROM user WHERE id = ?""",
                                                               (uid,)).fetchone()[0])


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


if __name__ == '__main__':
    app.run(port=5000)

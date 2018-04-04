from flask import Flask, request, Response, json, jsonify, render_template
import sqlite3 as sql

app = Flask(__name__, template_folder='static')
app.config['DEBUG'] = True


@app.route('/')
def home():
    return render_template('/index.html')


@app.route('/photo')
def load_photo_page():
    return render_template('/singlephoto.html')


@app.route('/dashboard/<int:uid>', methods=['GET', 'POST'])
def dashboard(uid):
    con = connect('looking_glass.db')
    cur = con.cursor()
    return render_template('/dashboard.html', user=cur.execute("""SELECT username FROM user WHERE id = ?""",
                                                               (uid,)).fetchone()[0])


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

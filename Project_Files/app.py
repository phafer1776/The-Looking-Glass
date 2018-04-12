from flask import Flask, request, Response, json, jsonify, render_template
import sqlite3 as sql

app = Flask(__name__, template_folder='static')
app.config['DEBUG'] = True


@app.route('/')
def home():
    return render_template('/index.html')

@app.route('/signin')
def signin():
    return render_template('/login-registration.html')

@app.route('/upload')
def upload():
    return render_template('/picture-upload.html')

@app.route('/popular')
def popular():
    return render_template('/Popular.html')

@app.route('/private')
def private():
    return render_template('/Private.html')

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

    def get_user(cursor, username):

        return cursor.execute("select * from user u where u.username = ?;", username)

    def create_user(firstname, lastname, username, password, contributor, downloads, cursor):

        if not get_user(cursor, username):

            cursor.execute(
                "INSERT INTO user(firstname, lastName, username, password, contributor, downloads) "
                "VALUES (?,?,?,?,?,?);",(firstname, lastname, username, username, password, contributor, downloads))

            print('Added {}'.format(username))

        else:
            print('{} already exists'.format(username))

    def get_image(cursor, filename, userid):

        return cursor.execute("select * from image i where i.filename = ? and i.userid = ?;", (filename, userid))

    def insert_image(id, title, userid, rating, description, filename, public, cursor):

        if not get_image(cursor, filename, userid):

            cursor.execute("insert into image(id, title, userid, rating, description, filename, public) "
                           "values (?,?,?,?,?,?,?);", (id, title, userid, rating, description, filename, public))

    def get_image_by_tag(cursor, tag):

        return cursor.execute("select * from image i tag t where i.id = t.imageID and t.tag = ?;"(tag))

    def set_image_tag(cursor, tagid, imageid, tag):

        cursor.execute("insert into tag(id, imageID, tag) values (?,?,?);" (tagid, imageid, tag))

    def get_username(cursor, user_id):

        return cursor.execute("select u.username from user u where u.id = ?;", (user_id))

    def get_firstname(cursor, user_id):

        return cursor.execute("select u.firstName from user u where u.id = ?;", (user_id))

    def get_lastname(cursor, user_id):

        return cursor.execute("select u.lastName from user u where u.id = ?;",(user_id))

    def get_password(cursor, user_id):

        return cursor.execute("select u.password from user u where u.id = ?;", (user_id))

    def get_image_title(cursor, image_id):

        return cursor.execute("select i.username from image i where i.id = ?;", (image_id))

    def get_rating(cursor, image_id):

        return cursor.execute("select i.rating from user i where i.id = ?;", (image_id))

    def set_rating(cursor, image_rate, image_id):

        cursor.execute("update image set rating = ? where id = ?;", (image_rate, image_id))

    def get_description(cursor, image_id):

        return cursor.execute("select i.description from image i where i.id = ?;", (image_id))

    def is_public(cursor, image_id):

        return cursor.execute("select i.public from image i where i.id = ?;", image_id)

    def update_public(cursor, image_id, public):

        cursor.execute("update image set public = ? where i.id = ?;", (public, image_id))

    def get_tags(cursor, image_id):

        return cursor.execute("select t.tag from tag t where t.imageID = ?;", image_id)

    def is_contributor(cursor, user_id):

        return cursor.execute("select u.contributor from user u where u.id = ?;", user_id)

    def update_contributor(cursor, user_id, contributes):

        cursor.execute("update user set contributor = ? where u.id = ?;", (contributes, user_id))

    def get_download_count(cursor, user_id):

        return cursor.execute("select u.downloads from user u where u.id = ?;", user_id)

    def update_download_count(cursor, user_id):

        cursor.execute("update user set downloads = ? "
                              "where id = ?", (get_download_count(cursor, user_id) + 1, user_id))

    def get_comment(cursor, comment_id):

        return cursor.execute("select * from comment c where c.id = ?;", comment_id)

    def get_image_comments(cursor, image_id):

        return cursor.execute("select * from comment c where c.imageID = ?;", image_id)
    
    def add_comment(cursor, comment_id, user_id, image_id):

        if not get_comment(cursor, comment_id):

            cursor.execute("insert into comment (id, userID, imageID) values(?,?,?);", (comment_id, user_id, image_id))


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

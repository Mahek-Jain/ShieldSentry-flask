from flask import Flask, request, render_template
from shieldsentry.shieldsentry import ShieldSentry
from marshmallow import Schema, fields, validate
from marshmallow import ValidationError
import sqlite3

class LoginSchema(Schema):
    username = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    password = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])

app = Flask(__name__)
sentry = ShieldSentry()
login_schema = LoginSchema()

def setup_database():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Create the 'users' table only if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def insert_admin_user():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Check if the admin user already exists
    c.execute("SELECT * FROM users WHERE username='admin'")
    if c.fetchone() is None:
        # Admin user does not exist, so insert
        c.execute("INSERT INTO users VALUES ('admin', 'adminpass')")
        print("Admin user inserted.")
    else:
        # Admin user already exists
        print("Admin user already exists.")

    # Save (commit) the changes and close the connection
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(username, password):
    try:
        conn = get_db_connection()
        query = "SELECT * FROM users WHERE username = '{}' AND password = '{}'".format(username, password)
        user = conn.execute(query).fetchone()
        conn.close()
        return user
    except Exception as e:
        return None


@app.route("/", methods=['GET', 'POST'])
def index():
    message = ''
    if request.method == 'POST':
        raw_username = request.form['username']
        raw_password = request.form['password']

        # Sanitize inputs
        username = sentry.sanitize('SQL', raw_username)
        password = sentry.sanitize('SQL', raw_password)
        
        user = execute_query(username, password)
        
        if user:
            message = 'Logged in successfully!'
        else:
            message = 'Failed to log in!'

    return render_template('index.html', message=message)

@app.route("/vulnerable", methods=['GET', 'POST'])
def vulnerable():
    message = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = execute_query(username, password)

        if user:
            message = 'Logged in successfully!'
        else:
            message = 'Failed to log in!'

    return render_template('vulnerable.html', message=message)

@app.route("/marshmallow", methods=['GET', 'POST'])
def marshmallow():
    message = ''
    if request.method == 'POST':
        try:
            # Validate and deserialize input
            data = login_schema.load(request.form)
            username = data['username']
            password = data['password']

            user = execute_query(username, password)

            if user:
                message = 'Logged in successfully!'
            else:
                message = 'Failed to log in!'

        except ValidationError as err:
            message = 'Failed to log in!'

    return render_template('marshmallow.html', message=message)

if __name__ == "__main__":
    setup_database()
    insert_admin_user()
    app.run(debug=True)
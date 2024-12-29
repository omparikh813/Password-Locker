
import mysql.connector
from flask import Flask, render_template, request, url_for, flash, redirect, session
from email.message import EmailMessage
from werkzeug.exceptions import abort
from cryptography.fernet import Fernet
import hide
import os
import random
import ssl
import smtplib
import sys

# Creates recurring connection
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='root1234',
        database='password_application',
        buffered=True
    )
    return conn

# Finds post for management
def get_login(login_id):
    hide.decryptor()

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Retrives post from database
    cur.execute('SELECT * FROM user_applications WHERE id = %s', (login_id,))
    login = cur.fetchone()
    conn.close()

    # Returns post if found
    if login is None:
        abort(404)
    return login

    hide.encryptor()

# Configures application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'

# Home Page
@app.route('/')
def home():
    return render_template('home.html')

# Login Page
@app.route('/login', methods=('GET', 'POST'))
def login():

    # Retrieves username and password from website form
    if request.method == 'POST':
        hide.decryptor()

        username = request.form['username']
        password = request.form['password']

        # Allows access to variables throughout the session
        session['username'] = username
        session['password'] = password

        # Checks valid input
        if not username or not password:
            flash('Please enter valid information!')
        else:
            conn = get_db_connection()
            cur = conn.cursor()

            # Verifies Account
            cur.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password,))
            data = cur.fetchone()

            hide.encryptor()

            if data:
                # Saved for later use
                email = list(data)[3]
                id = list(data)[0]

                # Allows access throughout the request
                session['email'] = email
                session['id'] = id
            
                # Email Accociates
                sender_email = 'omisdummy@gmail.com'
                sender_pass = os.environ.get("EMAIL_PASSWORD")

                # Email characteristics
                global code
                code = random.randint(100000, 999999)
                subject = 'Two-Step Veriification code'
                body = 'Here is your 6-digit code: ' + str(code)

                em = EmailMessage()
                em['From'] = sender_email
                em['To'] = email
                em['Subject'] = subject
                em.set_content(body)

                # Sends email securely through ssl
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                    smtp.login(sender_email, sender_pass)
                    smtp.sendmail(sender_email, email, em.as_string())
                
                conn.close()

                # Redirect to 2FA page after initial login
                return redirect(url_for('two_factor'))
            else:
                flash('Username or password is incorrect! Please try again or create an account!')

    # Returns webpage from GET request
    return render_template('login.html')

#N ew account creation page
@app.route('/login/new_account', methods=('GET', 'POST'))
def new_account():
    # Retrieves username, password, and email from website form
    if request.method == 'POST':
        #hide.decryptor()

        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT * FROM users WHERE username = %s', (username,))

        # Checks valid input
        if not username or not password or not email:
            flash('Please enter valid information!')
        # Verifies that the inputted username is not already in use
        elif cur.fetchone():
            flash('An account with this username already exists!')
        # Adds new user to database
        else:
            cur.execute('INSERT INTO users (username, password, email) VALUES (%s, %s, %s)', (username, password, email,))
            conn.commit()

            #hide.encryptor()
            conn.close()
        
            # Redirect to login page for new user to login
            return redirect(url_for('login'))
        
    # Returns webpage from GET request
    return render_template('new_account.html')

# Page for two factor authentication
@app.route('/login/2fa', methods=('GET', 'POST'))
def two_factor():
    # Retrieves 2FA code from form
    if request.method == 'POST':
        # Logs user in if code is correct
        if int(request.form['code']) == code:
            return redirect(url_for('pass_list'))
        else:
            flash('Incorrect code, please try again!')
    
    # Returns webpage from GET request
    return render_template('2FA.html')

#Page for accessing passwords
@app.route('/pass_list')
def pass_list():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Retrieves all of the user's passwords to be displayed on the webpage
    cur.execute(
            'SELECT user_applications.id, application, pass FROM users INNER JOIN user_applications ON users.id = user_applications.user_id WHERE username = %s', (session['username'],))
    rows = cur.fetchall()
    conn.close()

    # Returns webpage from GET request
    return render_template('pass_list.html', rows=rows)



# Page to display an application
@app.route('/pass_list/<int:login_id>')
def app_display(login_id):

    # Retrives information for a application login pair
    login = get_login(login_id)

    # Verifies logged in user to prevent browser directory
    if login['user_id'] == session['id']:
        return render_template('app_display.html', login=login)
    else:
        abort(404)


# Page to add passwords
@app.route('/pass_list/add_password', methods=('GET', 'POST'))
def add_password():
    # Retrieves application name and password from form
    if request.method == 'POST':
        application = request.form['application']
        password = request.form['user_pass']

        # Checks valid input
        if not application:
            flash('Please enter valid information!')
        else:
            conn = get_db_connection()
            cur = conn.cursor()

            # Adds inputted login pair to database with the user's unique id
            cur.execute('INSERT INTO user_applications (application, pass, user_id) VALUES (%s, %s, %s)', (application, password, session['id'],))
            conn.commit()
            conn.close()

        # Redirects to password list after adding a new login
        return redirect(url_for('pass_list'))

    # Returns webpage from GET request
    return render_template('add_password.html')

# Page to edit application login pairs
@app.route('/pass_list/<int:login_id>/edit', methods=('GET', 'POST'))
def edit(login_id):

    # Retrives information for a application login pair
    login = get_login(login_id)
    
    if request.method == 'POST':
        application = request.form['application']
        password = request.form['password']

        # Checks valid input
        if not application:
            flash('Please enter valid information!')
        else:
            conn = get_db_connection()
            cur = conn.cursor(dictionary=True)

            # Updates the database with changed login application pair
            cur.execute('UPDATE user_applications SET application = %s, pass = %s WHERE id = %s', (application, password, login_id,))
            conn.commit()
            conn.close()
 
            # Redirects to password list after adding a new login
            return redirect(url_for('pass_list'))

    # Verifies logged in user to prevent browser directory
    if login['user_id'] == session['id']:
        return render_template('edit.html', login=login)
    else:
        abort(404)

@app.route('/pass_list/<int:login_id>/delete', methods=('POST',))
def delete(login_id):

    # Retrives information for a application login pair
    login = get_login(login_id)
    
    conn = get_db_connection()
    cur = conn.cursor()

    # Deletes row of database containing the selected application login
    cur.execute('DELETE FROM user_applications WHERE id = %s AND user_id = %s', (login_id, session['id'],))
    conn.commit()
    conn.close()
    flash('"{}" was successfully deleted!'.format(login['application']))

    # Redirects to password list after deletion
    return redirect(url_for('pass_list'))

import mysql.connector
from flask import Flask, render_template, request, url_for, flash, redirect, session
from email.message import EmailMessage
#from cryptography.fernet import Fernet
import os
import random
import ssl
import smtplib
import sys

#Creates recurring connection
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='root1234',
        database='password_application',
        buffered=True
    )
    return conn

#Configures application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'

#Home Page
@app.route('/')
def home():
    return render_template('home.html')

#Login Page
@app.route('/login', methods=('GET', 'POST'))
def login():
    #hide.decryptor()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        #Allows access throughout the request
        session['username'] = username
        session['password'] = password

        if not username or not password:
            flash('Please enter valid information!')
        else:
            conn = get_db_connection()
            cur = conn.cursor()

            #Verifies Account
            cur.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password,))
            data = cur.fetchone()

            if data:
                email = list(data)[3]
                id = list(data)[0]

                #Allows access throughout the request
                session['email'] = email
                session['id'] = id
            

                sender_email = 'omisdummy@gmail.com'
                sender_pass = os.environ.get("EMAIL_PASSWORD")

                #Email characteristics
                global code
                code = random.randint(100000, 999999)
                subject = 'Two-Step Veriification code'
                body = 'Here is your 6-digit code: ' + str(code)

                em = EmailMessage()
                em['From'] = sender_email
                em['To'] = email
                em['Subject'] = subject
                em.set_content(body)

                #sends email securely through ssl
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                    smtp.login(sender_email, sender_pass)
                    smtp.sendmail(sender_email, email, em.as_string())
                
                conn.close()

                #Redirect to 2FA page
                return redirect(url_for('two_factor'))
            else:
                flash('Username or password is incorrect! Please try again or create an account!')

    return render_template('login.html')

#New account creation
@app.route('/login/new_account', methods=('GET', 'POST'))
def new_account():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT * FROM users WHERE username = %s', (username,))

        if not username or not password or not email:
            flash('Please enter valid information!')
        elif cur.fetchone():
            flash('An account with this username already exists!')
        else:
            cur.execute('INSERT INTO users (username, password, email) VALUES (%s, %s, %s)', (username, password, email,))
            conn.commit()
            conn.close()

            return redirect(url_for('login'))

    return render_template('new_account.html')

#Page for two factor authentication
@app.route('/login/2fa', methods=('GET', 'POST'))
def two_factor():
    if request.method == 'POST':
        if int(request.form['code']) == code:
            #RETURN TO ACCOUNT PAGE
            return redirect(url_for('pass_list'))
        else:
            flash('Incorrect code, please try again!')
    
    return render_template('2FA.html')

#Page for accessing passwords
@app.route('/pass_list')
def pass_list():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute(
            'SELECT application, pass FROM users INNER JOIN user_applications ON users.id = user_applications.user_id WHERE username = %s', (session['username'],))
    rows = cur.fetchall()
    conn.close()

    return render_template('pass_list.html', rows=rows)

#Page to add passwords
@app.route('/pass_list/add_password', methods=('GET', 'POST'))
def add_password():
    if request.method == 'POST':
        application = request.form['application']
        password = request.form['user_pass']

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('INSERT INTO user_applications (application, pass, user_id) VALUES (%s, %s, %s)', (application, password, session['id'],))
        conn.commit()
        conn.close()

        return redirect(url_for('pass_list'))

    return render_template('add_password.html')


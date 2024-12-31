#!/usr/bin/env python3

import mysql.connector
from cryptography.fernet import Fernet

#Connects to database
conn = mysql.connector.connect(
    host='localhost',
    user=os.environ.get("MYSQL_USER"),
    password=os.environ.get("MYSQL_PASS"),
    database='password_application'
)

#Sets cursor for databse
cur = conn.cursor()

def encryptor():
    #Generates encryption key and stores in file
    key = Fernet.generate_key()
    with open('key.key', 'wb') as keyfile:
        keyfile.write(key)

    #Finds rows of usernames and passwords
    cur.execute('SELECT username, password, email FROM users')
    rows = encrypted_rows = cur.fetchall()
    encrypted_rows = [list(row) for row in rows]

    #Iterates through both lists at once to replace original data with encrypted data
    for row, encrypted_row in zip(rows, encrypted_rows):

        #Encrypts rows and stores it in encrypted_rows
        encrypted_row[0] = Fernet(key).encrypt(row[0].encode(encoding="utf-8"))
        encrypted_row[1] = Fernet(key).encrypt(row[1].encode(encoding="utf-8"))

        #Updates original data with encrypted data
        cur.execute('UPDATE users SET username=REPLACE(username, %s, %s)', (row[0], encrypted_row[0],))
        cur.execute('UPDATE users SET password=REPLACE(password, %s, %s) WHERE username=%s', (row[1], encrypted_row[1], encrypted_row[0],))
        cur.execute('UPDATE users SET email=REPLACE(email, %s, %s) WHERE username=%s', (row[2], encrypted_row[2], encrypted_row[0],))

        conn.commit()

    #Finds rows of applications and passwords
    cur.execute('SELECT application, pass FROM user_applications')
    rows = encrypted_rows = cur.fetchall()
    encrypted_rows = [list(row) for row in rows]

    #Iterates through both lists at once to replace original data with encrypted data
    for row, encrypted_row in zip(rows, encrypted_rows):

        #Encrypts rows and stores it in encrypted_rows
        encrypted_row[0] = Fernet(key).encrypt(row[0].encode(encoding="utf-8"))
        encrypted_row[1] = Fernet(key).encrypt(row[1].encode(encoding="utf-8"))

        #Updates original data with encrypted data
        cur.execute('UPDATE user_applications SET application=REPLACE(application, %s, %s)', (row[0], encrypted_row[0],))
        cur.execute('UPDATE user_applications SET pass=REPLACE(pass, %s, %s)', (row[1], encrypted_row[1],))

        conn.commit()



def decryptor():
    #Reopens key file for decryption
    with open('key.key', 'rb') as keyfile:
        key = keyfile.read()

    #Finds rows of encrypted usernames and passwords
    cur.execute('SELECT username, password, email FROM users')
    rows = decrypted_rows = cur.fetchall()
    decrypted_rows = [list(row) for row in rows]

    #Iterates through both lists at once to replace encrypted data with decrypted data
    for row, decrypted_row in zip(rows, decrypted_rows):

        #decrypts rows and stores it in decypted_rows
        decrypted_row[0] = Fernet(key).decrypt(row[0])#.encode(encoding="utf-8"))
        decrypted_row[1] = Fernet(key).decrypt(row[1])#.encode(encoding="utf-8"))

        #Updates original data with encrypted data
        cur.execute('UPDATE users SET username=REPLACE(username, %s, %s)', (row[0], decrypted_row[0],))
        cur.execute('UPDATE users SET password=REPLACE(password, %s, %s) WHERE username=%s', (row[1], decrypted_row[1], decrypted_row[0],))
        cur.execute('UPDATE users SET email=REPLACE(email, %s, %s) WHERE username=%s', (row[2], decrypted_row[2], decrypted_row[0],))

        conn.commit()
    
    #Finds rows of encrypted applications and passwords
    cur.execute('SELECT application, pass FROM user_applications')
    rows = decrypted_rows = cur.fetchall()
    decrypted_rows = [list(row) for row in rows]

    #Iterates through both lists at once to replace encrypted data with decrypted data
    for row, decrypted_row in zip(rows, decrypted_rows):

        #decrypts rows and stores it in decypted_rows
        decrypted_row[0] = Fernet(key).decrypt(row[0])#.encode(encoding="utf-8"))
        decrypted_row[1] = Fernet(key).decrypt(row[1])#.encode(encoding="utf-8"))

        #Updates original data with encrypted data
        cur.execute('UPDATE user_applications SET application=REPLACE(application, %s, %s)', (row[0], decrypted_row[0],))
        cur.execute('UPDATE user_applications SET pass=REPLACE(pass, %s, %s)', (row[1], decrypted_row[1],))

        conn.commit()
    

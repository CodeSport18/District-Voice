import pymongo
from bson.objectid import ObjectId
from datetime import date
from flask import Flask, flash, render_template, request, redirect, session
from passlib.hash import sha256_crypt
import smtplib

loggedIn = False
app = Flask(__name__)
app.secret_key = 'CyvX/N++.huz[H,TnwW2{V8Hx=o|O'

uri = "mongodb+srv://neelvraina:RaspberryPi5@cluster0.obnuqri.mongodb.net/?retryWrites=true&w=majority"
# Create a new client and connect to the server
client = pymongo.MongoClient(uri, tlsAllowInvalidCertificates=True)

# app.config['MONGO_URI'] = 'mongodb+srv://homework:dada@cluster0.u8tap.mongodb.net/specialDays?retryWrites=true&w=majority'
db = client.congressional_app_challenge
username_local = ''


@app.route('/', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        if 'username' not in session:
            return render_template('signup.html')
        else:
            return redirect('/index')

    if request.method == 'POST':
        try:
            document = {}
            f = request.form['fname']
            l = request.form['lname']
            e = request.form['email']
            u = request.form['uname']
            p = sha256_crypt.hash(request.form['pname'])
            document = {'firstname': f, 'lastname': l, 'type': 'user', 'email': e, 'username': u, 'password': p}
            print(document)
            doc = db.account_info.find_one({'username': u})
            if doc == None:
                db.account_info.insert_one(document)
                return redirect('/')
            else:
                flash('Username already exists. Please try again.')
                return redirect('/')
            
        except:
            document = {}
            u = request.form['uname']
            t = request.form['accounttype']
            p = request.form['pname']
            doc = db.account_info.find_one({'username': u})
            if doc:
                # Account Exists
                username_local = u
                if sha256_crypt.verify(p, doc['password']) == True and doc['type'] == t:
                    session['username'] = u
                    session['type'] = t
                    if t == 'representative':
                        return redirect('/complaints')
                    else:
                        return redirect('/index')
                else:
                    return redirect('/')
            else:
                return redirect('/')


@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'username' not in session:
        flash('You must login')
        return redirect('/')
    else:
        if request.method == 'GET':
            # notes = db[session['username']].find().sort("_id", 1)
            # return render_template('index.html', notes=notes)
            return render_template('index.html')
        if request.method == 'POST':
            document = {}
            document['note'] = request.form['note']
            document['date'] = request.form['date']
            document['type'] = request.form['type']
            document['upvotes'] = '0'
            document['username'] = username_local
            document['approvalStatus'] = "False"
            db['complaints'].insert_one(document)
            return redirect('/index')
        
@app.route('/complaints', methods=['GET', 'POST'])
def complaints():
    if 'username' not in session:
        flash('You must login')
        return redirect('/')
    if session['type'] != 'representative':
        flash('You must login')
        return redirect('/')
    else:
        if request.method == 'GET':
            notes = db['complaints'].find({'approvalStatus': 'False'})
            # return render_template('complaints.html', notes=notes)
            return render_template('complaints.html', notes = notes)
        
@app.route('/voting', methods=['GET', 'POST'])
def voting():
    if 'username' not in session:
        flash('You must login')
        return redirect('/')
    else:
        if request.method == 'GET':
            notes = db['complaints'].find({'approvalStatus': 'True'}).sort("upvotes", -1)
            # return render_template('votes.html', notes=notes)
            return render_template('votes.html', notes = notes)
        if request.method == 'POST':
            document = {}
            document['note'] = request.form['note']
            document['date'] = request.form['date']
            document['type'] = request.form['type']
            document['username'] = username_local
            db['complaints'].insert_one(document)
            return redirect('/complaints')
    
@app.route('/delete/<note_id>', methods=['GET', 'POST'])
def delete(note_id):
    db['complaints'].delete_one({'_id': ObjectId(note_id)})
    return redirect('/')

@app.route('/upForVote/<note_id>', methods=['GET', 'POST'])
def upForVote(note_id):
    doc = db.complaints.find_one({'_id': ObjectId(str(note_id)) })

    filter = {'_id': ObjectId(str(note_id))}

    update = {'$set': {'approvalStatus': "True"}}

    # Update a single document matching the filter
    db.complaints.update_one(filter, update)

    print(doc['approvalStatus'])
    return redirect('/voting')

@app.route('/upvote/<note_id>', methods=['GET', 'POST'])
def upvote(note_id):
    user = session['username']  # Get the current logged-in user
    note = db.complaints.find_one( {'_id': ObjectId(str(note_id))} )

    # Check if the user has already upvoted this note
    if db.user_upvotes.find_one({'user_id': user, 'note_id': note['_id']}):
        flash("You have already upvoted this note.", "warning")  # Store a flash message
        return redirect('/voting')

    # Record the upvote in the 'complaints' collection
    filter = {'_id': ObjectId(str(note_id))}
    update = {'$set': {'upvotes': str(int(note['upvotes']) + 1)}}
    db.complaints.update_one(filter, update)

    # Record the upvote in the 'user_upvotes' collection
    db.user_upvotes.insert_one({'user_id': user, 'note_id': note['_id']})

    return redirect('/voting')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout successful')
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from keras_facenet import FaceNet
import cv2 as cv
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import os
from PIL import Image
import io
import base64
# import our model from folder
facenet = FaceNet()
faces_embeddings = np.load("/Users/siddharthamalik/Downloads/face-recognition-with-liveness-web-login-master/faces_embeddings_classes.npz")
Y = faces_embeddings['arr_1']
faces_embeddings=faces_embeddings['arr_0']

haarcascade = cv.CascadeClassifier("/Users/siddharthamalik/Downloads/face-recognition-with-liveness-web-login-master/haarcascade_frontalface_default.xml")
similarity_threshold = 0.7

def chec(im):
    rgb_img = cv.cvtColor(im, cv.COLOR_BGR2RGB)
    gray_img = cv.cvtColor(im, cv.COLOR_BGR2GRAY)
    faces = haarcascade.detectMultiScale(gray_img, 1.3, 5)
    for x,y,w,h in faces:
        img = rgb_img[y:y+h, x:x+w]
        img = cv.resize(img, (160,160)) 
        img = np.expand_dims(img,axis=0)
        new_face_embedding = facenet.embeddings(img)
        similarity_scores = cosine_similarity(new_face_embedding, faces_embeddings)
        max_index = np.argmax(similarity_scores)


        if similarity_scores[0][max_index] > similarity_threshold:


            identified_person = Y[max_index]
            return(identified_person)

        else:
            return('No identified person.')

app = Flask(__name__)
app.secret_key = 'web_app_for_face_recognition_and_liveness' # something super secret
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Users(db.Model):
    username = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(100))
    password = db.Column(db.String(100))

new_user_2 = Users(username='priyanshu', password='123456789', name='priyanshu')
new_user_3 = Users(username='akshan', password='123456789', name='akshan')
db.session.add(new_user_2)
db.session.add(new_user_3)
db.session.commit()
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        session.pop('name', None)
        username = request.form.get('username')
        password = request.form.get('password')
        
        f = request.form.get('captured_image_data')
        f=f.split(',')[1]
        imgdata = base64.b64decode(str(f))
        img = Image.open(io.BytesIO(imgdata))
        im = np.array(img)
        
        user = Users.query.filter_by(username=username).first()
        if user is not None and user.password == password:
            session['name'] = user.name 
            detected_name=chec(im)
            if user.name == detected_name:
                return redirect(url_for('main'))
            else:
                return render_template('login_page.html', invalid_user=True, username=username)
        else:
            return render_template('login_page.html', incorrect=True)

    return render_template('login_page.html')

@app.route('/main', methods=['GET'])
def main():
    name = session['name']
    return render_template('main_page.html', name=name)

if __name__ == '__main__':
    db.create_all()

    # add users to database

    # new_user = Users(username='jom_ariya', password='123456789', name='Ariya')
    # db.session.add(new_user)

    #new_user_2 = Users(username='priyanshu', password='123456789', name='priyanshu')
    #new_user_3 = Users(username='akshan', password='123456789', name='akshan')
    #db.session.add(new_user_2)
    #db.session.add(new_user_3)

    app.run(debug=True)

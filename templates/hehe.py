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
            return({identified_person})

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
        print(f)
        imgdata = base64.b64decode(str(f))
        img = Image.open(io.BytesIO(imgdata))
        im = np.array(img)
        
        user = Users.query.filter_by(username=username).first()
        print(user)
        if user is not None and user.password == password:
            session['name'] = user.name 
            detected_name=chec(im)
            print(detected_name)
            return detected_name
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

    # new_user_2 = Users(username='earth_ekaphat', password='123456789', name='Ekaphat')
    # new_user_3 = Users(username='bonus_ekkawit', password='123456789', name='Ekkawit')
    # db.session.add(new_user_2)
    # db.session.add(new_user_3)

    app.run(debug=True)


    <!DOCTYPE html>
<html lang="en">
<head>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">
    <link rel="stylesheet" href="https://code.getmdl.io/1.3.0/material.indigo-pink.min.css">
    <script defer src="https://code.getmdl.io/1.3.0/material.min.js"></script>
    <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/webcamjs/1.0.24/webcam.js"></script>
    <meta charset="UTF-8">
    <title>Login Page</title>

</head>
<body>
  <div class="signin">
    <div class="back-img">
      <h2 class="active">Face Login</h2>
      <div class="sign-in-text">
        <h3 class="active">Sign In</h3>
      </div><!--/.sign-in-text-->
      <div class="layer">
      </div><!--/.layer-->
      <p class="point">&#9650;</p>
    </div><!--/.back-img-->
    <div class="form-section">
      {% if incorrect == True %}
      <p style="color:red"> Username or Password is incorrect </p>
      {% elif invalid_user == True %}
      <p style="color:red"> You are not {{username}} </p>
      {% endif %}
      <form id="signInForm" method="POST" enctype="multipart/form-data">
        <!-- Email -->
        <div class="mdl-textfield mdl-js-textfield mdl-textfield--floating-label">
            <input class="mdl-textfield__input" type="text" id="username" name="username">
            <label class="mdl-textfield__label" for="sample3">Username</label>
        </div>
        <br/>
        <br/>
        <!-- Password -->
        <div class="mdl-textfield mdl-js-textfield mdl-textfield--floating-label">
            <input pattern=".{8,}" class="mdl-textfield__input" type="password" id="password" name="password">
            <label class="mdl-textfield__label" for="sample3">Password</label>
            <span class="mdl-textfield__error">Minimum 8 characters</span>
        </div>
        <br/>
        <p class="forgot-text">Forgot Password ?</p>
        <!-- CheckBox -->
        <div class="container">  
            <div class="row">
                <div class="col-lg-6" align="center">
                    <label>Capture live photo</label>
                    <div id="my_camera" class="pre_capture_frame"></div>
                    <br>
                    <button type="button" id ="captured_image_data_hi"class="btn btn-info btn-round btn-file" onclick="take_snapshot()">Take Snapshot</button>
                    <input type="hidden" id="captured_image_data_img" name="captured_image_data">
                </div>
                <div class="col-lg-6" align="center">
                    <label>Result</label>
                    <div id="results" >
                        <img style="width: 350px;" class="after_capture_frame" id="captured_image_preview" src="image_placeholder.jpg" />
                    </div>
                </div>  
            </div><!--  end row -->
        </div>
        <label class="mdl-checkbox mdl-js-checkbox mdl-js-ripple-effect" for="checkbox-1">
            <input type="checkbox" id="checkbox-1" class="mdl-checkbox__input" checked>
            <span class="keep-text mdl-checkbox__label">Keep me Signed In</span>
        </label>
        <button type="button" class="sign-in-btn mdl-button mdl-js-ripple-effect mdl-js-button mdl-button--raised mdl-button--colored" id="sub_button">
            Sign In
        </button><!--/button-->
    </form>
 <!--/.signin-->
 <script>
  var img_uri
  // Function to take a snapshot
  function take_snapshot() {
    Webcam.snap(function(data_uri) {
      // Display captured image preview
      var capturedImagePreview = document.getElementById('captured_image_preview');
      capturedImagePreview.src = data_uri;
      img_uri = data_uri

    });
  }

  // Initialize webcam
  Webcam.set({
    width: 320,
    height: 240,
    image_format: 'jpeg',
    jpeg_quality: 90
  });
  Webcam.attach('#my_camera');

  // Function to submit the form
  function submitForm() {
    const img = document.getElementById("captured_image_data")
    fetch(img.src).then(res=>res.blob()).then(blob=>{
      const file = new File([blob],'test.png',blob)
      console.log(file)
      document.getElementById('signInForm').submit();
    })
    // Submit the form
    //document.getElementById('signInForm').submit();
  }

  document.getElementById("sub_button").addEventListener("click",function(event){
    event.preventDefault();
        var username = document.getElementById('username').value
        console.log(username)
      // Create FormData object and append image data
      var formData = new FormData();
      formData.append('username',username);
      formData.append('password',document.getElementById('password').value);
      formData.append('captured_image_data', img_uri);
      
      // Make HTTPS request to Flask API
      fetch('/login', {
        method: 'POST',
        body: formData
      }).then(res=>res.json())
      .then(response => {
        console.log(response)
      })
      .catch(error => {
        console.error('Error uploading image:', error);
      });
  })
</script>
</body>
</html>

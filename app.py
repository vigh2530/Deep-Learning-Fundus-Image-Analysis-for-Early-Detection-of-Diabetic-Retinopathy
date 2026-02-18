from tensorflow.keras.models import load_model
from flask import Flask, render_template, request, session, redirect, url_for, flash
import numpy as np
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.xception import preprocess_input
from pymongo import MongoClient
import os

# -------------------- MongoDB Connection --------------------
client = MongoClient("mongodb://localhost:27017/")
db = client["diabetic_retinopathy_db"]
users_collection = db["users"]

# -------------------- Flask App --------------------
app = Flask(__name__)
app.secret_key = "hiuffhhwiuf"

# -------------------- Load Model --------------------
model = load_model("Updated-Xception-diabetic-retinopathy.h5")

# -------------------- Upload Folder --------------------
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------- Home Page --------------------
@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template("home.html")

# -------------------- Register --------------------
@app.route("/register", methods=['GET', 'POST'])
def regis():
    if request.method == "POST":

        user_data = {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "password": request.form.get("password")
        }

        users_collection.insert_one(user_data)

        return redirect(url_for("login"))

    return render_template("register.html")

# -------------------- Login --------------------
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":

        session.pop("user", None)

        email = request.form.get("email")
        password = request.form.get("password")

        user = users_collection.find_one({
            "email": email,
            "password": password
        })

        if user:
            session['user'] = user['name']
            return redirect(url_for("pred"))
        else:
            flash("Invalid Email or Password")
            return render_template("login.html")

    return render_template("login.html")

# -------------------- Prediction --------------------
@app.route("/prediction", methods=['GET', 'POST'])
def pred():

    if "user" not in session:
        return redirect(url_for("login"))

    name = session['user']

    if request.method == "POST":

        file = request.files["file"]

        if file.filename == "":
            return "No file selected"

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        img = image.load_img(filepath, target_size=(299, 299))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)

        prediction = model.predict(img_array)
        predicted_class = np.argmax(prediction, axis=1)[0]
        confidence = float(np.max(prediction) * 100)

        class_labels = {
            0: "No_DR",
            1: "Mild_DR",
            2: "Moderate_DR",
            3: "Severe_DR",
            4: "Proliferative_DR"
        }

        result = class_labels[predicted_class]

        return render_template(
            "prediction.html",
            name=name,
            prediction=result,
            confidence=round(confidence, 2),
            uploaded_image=filepath
        )

    return render_template("prediction.html", name=name)

# -------------------- Logout --------------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# -------------------- Run App --------------------
if __name__ == "__main__":
    app.run(debug=True)

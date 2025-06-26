from flask import Flask, render_template, request, redirect, session, url_for
from replit import db
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'furrbutler_secret_key'

    # Setup for photo uploads
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Utility to check file type
def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    # Home
@app.route('/')
def home():
        if "user" in session:
            return redirect(url_for('dashboard'))
        return render_template("index.html")

    # Register
@app.route('/register', methods=["GET", "POST"])
def register():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")

            if not email or not password:
                return "Please enter both email and password."

            if f"user:{email}" in db:
                return "User already exists. Try logging in."

            db[f"user:{email}"] = {
                "email": email,
                "password": password
            }

            return redirect(url_for("login"))
        return render_template("register_new.html")

    # Login
@app.route('/login', methods=["GET", "POST"])
def login():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")

            if not email or not password:
                return "Please enter both email and password."

            user_key = f"user:{email}"
            user = db.get(user_key)

            if user and user["password"] == password:
                session["user"] = email
                return redirect(url_for("dashboard"))
            else:
                return "Invalid email or password."

        return render_template("login.html")
    #Vendor Login
@app.route('/vendor-login', methods=["GET", "POST"])
def vendor_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return "Please enter both email and password."

        vendor_key = f"vendor:{email}"
        vendor = db.get(vendor_key)

        if vendor and vendor["password"] == password:
            session["vendor"] = email
            return redirect("https://erp.furrbutler.com")  # placeholder, or use a future ERP route
        else:
            return "Invalid vendor login."

    return render_template("vendor_login.html")
    # Dashboard
@app.route('/dashboard')
def dashboard():
        if "user" not in session:
            return redirect(url_for("login"))

        email = session["user"]
        return render_template("dashboard.html", email=email)

    # Groomers & Vendors
@app.route('/groomers')
def groomers():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("groomers.html")

@app.route('/vendor/<vendor_id>')
def vendor_profile(vendor_id):
    if "user" not in session:
        return redirect(url_for("login"))

    # Fake static vendor
    if vendor_id == "fluffy-paws":
        vendor = {
            "name": "Fluffy Paws Grooming",
            "description": "Fluffy Paws offers expert grooming services for dogs and cats. We specialize in treating your pets like royalty.",
            "image": "https://place-puppy.com/600x400",
            "services": ["Full Grooming", "Nail Clipping", "Ear Cleaning"],
            "market_url": "#",
            "booking_url": "/vendor/fluffy-paws/book"
        }
        return render_template("vendor_profile.html", vendor=vendor)

    # Placeholder vendors (ERP-linked in future)
    else:
        return render_template("vendor_placeholder.html", vendor_name=vendor_id.replace("-", " ").title())

    # Book a service
@app.route('/vendor/<vendor_id>/book', methods=["GET", "POST"])
def book_vendor(vendor_id):
    if "user" not in session:
        return redirect(url_for("login"))

    if vendor_id != "fluffy-paws":
        return "Booking only available for Fluffy Paws demo vendor."

    services = ["Full Grooming", "Nail Clipping", "Ear Cleaning"]

    if request.method == "POST":
        selected_service = request.form.get("service")
        selected_date = request.form.get("date")

        # Future: Save booking to db or send confirmation
        print(f"Booking: {selected_service} on {selected_date}")

        return redirect(url_for("dashboard"))  # You can add a success message later

    return render_template("booking.html", vendor_name="Fluffy Paws Grooming", services=services)


    # Restaurants & Boarding
@app.route('/boarding')
def boarding():
        if "user" not in session:
            return redirect(url_for("login"))
        return render_template("boarding.html")

    # Vets & Pharma
@app.route('/vets')
def vets():
        if "user" not in session:
            return redirect(url_for("login"))
        return render_template("vets.html")


    # Pet Profile
@app.route('/pet-profile', methods=["GET", "POST"])
def pet_profile():
        if "user" not in session:
            return redirect(url_for("login"))

        # Load dog breeds from JSON
        with open("dog_breeds.json", "r") as f:
            breeds = json.load(f)

        user = session["user"]
        pets = db.get(f"pets:{user}", [])

        if request.method == "POST":
            name = request.form.get("name")
            birthday = request.form.get("birthday")
            breed = request.form.get("breed")
            blood = request.form.get("blood")
            photo_url = ""

            file = request.files.get("photo")
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                photo_url = "/" + filepath

            pet = {
                "name": name,
                "birthday": birthday,
                "breed": breed,
                "blood": blood,
                "photo": photo_url
            }

            pets.append(pet)
            db[f"pets:{user}"] = pets

            return redirect(url_for("pet_profile"))

        return render_template("pet_profile.html", breeds=breeds, pets=pets)
    # add pet
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/pet-profile/add', methods=['GET', 'POST'])
def add_pet():
    if "user" not in session:
        return redirect(url_for("login"))

    # Load dog breeds from JSON
    with open("dog_breeds.json", "r") as f:
        breeds = json.load(f)

    if request.method == 'POST':
        name = request.form.get("name", "").strip()
        birthday = request.form.get("birthday")
        breed = request.form.get("breed")
        blood = request.form.get("blood")
        photo = request.files.get("photo")

        if not name:
            return "Pet name is required."

        filename = None
        if photo and photo.filename:
            filename = secure_filename(photo.filename)
            try:
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            except Exception as e:
                print("Image save failed:", e)

        # Get existing pets or create empty list
        user = session["user"]
        pets = db.get(f"pets:{user}", [])

        # Add new pet to the list
        pet = {
            "name": name,
            "birthday": birthday,
            "breed": breed,
            "blood": blood,
            "photo": filename
        }

        pets.append(pet)
        db[f"pets:{user}"] = pets

        print("Saved pet:", pet)
        print("Total pets:", len(pets))

        return redirect(url_for("pet_profile"))

    return render_template("add_pet.html", breeds=breeds)
    #edit profile
@app.route('/pet-profile/edit/<int:index>', methods=["GET", "POST"])
def edit_pet(index):
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    pets = db.get(f"pets:{user}", [])

    if index >= len(pets):
        return "Pet not found"

    # Load dog breeds
    with open("dog_breeds.json", "r") as f:
        breeds = json.load(f)

    if request.method == "POST":
        pets[index]["name"] = request.form.get("name")
        pets[index]["birthday"] = request.form.get("birthday")
        pets[index]["breed"] = request.form.get("breed")
        pets[index]["blood"] = request.form.get("blood")

        db[f"pets:{user}"] = pets
        return redirect(url_for("pet_profile"))

    return render_template("edit_pet.html", pet=pets[index], index=index, breeds=breeds)

    # Logout
@app.route('/logout')
def logout():
        session.clear()
        return redirect(url_for("home"))

    # Run app
if __name__ == '__main__':
        app.run(host='0.0.0.0', port=81, debug=True)

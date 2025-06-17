from flask import Flask, render_template, request, redirect, session, url_for
from replit import db  # Replit's key-value database

app = Flask(__name__)
app.secret_key = 'furrbutler_secret_key'  # needed to manage sessions

# Home page
@app.route('/')
def home():
    if "user" in session:
        return redirect(url_for('dashboard'))
    return render_template("index.html")

# Register page (TEMPORARY FIX with renamed HTML)
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name")

        if f"user:{email}" in db:
            return "User already exists. Try logging in."

        db[f"user:{email}"] = {
            "email": email,
            "password": password,
            "name": name
        }

        return redirect(url_for("login"))
    return render_template("register_new.html")  # <-- changed this line

# Login page
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Check if it's role-based login (old system)
        if "role" in request.form:
            role = request.form.get("role")
            session["user"] = role
            session["role"] = role
            return redirect(url_for("dashboard"))
        
        # Check if it's email/password login (new system)
        email = request.form.get("email")
        password = request.form.get("password")
        
        if email and password:
            user_key = f"user:{email}"
            user = db.get(user_key)

            if user and user["password"] == password:
                session["user"] = user["email"]
                session["name"] = user["name"]
                return redirect(url_for("dashboard"))
            else:
                return "Invalid email or password"

    return render_template("login.html")

# Dashboard after login
@app.route('/dashboard')
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    # Handle role-based login
    if "role" in session:
        return render_template("dashboard.html", role=session["role"])
    
    # Handle registered user login
    if "name" in session:
        return render_template("dashboard.html", role=session["name"])
    
    # Fallback for registered users without cached name
    user_email = session["user"]
    user_data = db.get(f"user:{user_email}")
    if user_data:
        return render_template("dashboard.html", role=user_data["name"])
    
    return redirect(url_for("login"))

# Logout
@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81)

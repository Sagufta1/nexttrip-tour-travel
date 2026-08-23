import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, redirect, url_for, request,session
from werkzeug.security import generate_password_hash, check_password_hash
# generate_password_hash() is used to hash the password before storing it in the database. check_password_hash() is used to verify the password entered by the user during login.
import pymysql
pymysql.install_as_MySQLdb()
from flask_mysqldb import MySQL
from datetime import datetime

app = Flask(__name__)

# MySQL database settings
app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST")
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER")
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD")
app.config["MYSQL_DB"] = os.getenv("MYSQL_DB")
app.config["MYSQL_PORT"] = int(os.getenv("MYSQL_PORT", 3306))
mysql = MySQL(app)

app.secret_key = os.getenv("SECRET_KEY")     # Secret key is required to use Flask sessions

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return redirect(url_for("home") + "#about-us")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/package")
def package():
    cursor = mysql.connection.cursor()  # Connect to MySQL
    cursor.execute("SELECT * FROM packages")     # Get all packages from the database
    packages = cursor.fetchall()     # Store the packages
    print(packages)
    cursor.close()   # Close the connection

    return render_template("package.html", packages=packages)  # Send the packages to package.html


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":    #if the user submits the login form
        email = request.form["email"]   # Get email and password from login.html
        password = request.form["password"]
        cursor = mysql.connection.cursor()  # Connect to MySQL

        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )   # Find the user using their email
        
        user = cursor.fetchone()   # Get the user's data from the database
        cursor.close()      # Close database connection
        # Check: if  User exists, Entered password matches the hashed password
        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]   # Save user information in the session
            session["username"] = user[1]
            session["email"] = user[2]
            session["is_admin"] = user[4]  # Stores admin status in session

            return redirect(url_for("home"))  # Login successful → go to home page
        else:   # Login failed
            return render_template("login.html", error="Invalid email or password")  # Show error message
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":  #user submits the registration form
        name = request.form["name"]   # Get details from register.html
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)  # Convert password into a secure hash
        cursor = mysql.connection.cursor()   # Connect to MySQL
        # We save the HASH, not the real password
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password)
        )
        mysql.connection.commit()  # Save changes

        cursor.close()  # Close database connection
        return redirect(url_for("home"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    # Remove the user information from the session
    session.pop("user_id", None)
    session.pop("username", None)
    session.pop("email", None)

    # Go back to the home page
    return redirect(url_for("home"))


@app.route("/book-now", methods=["GET", "POST"])
def book_now():
    if "user_id" not in session:   # Check if the user is logged in
        return redirect(url_for("login"))

    today = datetime.today().strftime("%Y-%m-%d")     # Get today's date

    if request.method == "POST":
        # Get booking information from the form
        destination = request.form.get("destination", "").strip()
        travel_date = request.form.get("travel_date", "").strip()
        people_text = request.form.get("people", "").strip()
        phone = request.form.get("phone", "").strip()

        # Check if any required field is empty
        if not destination or not travel_date or not people_text or not phone:
            return render_template("book_now.html",error="Please fill in all fields.",today=today)
        # Check if travel date is valid
        try:
            selected_date = datetime.strptime(travel_date, "%Y-%m-%d").date()
            # Prevent past dates
            if selected_date < datetime.today().date():
                return render_template("book_now.html",error="Travel date cannot be in the past.",today=today)
        except ValueError:
            return render_template("book_now.html",error="Please enter a valid travel date.",today=today)
        # Check if number of people is valid
        try:
            people = int(people_text)
            if people <= 0:
                return render_template("book_now.html",error="Number of people must be at least 1.",today=today)

        except ValueError:
            return render_template("book_now.html",error="Please enter a valid number of people.",today=today)

        user_id = session["user_id"] # Get the logged-in user's ID
        
        cursor = mysql.connection.cursor()  # Connect to MySQL
        # Find the price of the selected package
        cursor.execute("SELECT price FROM packages WHERE destination = %s",(destination,))
        package = cursor.fetchone()
        # Check if the package exists
        if not package:
            cursor.close()
            return render_template("book_now.html",error="Selected package is not available.",today=today)
 
        price = package[0]  # Get package price    
        amount = price * people # Calculate total amount
        # Save the booking in the database
        cursor.execute("""INSERT INTO bookings(user_id, destination, travel_date, people, amount, phone)VALUES (%s, %s, %s, %s, %s, %s)""",(user_id,destination,travel_date,people,amount,phone))

        mysql.connection.commit()  # Save the booking
        cursor.close()  # Close database connection
        # Show booking confirmation
        return render_template("book_now.html",message="Booking Confirmed!",booking_done=True,today=today)

    # Show booking form
    return render_template("book_now.html",today=today)


@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()
    # Get the user's details
    cursor.execute(
        "SELECT name, email FROM users WHERE id = %s",
        (session["user_id"],)
    )

    user = cursor.fetchone()
    # Get the user's bookings
    cursor.execute("SELECT * FROM bookings WHERE user_id = %s",(session["user_id"],)
    )
    bookings = cursor.fetchall()
    cursor.close()

    return render_template("profile.html",user=user,bookings=bookings)

@app.route("/cancel-booking/<int:booking_id>")  
def cancel_booking(booking_id):  

    if "user_id" not in session:  # Checks whether the user is logged in
        return redirect(url_for("login"))  

    cursor = mysql.connection.cursor()  # Creates a connection to the MySQL database

    cursor.execute( 
        "DELETE FROM bookings WHERE id = %s AND user_id = %s",  # Deletes the selected booking only if it belongs to this user
        (booking_id, session["user_id"])  # Provides the booking ID and logged-in user's ID
    )

    mysql.connection.commit()  # Saves the deletion permanently in the database
    cursor.close()  # Closes the database connection
    return redirect(url_for("profile"))  # Sends the user back to their profile page

@app.route("/admin")
def admin():
    if "user_id" not in session:   # Check if user is logged in
        return redirect(url_for("login"))
    
    user_id = session["user_id"]  # Get user ID

    cursor = mysql.connection.cursor()   # Check if user is admin
    cursor.execute("SELECT is_admin FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if not user or user[0] != 1:   # Not admin
        cursor.close()
        return "Access Denied"

    cursor.execute("SELECT * FROM packages")  # Get all packages
    packages = cursor.fetchall()
    cursor.close()
    return render_template("admin.html", packages=packages)

@app.route("/admin/add", methods=["POST"])  # Handles adding a package
def admin_add():
    if "user_id" not in session:  # Check if user is logged in
        return redirect(url_for("login"))  # Go to login page

    user_id = session["user_id"]  # Get logged-in user's ID
    cursor = mysql.connection.cursor()  # Open database connection

    cursor.execute(
        "SELECT is_admin FROM users WHERE id = %s",
        (user_id,)
    )  # Check admin status

    user = cursor.fetchone()  # Get admin information

    if not user or user[0] != 1:  # Check if user is not admin
        cursor.close()  # Close database
        return "Access Denied"  # Block access

    # Get package information from form
    name = request.form["name"]  # Package name
    destination = request.form["destination"]  # Destination
    price = request.form["price"]  # Price
    description = request.form["description"]  # Description
    image = request.form["image"]  # Image
    duration = request.form["duration"]  # Duration
    highlight1 = request.form["highlight1"]  # Highlight 1
    highlight2 = request.form["highlight2"]  # Highlight 2
    highlight3 = request.form["highlight3"]  # Highlight 3

    # Insert new package
    cursor.execute("""INSERT INTO packages(name, destination, price, description, image, duration,highlight1, highlight2, highlight3)VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
        (name,destination,price,description,image,duration,highlight1,highlight2,highlight3))

    mysql.connection.commit()  # Save package permanently
    cursor.close()  # Close database connection
    return redirect(url_for("admin"))  # Return to Admin Panel


@app.route("/admin/edit", methods=["POST"])
def admin_edit():
    if "user_id" not in session:  # Check if user is logged in
        return redirect(url_for("login"))  # Go to login page

    user_id = session["user_id"]  # Get logged-in user's ID
    cursor = mysql.connection.cursor()  # Open database connection
    cursor.execute(
        "SELECT is_admin FROM users WHERE id = %s",
        (user_id,)
    )  # Check admin status

    user = cursor.fetchone()  # Get admin information

    if not user or user[0] != 1:  # Check if user is not admin
        cursor.close()  # Close database
        return "Access Denied"  # Block access

    # Get edited package information
    package_id = request.form["id"]  # Get package ID
    name = request.form["name"]  # Get package name
    destination = request.form["destination"]  # Get destination
    price = request.form["price"]  # Get price
    description = request.form["description"]  # Get description
    image = request.form["image"]  # Get image
    duration = request.form["duration"]  # Get duration
    highlight1 = request.form["highlight1"]  # Get highlight 1
    highlight2 = request.form["highlight2"]  # Get highlight 2
    highlight3 = request.form["highlight3"]  # Get highlight 3

    # Update package in database
    cursor.execute("""UPDATE packages SET name = %s,destination = %s,price = %s,description = %s,image = %s,duration = %s,highlight1 = %s,highlight2 = %s,highlight3 = %s
        WHERE id = %s""", (name,destination,price,description,image,duration,highlight1,highlight2,highlight3,package_id))

    mysql.connection.commit()  # Save changes
    cursor.close()  # Close database connection
    return redirect(url_for("admin"))  # Return to Admin Panel


@app.route("/admin/delete/<int:id>")  # Handles deleting a package
def admin_delete(id):
    if "user_id" not in session:  # Check if user is logged in
        return redirect(url_for("login"))  # Go to login page

    user_id = session["user_id"]  # Get logged-in user's ID
    cursor = mysql.connection.cursor()  # Open database connection
    cursor.execute(
        "SELECT is_admin FROM users WHERE id = %s",
        (user_id,)
    )  # Check admin status

    user = cursor.fetchone()  # Get admin information

    if not user or user[0] != 1:  # Check if user is not admin
        cursor.close()  # Close database
        return "Access Denied"  # Block access

    cursor.execute(
        "DELETE FROM packages WHERE id = %s",
        (id,)
    )  # Delete selected package

    mysql.connection.commit()  # Save deletion
    cursor.close()  # Close database connection
    return redirect(url_for("admin"))  # Return to Admin Panel

    
@app.route("/admin/get-package/<int:id>")  # Route to get one package
def get_package(id):
    if "user_id" not in session:  # Check if user is logged in
        return redirect(url_for("login"))  # Send to login if not logged in

    user_id = session["user_id"]  # Get logged-in user ID
    cursor = mysql.connection.cursor()  # Connect to MySQL
    cursor.execute(
        "SELECT is_admin FROM users WHERE id = %s",
        (user_id,)
    )  # Check admin status

    user = cursor.fetchone()  # Get admin information

    if not user or user[0] != 1:  # Check if user is not admin
        cursor.close()  # Close database connection
        return "Access Denied"  # Block access

    cursor.execute(
        "SELECT id, name, destination, price, description, image, duration, highlight1, highlight2, highlight3 FROM packages WHERE id = %s",
        (id,)
    )  # Get selected package

    package = cursor.fetchone()  # Get package data
    cursor.close()  # Close database connection

    if not package:  # Check if package exists
        return {"error": "Package not found"}, 404  # Show error

    return {"id": package[0],  
        "name": package[1],  
        "destination": package[2], 
        "price": str(package[3]), 
        "description": package[4],  
        "image": package[5], 
        "duration": package[6],  
        "highlight1": package[7],  
        "highlight2": package[8],  
        "highlight3": package[9]  
    }


# Handle unexpected server errors
@app.errorhandler(500)
def server_error(error):
    return """
    <h2>Something went wrong.</h2>
    <p>Please try again later.</p>
    <a href="/">Go back to Home</a>
    """, 500

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=False
    )

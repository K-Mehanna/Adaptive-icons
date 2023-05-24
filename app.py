# Libaries to help with the database
import os

# Libraries used 
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

# Functions imported from helpers.py
from helpers import apology

# Configure application
app = Flask(__name__)

# Ensure templates (html webpages) are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Specifies the location to save files
#UPLOAD_FOLDER = r"D:\Desktop\Documents\Programming Project\Test\static\images"
#app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Make sure API key is set
os.environ['API_KEY'] = 'pk_94949beadebd4b6ab617125cc67c82ff'
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/", methods=["GET", "POST"])
def index(): 
    def allowed_file(filename):
        allowedExtensions = {'png', 'jpg', 'jpeg'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowedExtensions
    
    if request.method == "POST":
        # Variable containing the icon
        icon = request.files["icon"]
        if icon.filename == '':
            return apology("must include image")
        elif not allowed_file(icon.filename):
            return apology("must be a png, jpg or jpeg")
        

    return render_template("index.html")

""" @app.route("/icon-submit", methods=["GET", "POST"])
def studentsCSV():
    # Function to check that the file extension is allowed 
    def allowed_file(filename):
        allowedExtensions = {'png', 'jpg', 'jpeg'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowedExtensions
    
    className = session["name"]

    # When the form is submitted
    if request.method == "POST":
        # Inserts the name of the class into the database
        nameID = db.execute("INSERT INTO classNames (name) VALUES (:name)", name = className)
        timesList = session["timesList"]
        student_numbers = session["student_numbers"] 
        teacherID = session["user_id"] 

        # Inserts each specific class instance into the database
        for timeID in timesList:
            db.execute(\"""INSERT INTO classes (teacherID, nameID, numberOfStudents, 
            timeID) VALUES (:ID, :nameID, :number, :timeID)
            \""", ID = teacherID, nameID = nameID, number = student_numbers, timeID = timeID)

        i=0
        # Variable containing a list of the names of the images
        images = request.files.getlist('images')
        # Variable containing the CSV file
        names = request.files["names"]
        if names.filename == '':
            return apology("must include CSV")
        # CSV file is saved into the correct directory
        names.save(os.path.join(os.getcwd(), names.filename))

        # Iterates through each line in the CSV
        with open(names.filename, 'r') as namesfile:
            reader = csv.reader(namesfile)
            for row in reader:
                # Extracts student's first and last names
                forename = row[0].title()
                surname = row[1].title()
                combinedName = ' '.join(row)
                image = images[i]
                name = image.filename
                if name == '':
                    return apology("Please upload photos")
                extension = os.path.splitext(name)[1]
                combinedFileName = combinedName.title() + extension

                # Saves image as student_name.extension
                if image and allowed_file(name):
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], combinedFileName))

                # Tests if the student is already in the database
                duplicateTest = db.execute(\"""SELECT studentID FROM students WHERE forename
                 = :forename AND surname = :surname\""", forename = forename, surname = surname)
                if len(duplicateTest) == 0:
                    studentID = db.execute(\"""INSERT INTO students (forename, surname) VALUES 
                    (:forename, :surname)\""", forename = forename, surname = surname)
                else:
                    studentID = duplicateTest[0]["studentID"]

                nameDict = db.execute("SELECT nameID FROM classNames WHERE name = :name", name = className)
                nameID = nameDict[0]["nameID"]

                classIDs = db.execute(\"""SELECT classID FROM classes LEFT JOIN classNames on classes.nameID = 
                classNames.nameID WHERE teacherID = :ID AND name = :name\""", ID = session["user_id"], name = className)
                for item in classIDs:
                    classID = item["classID"]
                    # Adds student to classToStudent table which maps a student to a class
                    insert = db.execute(\"""INSERT INTO classToStudent (classID, studentID)
                     VALUES (:classID, :studentID)\""", classID = classID, studentID = studentID)
                i += 1

        flash("Class added!")
        return redirect("/")
    else:
        return render_template("students-csv.html") """
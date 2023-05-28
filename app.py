# Libaries to help with the database
import os
import numpy as np
import cv2
from matplotlib import pyplot as plt
from PIL import ImageFilter, ImageEnhance, Image as im
import math

# Libraries used 
from flask import Flask, flash, redirect, render_template, request, session, send_from_directory, current_app, send_file
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

# Specifies the location to save files
UPLOAD_FOLDER = "static_images"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Make sure API key is set
os.environ['API_KEY'] = 'pk_94949beadebd4b6ab617125cc67c82ff'
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        inputType = request.form["action"]
        if inputType == "background":
            return redirect("/background")
        elif inputType == "foreground":
            return redirect("/foreground")
        else:
            return redirect("/")
    else:
        return render_template("new_index.html")

@app.route("/background", methods=["GET", "POST"])
def background():
    if request.method == "POST":
        # Variable containing the icon
        icon = request.files["icon"]
        if icon.filename == '':
            return apology("must include image")
        elif not allowed_file(icon.filename):
            return apology("must be a png, jpg or jpeg")
        mask, img, h, w, name, bgdModel, fgdModel = admin(icon)

        mask2 = np.where((mask==2)|(mask==0),0,1).astype('uint8')
        foreground = img*mask2[:,:,np.newaxis]
        
        # Applying the Canny Edge filter
        edge = cv2.Canny(img, 0, 300) # type: ignore

        cv2.imwrite(os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], "edge.png"), edge)

        # threshold
        thresh = cv2.threshold(edge, 128, 255, cv2.THRESH_BINARY)[1]

        # get the (largest) contour
        contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours[0] if len(contours) == 2 else contours[1]
        big_contour = max(contours, key=cv2.contourArea)

        # draw white filled contour on black background
        result = np.full_like(img, [40,40,40])
        cv2.drawContours(result, [big_contour], 0, (255,255,255), cv2.FILLED)
        cv2.imwrite(os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], "contour.png"), result)

        # whereever it is marked white (sure foreground), change mask=1
        # whereever it is marked black (sure background), change mask=0
        mask[np.array_equal(result, np.zeros(3))] = 0
        mask[np.array_equal(result, [255,255,255])] = 1
        
        cv2.grabCut(img,mask,None,bgdModel,fgdModel,5,cv2.GC_INIT_WITH_MASK) 
        
        bColour = str(request.form.get("bColour"))
        bColourArray = np.array([int(bColour[1:3], 16), int(bColour[3:5], 16), int(bColour[5:7], 16)])

        mask2 = np.where((mask==2)|(mask==0),0,1).astype('uint8')
        foreground = img*mask2[:,:,np.newaxis]

        mask3 = np.where((mask==2)|(mask==0),1,0).astype('uint8')
        background = img*mask3[:,:,np.newaxis]

        for i in range(h):
            for j in range(w):
                if not np.array_equal(background[i][j], np.zeros(3)):
                    background[i][j] = bColourArray

        data = im.fromarray(foreground)
        data.save(os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], "foreground.png"))
        data = im.fromarray(background)
        data.save(os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], "background.png"))
        combinedImage = np.add(foreground, background)

        data = im.fromarray(combinedImage)
        data.save(os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], "combined.png"))

        uploads = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'])
        prefix = name.rsplit('.', 1)[0]
        suffix = name.rsplit('.', 1)[1]
        # Returning file from appended path
        return send_from_directory(directory=uploads, path="combined.png", as_attachment=True, download_name = prefix + "_themed." + suffix)

        flash("Icon saved")
        return redirect("/")

    else:
        return render_template("background.html")


@app.route("/foreground", methods=["GET", "POST"])
def foreground():
    if request.method == "POST":
        # Variable containing the icon
        icon = request.files["icon"]
        if icon.filename == '':
            return apology("must include image")
        elif not allowed_file(icon.filename):
            return apology("must be a png, jpg or jpeg")
        
        mask, img, h, w, name, bgdModel, fgdModel = admin(icon)

        bColour = str(request.form.get("bColour"))
        bColourArray = np.array([int(bColour[1:3], 16), int(bColour[3:5], 16), int(bColour[5:7], 16)])
        fColour = str(request.form.get("fColour"))
        fColourArray = np.array([int(fColour[1:3], 16), int(fColour[3:5], 16), int(fColour[5:7], 16)])

        mask2 = np.where((mask==2)|(mask==0),0,1).astype('uint8')
        foreground = img*mask2[:,:,np.newaxis]

        mask3 = np.where((mask==2)|(mask==0),1,0).astype('uint8')
        background = img*mask3[:,:,np.newaxis]

        for i in range(h):
            for j in range(w):
                if not np.array_equal(background[i][j], np.zeros(3)):
                    background[i][j] = bColourArray
                if not np.array_equal(foreground[i][j], np.zeros(3)):
                    foreground[i][j] = fColourArray

        data = im.fromarray(foreground)
        data.save(os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], "foreground.png"))
        data = im.fromarray(background)
        data.save(os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], "background.png"))
        combinedImage = np.add(foreground, background)
        data = im.fromarray(combinedImage)
        data.save(os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], "combined.png"))

        uploads = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'])
        prefix = name.rsplit('.', 1)[0]
        suffix = name.rsplit('.', 1)[1]
        # Returning file from appended path
        return send_from_directory(directory=uploads, path="combined.png", as_attachment=True, download_name = prefix + "_themed." + suffix)

        flash("Icon saved")
        return redirect("/")

    return render_template("foreground.html")



def allowed_file(filename):
        allowedExtensions = {'png', 'jpg', 'jpeg'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowedExtensions

def admin(icon):
    name = str(icon.filename)
    icon.save(os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], name))
    img = cv2.imread(os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], name))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mask = np.zeros(img.shape[:2],np.uint8)

    bgdModel = np.zeros((1,65),np.float64)
    fgdModel = np.zeros((1,65),np.float64)
    # Gets dimensions of image
    h, w, c = img.shape

    image = im.open(os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], name))
    image = image.convert('RGB').filter(ImageFilter.FIND_EDGES)
    imageArray = np.array(image)
    top = h
    bottom = -1
    left = w
    right = -1
    for i in range(3, h - 2):
        for j in range(3, w - 2):
            if np.sum(imageArray[i][j]) > 200:
                if i < top:
                    top = i
                if i > bottom:
                    bottom = i
                if j < left:
                    left = j
                if j > right:
                    right = j
    top = max(1, top - 3)
    left = max(1, left - 3)
    bottom = min(h - 1, bottom + 3)
    right = min(w - 1, right + 3)
    # Visual for the inclusion rectangle
    for i in range(1, h):
        for j in range(1, w):
            if (((top) == i or i == bottom) and ((left) <= j and j <= right)) or (((left) == j or right == j) and ((top) <= i and i <= bottom)):
                imageArray[i][j] = np.array([255, 0, 0]) 
    imageArray[(top)][left] = np.array([0, 0, 255])
    imageArray[(bottom)][right] = np.array([0, 255, 0])
    im.fromarray(imageArray).save(os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], "edges.png"))
    rect = (left, top, (right - left), (bottom - top))
    mask, bgdModel, fgdModel = cv2.grabCut(img,mask,rect,bgdModel,fgdModel,10,cv2.GC_INIT_WITH_RECT)
    return mask, img, h, w, name, bgdModel, fgdModel
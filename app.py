from flask import Flask
from pymongo import MongoClient
from flask import render_template, request, redirect
from flask import session
import math
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

client = MongoClient(os.getenv("MONGO_URI"))
db = client["contact_book"]

users_collection = db["users"]
contacts_collection = db["contacts"]


# Home route
@app.route("/")
def home():
    if "username" in session:
        return redirect("/dashboard")
    else:
        return redirect("/login")



@app.route("/test", methods=["GET"])
def test():
    return "TEST ROUTE WORKING"


# Register route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        users_collection.insert_one({
            "username" : username,
            "password" : password
        })

        return redirect("/login")
    
    return render_template("register.html")

#Login Route
@app.route("/login",methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = users_collection.find_one({
            "username" : username,
            "password" : password

        })

        if user:
            session["username"] = username
            return redirect("/dashboard")

        else:
            return "Invalid Credentials"
    

    return render_template("login.html")

#dashboard route

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/login")
    
    return render_template("dashboard.html")


@app.route("/contact")
def contact():

    if "username" not in session:
        return redirect("/login")

    search = request.args.get("search", "")
    page =  int(request.args.get("page",1))
    limit = 5
    skip = (page - 1) * limit
    query = {"user": session["username"]}

    if search:
        query["$or"] = [
            {"name": {"$regex":search, "$options":"i"}},
            {"email": {"$regex":search, "$options":"i"}},
            {"phone": {"$regex":search, "$options":"i"}}
        ]

    total_contacts  = contacts_collection.count_documents(query)

    contacts = list(contacts_collection.find(query).skip(skip).limit(limit))

    total_pages = math.ceil(total_contacts/limit)

    return render_template("contact.html", 
                           contacts=contacts,
                           search=search,
                           page=page,
                           total_pages=total_pages
                        )
    

@app.route("/add-contact", methods=["GET","POST"])
def add_contact():
    if "username" not in session:
        return redirect("/login")
    
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        email = request.form["email"]

        contacts_collection.insert_one({
            "user" : session["username"],
            "name" : name,
            "email" : email,
            "phone": phone
        })

        return redirect("/contact")
    
    return render_template("add_contact.html")


@app.route("/delete/<id>")
def delete_contact(id):
    if "username" not in session:
        return redirect("/login")
     
    contacts_collection.delete_one({
        "_id": ObjectId(id),
        "user": session["username"]
    })
    return redirect("/dashboard")

@app.route("/edit/<id>",methods=["GET","POST"])
def editMethod(id):
    if "username" not in session:
        return redirect("/login")
    

    contact = contacts_collection.find_one({
        "_id" : ObjectId(id),
        "user" :  session["username"]
    })

    if not contact:
        return redirect("/dashboard")
    
    if request.method == "POST":
        contacts_collection.update_one(
            { "_id" : ObjectId(id) },
            {
                "$set" :{
                    "name" : request.form["name"],
                    "email" : request.form["email"],
                    "phone" : request.form["phone"]
                }
            }
        )
        return redirect("/dashboard")

    return render_template("edit_contact.html", contact=contact)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True, port=8000)
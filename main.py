import random
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# #Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def find_cafe(coffe_id):
    """return true if the cafe id matches the one in the database else return false"""
    cafes = Cafe.query.all()
    for cafe_id in cafes:
        if coffe_id == cafe_id.id:
            return True
    else:
        return False

# # Café TABLE Configuration
class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)

    def to_dict(self):
        # Alternatively, use Dictionary Comprehension to do the same thing.
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


@app.route("/")
def home():
    return render_template("index.html")


# ## HTTP GET - Read Record

@app.route('/random',methods=['GET'])
def get_random_cafe():
    random_coffe_number =random.randint(1,21)
    cafe = Cafe.query.filter_by(id=random_coffe_number).first()
    return jsonify(cafe.to_dict())


@app.route('/all',methods=['GET'])
def get_all_cafe():
    cafes = Cafe.query.all()
    cafe_data={'cafes': [cafe.to_dict() for cafe in cafes]}
    return jsonify(cafe_data)

@app.route("/search",methods=['GET'])
def find_a_cafe():
    """ used to search through the database to find the entered element in args """
    query_location = request.args.get("loc")
    # get all the cafés that have the same location
    cafes = Cafe.query.filter_by(location=query_location).all()
    if cafes:
        return jsonify(cafes=[cafe.to_dict() for cafe in cafes])
    else:
        return jsonify(error={"Not Found": "Sorry, we don't have a cafe at that location."})


# HTTP POST - Create Record
@app.route("/add",methods=['POST'])
def add_cafe():
    """getting the data through the link and make a new record using args keyword"""
    new_cafe = Cafe(
        name=request.args.get("name"),
        map_url=request.args.get("map_url"),
        img_url=request.args.get("img_url"),
        location=request.args.get("loc"),
        has_sockets=bool(request.args.get("sockets")),
        has_toilet=bool(request.args.get("toilet")),
        has_wifi=bool(request.args.get("wifi")),
        can_take_calls=bool(request.args.get("calls")),
        seats=request.args.get("seats"),
        coffee_price=request.args.get("coffee_price"),
    )
    with app.app_context():
        db.session.add(new_cafe)
        db.session.commit()
    return jsonify(response={"success": "Successfully added the new cafe."})

# HTTP PUT/PATCH - Update Record
@app.route('/update-price/<int:coffe_id>',methods=['GET','PATCH'])
def update_cafe_data(coffe_id):
    # if the id matches the one in the database
    cafe = Cafe.query.filter_by(id=coffe_id).first()
    # get all the cafés in the database and check the given id with the id form database
    if find_cafe(coffe_id):
        if request.method == 'PATCH':
            new_price = request.args.get("new_price")
            cafe.coffee_price = str(f'${new_price}')
            db.session.commit()
            return jsonify(success={"Successfully": "Price updated successfully"})
    else:
        return jsonify(error={"Not Found": "Sorry, we don't have a cafe at that id."}),404


# HTTP DELETE - Delete Record
@app.route("/report_closed/<int:cafe_id>",methods=['DELETE'])
def delete_a_cafe(cafe_id):
    # get all the cafés in the database and check the given id with the id form database
    api_key=str(request.args.get('api_key'))
    cafe = Cafe.query.filter_by(id=cafe_id).first()
    if find_cafe(cafe_id):
        if request.method =='DELETE' and api_key=="TopSecretAPIKey":
            db.session.delete(cafe)
            db.session.commit()
            return jsonify(success={"Successfully": "Cafe was deleted successfully"})
    else:
        return jsonify(Failer={"Not Found": "Sorry, we don't have a cafe at that id."}), 404


if __name__ == '__main__':
    app.run(debug=True)

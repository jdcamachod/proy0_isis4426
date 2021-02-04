from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_user, login_required, current_user, logout_user
from flask_restful import Api, Resource
from flask_marshmallow import Marshmallow

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SECRET_KEY'] = 'secret-key-goes-here'
db = SQLAlchemy(app)
ma = Marshmallow(app)
api = Api(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)
CATEGORIES = ["Conferencia", "Seminario", "Congreso", "Curso"]
class Event_Schema(ma.Schema):
    class Meta:
        fields = ("id", "name", "category", "place", "address", "start_date",
                  "end_date", "type", "created_at", "owner_id")
class User_Schema(ma.Schema):
    class Meta:
        fields = ("id", "email", "password", "name", "api_key")
user_schema = User_Schema()
event_schema = Event_Schema()
events_schema = Event_Schema(many=True)

class ResourceEvents(Resource):
    @login_required
    def get(self):
        events = Event.query.filter_by(
            owner_id=current_user.id).order_by(desc(Event.created_at)).all()
        return events_schema.dump(events)
api.add_resource(ResourceEvents, '/api/events')

class ResourceCreateEvent(Resource):
    @login_required
    def post(self):
        start_date = request.json['start_date']
        end_date = request.json['end_date']
        start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
        end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
        new_event = Event(name=request.json['name'], category=request.json['category'],
                          place=request.json['place'], address=request.json['address'],
                          start_date=start_date, end_date=end_date,
                          type=request.json['type'], owner_id=current_user.id)
        db.session.add(new_event)
        db.session.commit()
        return event_schema.dump(new_event)

api.add_resource(ResourceCreateEvent, '/api/events/create')

class ResourceEvent(Resource):
    @login_required
    def get(self, id):
        event = Event.query.get_or_404(id)
        if current_user.id == event.owner_id:
            return event_schema.dump(event)
        else:
            return '', 401
    @login_required
    def put(self, id):
        event = Event.query.get_or_404(id)
        if current_user.id == event.owner_id:
            if 'name' in request.json:
                event.name = request.json['name']
            if 'category' in request.json:
                event.category = request.json['category']
            if 'place' in request.json:
                event.place = request.json['place']
            if 'address' in request.json:
                event.address = request.json['address']
            if 'start_date' in request.json:
                event.start_date = request.json['start_date']
            if 'end_date' in request.json:
                event.end_date = request.json['end_date']
            if 'type' in request.json:
                event.type = request.json['type']
            db.session.commit()
            return event_schema.dump(event)
        else:
            return '', 401


    @login_required
    def delete(self, id):
        event = Event.query.get_or_404(id)
        if event.owner_id == current_user.id:
            db.session.delete(event)
            db.session.commit()
            return '', 204
        else:
            return '', 401



api.add_resource(ResourceEvent, '/api/events/<int:id>')

class ResourceLogin(Resource):
    def post(self):
        email = request.json['email']
        password = request.json['password']
        user = User.query.filter_by(email=email).first()
        print(email)
        if not user or not check_password_hash(user.password, password):
            return ''
        login_user(user)
        return user_schema.dump(user)

api.add_resource(ResourceLogin, '/api/login')

class ResourceLogout(Resource):
    def get(self):
        logout_user()
        return '', 200
api.add_resource(ResourceLogout, '/api/logout')

class ResourceSignUp(Resource):
    def post(self):
        email = request.json['email']
        name = request.json['name']
        password = request.json['password']

        user = User.query.filter_by(email=email).first()
        if user:
            return {"error": "Usuario registrado"}
        new_user = User(email=email, name=name, password=generate_password_hash(
            password, method='sha256'))
        db.session.add(new_user)
        db.session.commit()
        return user_schema.dump(new_user)

api.add_resource(ResourceSignUp, '/api/signup')




@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    category = db.Column(db.String(80))
    place = db.Column(db.String(255))
    address = db.Column(db.String(255))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    type = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    owner_id = db.Column(
        db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Event %r>' % self.name



class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(200))
    events = db.relationship('Event', backref='event_owner')

    def __repr__(self):
        return '<User %r>' % self.name



@app.route('/events/')
@login_required
def index():
    events = Event.query.filter_by(
        owner_id=current_user.id).order_by(desc(Event.created_at)).all()
    return render_template('index.html', events=events)


@app.route('/events/create/', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        place = request.form['place']
        address = request.form['address']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        type = request.form['type']
        if type == "True":
            type = True
        else:
            type = False
        start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
        end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
        if len(name) < 1:
            flash("Ingrese un nombre")
            date = datetime.now().strftime('%Y-%m-%dT%H:%M')
            return render_template('create.html', categories=CATEGORIES, date=date)
        new_event = Event(name=name, category=category, place=place,
                          address=address, start_date=start_date, end_date=end_date, type=type, owner_id=current_user.id)

        try:
            db.session.add(new_event)
            db.session.commit()
            return redirect('/events/')
        except:
            return "Hubo un problema agregando el nuevo evento"
    else:
        date = datetime.now().strftime('%Y-%m-%dT%H:%M')
        return render_template('create.html', categories=CATEGORIES, date=date)


@app.route('/events/<int:id>/delete/')
@login_required
def delete(id):
    event = Event.query.get_or_404(id)
    if event.owner_id == current_user.id:
        try:
            db.session.delete(event)
            db.session.commit()
            return redirect('/events/')
        except:
            return "Hubo un problema al borrar el evento"
    else:
        return render_template('unauthorized.html')


@app.route('/events/<int:id>/update/', methods=['GET', 'POST'])
@login_required
def update(id):
    event = Event.query.get_or_404(id)
    if event.owner_id == current_user.id:
        if request.method == 'POST':
            event.name = request.form['name']
            event.category = request.form['category']
            event.place = request.form['place']
            event.address = request.form['address']
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            type = request.form['type']
            if type == "True":
                event.type = True
            else:
                event.type = False
            event.start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
            event.end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
            if len(event.name) < 1:
                flash("Ingrese un nombre")
                return render_template('update.html', event=event, start_date=start_date, end_date=end_date)
            try:
                db.session.commit()
                return redirect('/events/')
            except:
                return "Hubo un problema actualizando el evento."
        else:
            start_date = event.start_date.strftime('%Y-%m-%dT%H:%M')
            end_date = event.end_date.strftime('%Y-%m-%dT%H:%M')
            return render_template('update.html', event=event, start_date=start_date, end_date=end_date)
    else:
        return render_template('unauthorized.html')


@app.route('/events/<int:id>/')
@login_required
def eventDetail(id):
    event = Event.query.get_or_404(id)
    if event.owner_id == current_user.id:
        return render_template('eventDetail.html', event=event)
    else:
        return render_template('unauthorized.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash('Verifique sus credenciales')
            return redirect('/login/')
        login_user(user, remember=remember)
        return redirect('/events/')
    return render_template('login.html')




@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email ya registrado')
            return redirect('/signup/')
        new_user = User(email=email, name=name, password=generate_password_hash(
            password, method='sha256'))
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login/')
    return render_template('signup.html')


@app.route('/logout/')
def logout():
    logout_user()
    return redirect('/')


@app.route('/')
def main():
    if current_user.is_authenticated:
        return redirect('/events/')
    else:
        return redirect('/login/')


if __name__ == '__main__':
    app.run(debug=True)

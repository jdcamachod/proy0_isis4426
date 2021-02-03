from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_user, login_required, current_user, logout_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SECRET_KEY'] = 'secret-key-goes-here'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)
CATEGORIES = ["Conferencia", "Seminario", "Congreso", "Curso"]


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
        owner_id=current_user.id).order_by(Event.created_at).all()
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

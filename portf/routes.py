from portf import app, db
from flask import render_template, session, request, jsonify, redirect
from portf.models import Actives


@app.route('/')
def main():
    return render_template('index.html')


@app.route('/actives', methods=('POST', 'GET'))
def actives():
    if request.method == 'POST':
        print(request.form)
        if 'id' in request.form:
            if not request.form.get('id'):
                error = "Enter active's id"
            else:
                active_id = request.form.get('id')
                active = Actives.query.filter_by(id=active_id).first()
                if not active:
                    error = 'Active with id {} is not exists'.format(active_id)
                else:
                    db.session.delete(active)
                    db.session.commit()
        else:
            active_name = request.form.get('active_name')
            ticket = request.form.get('ticket')
            if not active_name or not ticket:
                error = "Enter active's name and ticket"
            elif Actives.query.filter_by(name=active_name).first():
                error = 'Active with name {} already exists'.format(active_name)
            elif Actives.query.filter_by(ticket=ticket).first():
                error = 'Active with ticket {} already exists'.format(ticket)
            else:
                active = Actives(name=active_name, ticket=ticket)
                db.session.add(active)
                db.session.commit()
    actives = Actives.query.filter(Actives.count != 0)
    all_actives = Actives.query.all()
    if 'error' not in locals():
        error = None
    return render_template('actives.html', actives=actives, all_actives=all_actives, error=error)


@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/form_buy', methods=['GET', 'POST'])
def form_buy():
    name = request.form('active_name').get()
    count = request.form('count').get()
    price = request.form('price').get()
    if not name:
        error = "Enter the active's name"
    elif not count:
        error = "Enter the count"
    elif not price:
        error = "Enter the price"
    else:
        active = Actives.query.filter_by(name=name)
        if not active:
            error = "Active with name {} is not exist"
        else:
            active.count = count
            active.price = price
            db.session.add(active)
            db.session.commit()
    if 'error' not in locals():
        error = None
    return render_template('index.html', error=error)



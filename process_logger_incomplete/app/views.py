from flask import Blueprint, render_template, redirect
from .models import db, ProcessLog, User, Subject, Instrument, Process
from .forms import LogForm
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('home.html')

@main.route('/log', methods=['GET', 'POST'])
def log_process():
    form = LogForm()
    form.user.choices = [(u.id, u.name) for u in User.query.all()]
    form.subject.choices = [(s.id, s.name) for s in Subject.query.all()]
    form.process.choices = [(p.id, p.name) for p in Process.query.all()]
    form.instrument.choices = [(i.id, i.name) for i in Instrument.query.all()]

    if form.validate_on_submit():
        log = ProcessLog(
            user_id=form.user.data,
            subject_id=form.subject.data,
            process_id=form.process.data,
            instrument_id=form.instrument.data,
            timestamp=datetime.now()
        )
        db.session.add(log)
        db.session.commit()
        return redirect('/')
    
    return render_template('log.html', form=form)

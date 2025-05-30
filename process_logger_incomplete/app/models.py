from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Instrument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    can_perform_all = db.Column(db.Boolean, default=False)
    processes = db.relationship('Process', secondary='instrument_process', back_populates='instruments')

class Process(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    instruments = db.relationship('Instrument', secondary='instrument_process', back_populates='processes')

class InstrumentProcess(db.Model):
    __tablename__ = 'instrument_process'
    instrument_id = db.Column(db.Integer, db.ForeignKey('instrument.id'), primary_key=True)
    process_id = db.Column(db.Integer, db.ForeignKey('process.id'), primary_key=True)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, default='Unknown')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, default='Anonymous')

class ProcessLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    process_id = db.Column(db.Integer, db.ForeignKey('process.id'))
    instrument_id = db.Column(db.Integer, db.ForeignKey('instrument.id'))
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class WeeklyPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    week_start = db.Column(db.Date)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    process_id = db.Column(db.Integer, db.ForeignKey('process.id'))
    instrument_id = db.Column(db.Integer, db.ForeignKey('instrument.id'))
    scheduled_time = db.Column(db.DateTime)
    status = db.Column(db.String, default='scheduled')

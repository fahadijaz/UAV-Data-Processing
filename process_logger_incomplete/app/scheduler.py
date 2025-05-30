from .models import db, WeeklyPlan, Subject, Process, Instrument
from datetime import date, datetime, timedelta
import random

def generate_weekly_schedule():
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    subjects = Subject.query.all()
    processes = Process.query.all()
    instruments = Instrument.query.all()

    for subject in subjects:
        for process in processes:
            compatible = [i for i in instruments if i.can_perform_all or process in i.processes]
            if not compatible:
                continue

            plan = WeeklyPlan(
                week_start=week_start,
                subject_id=subject.id,
                process_id=process.id,
                instrument_id=random.choice(compatible).id,
                scheduled_time=datetime.combine(week_start + timedelta(days=random.randint(0, 6)), datetime.min.time()),
                status='scheduled'
            )
            db.session.add(plan)

    db.session.commit()

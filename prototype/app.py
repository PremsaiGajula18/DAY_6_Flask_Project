from flask import Flask, render_template, request, redirect, url_for, abort

app = Flask(__name__)

# In-memory list storing events
events = [
    {
        "id": 1,
        "title": "Python & Flask Workshop",
        "venue": "MITRAz Training Centre",
        "date": "2026-10-05",
        "capacity": 20,
        "booked": 8
    },
    {
        "id": 2,
        "title": "Community Clean-up Drive",
        "venue": "Town Hall",
        "date": "2026-10-12",
        "capacity": 15,
        "booked": 15
    }
]

# Helper to find an event by ID
def get_event(event_id):
    for e in events:
        if e["id"] == event_id:
            return e
    abort(404)


# 1. PAGE 1: Home (List all events)
@app.route('/')
def home():
    return render_template('index.html', event_list=events)


# 2. PAGE 2: Post New Event
@app.route('/new', methods=['GET', 'POST'])
def create_event():
    if request.method == 'POST':
        new_event = {

            "id": len(events) + 1,
            "title": request.form.get('title'),
            "venue": request.form.get('venue'),
            "date": request.form.get('date'),
            "capacity": int(request.form.get('capacity', 1)),
            "booked": 0
         
        }
        events.append(new_event)
        return redirect(url_for('home'))
    
    return render_template('create.html')
    

# 3. PAGE 3: Event Details & View
@app.route('/event/<int:event_id>')
def event_details(event_id):
    event = get_event(event_id)
    return render_template('event.html', event=event)


# 4. ACTION: Register for Event (POST from PAGE 3)
@app.route('/event/<int:event_id>/register', methods=['POST'])
def register_event(event_id):
    event = get_event(event_id)
    seats = int(request.form.get('seats', 1))
    
    # Check if capacity allows
    if event['booked'] + seats <= event['capacity']:
        event['booked'] += seats

    return redirect(url_for('event_details', event_id=event_id))


if __name__ == '__main__':
    app.run(debug=True, port=5000)

import os
from datetime import date
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from flask import Flask, render_template, request, redirect, url_for, flash, abort

# Load environmental variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "test-key-community-events")

# Database Configuration from Environmental Variables
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "community_events")


def get_db_connection():
    """Create and return a MySQL connection using environmental variables."""
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


def init_db():
    """Initialize database and tables if they do not exist, and seed initial data."""
    try:
        # Step 1: Connect to MySQL server without database to ensure DB exists
        server_conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD
        )
        server_cursor = server_conn.cursor()
        server_cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
        server_cursor.close()
        server_conn.close()

        # Step 2: Connect to the specific database and create tables
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                category VARCHAR(100) NOT NULL,
                date VARCHAR(50) NOT NULL,
                time VARCHAR(50) NOT NULL,
                venue VARCHAR(255) NOT NULL,
                capacity INT NOT NULL DEFAULT 0,
                booked_seats INT NOT NULL DEFAULT 0,
                email VARCHAR(255) NOT NULL,
                deadline VARCHAR(50) NOT NULL,
                description TEXT NOT NULL,
                cover_class VARCHAR(100) DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create registrations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                event_id INT NOT NULL,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                phone VARCHAR(50) NOT NULL,
                seats INT NOT NULL DEFAULT 1,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            )
        """)

        # Seed sample event if events table is empty
        cursor.execute("SELECT COUNT(*) FROM events")
        (count,) = cursor.fetchone()
        if count == 0:
            cursor.execute("""
                INSERT INTO events (title, category, date, time, venue, capacity, booked_seats, email, deadline, description, cover_class)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                "Digital Skills Saturday",
                "Workshop",
                "2026-10-05",
                "10:00",
                "MITRAz Training Centre",
                30,
                12,
                "organizer@example.com",
                "2026-10-04",
                "A practical introduction to everyday digital skills for local learners.",
                ""
            ))
            conn.commit()

        cursor.close()
        conn.close()
        print(f" Database '{DB_NAME}' initialized successfully.")
    except Error as e:
        print(f" MySQL Connection Warning: {e}")
        print("Please check that MySQL service is running and credentials in .env are correct.")


# Helper function to find an event from MySQL by ID
def get_event(event_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
    event = cursor.fetchone()
    cursor.close()
    conn.close()

    if not event:
        abort(404)
    return event


# --- Routes using MySQL Database ---

@app.route('/')
def index():
    search_query = request.args.get('search', '').strip()
    selected_category = request.args.get('category', '').strip()
    upcoming_only = request.args.get('upcoming') == '1'

    query = "SELECT * FROM events WHERE 1=1"
    params = []

    if search_query:
        query += " AND (title LIKE %s OR venue LIKE %s)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])

    if selected_category:
        query += " AND category = %s"
        params.append(selected_category)

    if upcoming_only:
        today_str = date.today().isoformat()
        query += " AND date >= %s"
        params.append(today_str)

    query += " ORDER BY date ASC, time ASC"

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, tuple(params))
        events = cursor.fetchall()
        cursor.close()
        conn.close()
    except Error as e:
        flash(f"Database error: {e}. Please ensure MySQL is running.", "error")
        events = []

    return render_template(
        'index.html',
        events=events,
        search_query=search_query,
        selected_category=selected_category,
        upcoming_only=upcoming_only
    )


@app.route('/events/new', methods=['GET', 'POST'])
def create_event():
    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        event_date = request.form.get('date')
        time = request.form.get('time')
        venue = request.form.get('venue')
        capacity = int(request.form.get('capacity', 0))
        email = request.form.get('email')
        deadline = request.form.get('deadline')
        description = request.form.get('description')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO events (title, category, date, time, venue, capacity, booked_seats, email, deadline, description, cover_class)
                VALUES (%s, %s, %s, %s, %s, %s, 0, %s, %s, %s, '')
            """, (title, category, event_date, time, venue, capacity, email, deadline, description))
            conn.commit()
            cursor.close()
            conn.close()

            flash("Event published successfully!", "success")
            return redirect(url_for('index'))
        except Error as e:
            flash(f"Failed to publish event: {e}", "error")

    return render_template('create_event.html')


@app.route('/events/<int:event_id>')
def event_details(event_id):
    try:
        event = get_event(event_id)
        return render_template('event_details.html', event=event)
    except Error as e:
        flash(f"Database error: {e}", "error")
        return redirect(url_for('index'))


@app.route('/events/<int:event_id>/register', methods=['GET', 'POST'])
def register_event(event_id):
    try:
        event = get_event(event_id)
    except Error as e:
        flash(f"Database error: {e}", "error")
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        seats = int(request.form.get('seats', 1))
        available = event['capacity'] - event['booked_seats']

        if seats <= available:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                # Update booked seats count in events table
                cursor.execute("""
                    UPDATE events SET booked_seats = booked_seats + %s WHERE id = %s
                """, (seats, event_id))

                # Insert registration record
                cursor.execute("""
                    INSERT INTO registrations (event_id, name, email, phone, seats)
                    VALUES (%s, %s, %s, %s, %s)
                """, (event_id, name, email, phone, seats))

                conn.commit()
                cursor.close()
                conn.close()

                flash(f"Successfully registered {seats} seat(s)!", "success")
                return redirect(url_for('event_details', event_id=event_id))
            except Error as e:
                flash(f"Registration failed: {e}", "error")
        else:
            flash("Sorry, not enough seats available.", "error")

    return render_template('register.html', event=event)


@app.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
def edit_event(event_id):
    try:
        event = get_event(event_id)
    except Error as e:
        flash(f"Database error: {e}", "error")
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        event_date = request.form.get('date')
        time = request.form.get('time')
        venue = request.form.get('venue')
        capacity = int(request.form.get('capacity', event['capacity']))
        email = request.form.get('email')
        deadline = request.form.get('deadline')
        description = request.form.get('description')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE events SET
                    title = %s,
                    category = %s,
                    date = %s,
                    time = %s,
                    venue = %s,
                    capacity = %s,
                    email = %s,
                    deadline = %s,
                    description = %s
                WHERE id = %s
            """, (title, category, event_date, time, venue, capacity, email, deadline, description, event_id))
            conn.commit()
            cursor.close()
            conn.close()

            flash("Event updated successfully!", "success")
            return redirect(url_for('event_details', event_id=event_id))
        except Error as e:
            flash(f"Failed to update event: {e}", "error")

    return render_template('edit_event.html', event=event)


@app.route('/events/<int:event_id>/delete', methods=['POST'])
def delete_event(event_id):
    try:
        event = get_event(event_id)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
        conn.commit()
        cursor.close()
        conn.close()

        flash(f"Event '{event['title']}' deleted successfully!", "success")
    except Error as e:
        flash(f"Failed to delete event: {e}", "error")

    return redirect(url_for('index'))


if __name__ == '__main__':
    # Initialize database and tables on startup
    init_db()
    app.run(debug=True)
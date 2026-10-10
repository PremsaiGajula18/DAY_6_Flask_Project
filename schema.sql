-- Database Schema for Community Events Manager

CREATE DATABASE IF NOT EXISTS community_events;
USE community_events;

-- Events Table
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
);

-- Registrations Table
CREATE TABLE IF NOT EXISTS registrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    seats INT NOT NULL DEFAULT 1,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

-- Initial Seed Data
INSERT INTO events (title, category, date, time, venue, capacity, booked_seats, email, deadline, description, cover_class)
SELECT 
    'Digital Skills Saturday',
    'Workshop',
    '2026-10-05',
    '10:00',
    'MITRAz Training Centre',
    30,
    12,
    'organizer@example.com',
    '2026-10-04',
    'A practical introduction to everyday digital skills for local learners.',
    ''
WHERE NOT EXISTS (SELECT 1 FROM events WHERE id = 1);

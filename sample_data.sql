-- Insert sample candidates
INSERT INTO candidates (name, email, phone, experience_years, skills, current_role)
VALUES
('Alice Johnson', 'alice.johnson@example.com', '555-1234', 5, 'Python, Django, SQL', 'Software Developer'),
('Bob Smith', 'bob.smith@example.com', '555-5678', 3, 'JavaScript, React, Node.js', 'Frontend Developer'),
('Charlie Brown', 'charlie.brown@example.com', '555-8765', 7, 'Java, Spring, Microservices', 'Backend Engineer'),
('Diana Prince', 'diana.prince@example.com', '555-4321', 10, 'Project Management, Agile, Scrum', 'Project Manager');

-- Insert sample jobs
INSERT INTO jobs (title, description, requirements, location, salary_range, is_active)
VALUES
('Software Engineer',
 'Develop and maintain software applications in a dynamic team environment.',
 'Proficiency in Python and Django. Experience with SQL is a plus.',
 'New York, NY',
 '$90,000 - $120,000',
 1),
('Frontend Developer',
 'Design and implement user interfaces for web applications.',
 'Experience with React and JavaScript frameworks.',
 'San Francisco, CA',
 '$80,000 - $110,000',
 1),
('Backend Engineer',
 'Build and optimize server-side applications and databases.',
 'Proficiency in Java and experience with Spring framework.',
 'Seattle, WA',
 '$100,000 - $130,000',
 1),
('Project Manager',
 'Oversee software development projects, manage teams, and ensure timely delivery.',
 'Experience with Agile methodologies and Scrum framework.',
 'Remote',
 '$110,000 - $140,000',
 1);

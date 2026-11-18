DROP DATABASE IF EXISTS job_tracker;
CREATE DATABASE job_tracker;

USE job_tracker;

CREATE TABLE companies (
    company_id INT PRIMARY KEY AUTO_INCREMENT,
    company_name VARCHAR(100) NOT NULL,
    industry VARCHAR(50),
    website VARCHAR(200),
    city VARCHAR(50),
    state VARCHAR(50),
    notes TEXT
);

CREATE TABLE jobs (
    job_id INT PRIMARY KEY AUTO_INCREMENT,
    company_id INT NOT NULL,
    job_title VARCHAR(100) NOT NULL,
    job_type ENUM('Full-time', 'Part-time', 'Contract', 'Internship'),
    salary_min INT,
    salary_max INT,
    job_url VARCHAR(300),
    date_posted DATE,
    requirements JSON,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

CREATE TABLE applications (
    application_id INT PRIMARY KEY AUTO_INCREMENT,
    job_id INT NOT NULL,
    application_date DATE NOT NULL,
    status ENUM('Applied', 'Screening', 'Interview', 'Offer', 'Rejected', 'Withdrawn') DEFAULT 'Applied',
    resume_version VARCHAR(50),
    cover_letter_sent BOOLEAN,
    interview_data JSON,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);

CREATE TABLE contacts (
    contact_id INT PRIMARY KEY AUTO_INCREMENT,
    company_id INT NOT NULL,
    contact_name VARCHAR(100) NOT NULL,
    title VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    linkedin_url VARCHAR(200),
    notes TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- Sample data insertion for testing purposes
INSERT INTO companies (company_name, industry, website, city, state, notes) VALUES
('Tech Innovators Inc.', 'Technology', 'https://www.techinnovators.com', 'San Francisco', 'CA', 'Leading tech company specializing in AI solutions.'),
('Green Energy Solutions', 'Renewable Energy', 'https://www.greenenergy.com', 'Austin', 'TX', 'Focuses on sustainable energy projects and innovations.'),
('HealthCare Plus', 'Healthcare', 'https://www.healthcareplus.com', 'New York', 'NY', 'Provides comprehensive healthcare services and solutions.');

INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements) VALUES
(1, 'Software Engineer', 'Full-time', 90000, 120000, 'https://www.techinnovators.com/careers/software-engineer', '2024-06-01', '{"skills": ["Python", "SQL", "Data Structures", "Flask"], "experience": "3+ years"}'),
(2, 'Project Manager', 'Contract', 70000, 90000, 'https://www.greenenergy.com/careers/project-manager', '2024-05-15', '{"skills": ["Project Management", "Agile", "Communication"], "experience": "5+ years"}'),
(3, 'Data Analyst', 'Full-time', 80000, 100000, 'https://www.healthcareplus.com/careers/data-analyst', '2024-04-20', '{"skills": ["Tableau", "Excel", "Python"], "experience": "2+ years"}');

INSERT INTO applications (job_id, application_date, status, resume_version, cover_letter_sent, interview_data) VALUES
(1, '2024-06-05', 'Applied', 'v1', TRUE, '{"interview_date": "2024-06-10", "interviewers": ["John Doe"], "feedback": "Positive"}'),
(2, '2024-05-20', 'Interview', 'v2', FALSE, '{"interview_date": "2024-05-25", "interviewers": ["Jane Smith", "Ally Wallis"], "feedback": "Needs improvement"}'),
(3, '2024-04-25', 'Offer', 'v1', TRUE, '{"interview_date": "2024-04-30", "interviewers": ["Dr. Emily Johnson", "Bill Murray", "Dave Wilson"], "feedback": "Excellent candidate"}');

INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes) VALUES
(2, 'Hugo Boss', 'Software Engineer I', 'hboss@greenenergy.com', NULL, 'https://www.linkedin.com/hboss', 'Provided letter of recommendation'),
(2, 'Kathy Thomas', 'SE Manager', 'kthomas@greenenergy.com', '954-213-2090', 'https://www.linkedin.com/kathythomas', 'Scheduled a coffee chat to discuss interview tips'),
(3, 'Jerry Watts', 'QA Analyst', 'jerrywatts@healthcareplus.com', '713-265-2753', 'https://www.linkedin.com/jerrywatts', 'Discussed potential job opportunities and company culture');

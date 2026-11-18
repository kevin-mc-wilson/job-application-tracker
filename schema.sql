DROP DATABASE IF EXISTS job_tracker;
CREATE DATABASE job_tracker;

USE job_tracker;
SET NAMES utf8mb4;

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
('HealthCare Plus', 'Healthcare', 'https://www.healthcareplus.com', 'New York', 'NY', 'Provides comprehensive healthcare services and solutions.'),
-- Edge case: company with many jobs and contacts
('Nimbus Cloud Systems', 'Cloud Computing', 'https://www.nimbuscloud.io', 'Seattle', 'WA', 'Hiring aggressively; four open engineering roles.'),
-- Edge case: apostrophe in the name, ampersand in the industry, very long notes
('O''Reilly Data Labs', 'Data & Analytics', 'https://www.oreillydatalabs.com', 'Boston', 'MA', 'Referred by a former classmate. Interview process is five rounds: recruiter screen, SQL take-home, live coding in Python, system design with the data platform team, and a final conversation with the VP of Engineering. Mentioned a strong preference for candidates with production experience in Airflow and Spark. Follow up in two weeks if there is no response.'),
-- Edge case: non-ASCII characters, non-US state code, long website URL with a query string
('Zürich Cloud GmbH', 'Software', 'https://www.zuerichcloud.example.ch/en/careers/engineering?utm_source=jobtracker&utm_campaign=2025', 'Zürich', 'ZH', 'Remote-friendly; relocation support offered.'),
-- Edge case: only the required column is filled in; no jobs or contacts yet
('Stealth Startup', NULL, NULL, NULL, NULL, NULL),
('CyberShield Security', 'Cybersecurity', 'https://www.cybershield.example', 'Miami', 'FL', 'Local to South Florida. Hybrid schedule.');

INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements) VALUES
(1, 'Software Engineer', 'Full-time', 90000, 120000, 'https://www.techinnovators.com/careers/software-engineer', '2024-06-01', '{"skills": ["Python", "SQL", "Data Structures", "Flask"], "experience": "3+ years"}'),
(2, 'Project Manager', 'Contract', 70000, 90000, 'https://www.greenenergy.com/careers/project-manager', '2024-05-15', '{"skills": ["Project Management", "Agile", "Communication"], "experience": "5+ years"}'),
(3, 'Data Analyst', 'Full-time', 80000, 100000, 'https://www.healthcareplus.com/careers/data-analyst', '2024-04-20', '{"skills": ["Tableau", "Excel", "Python"], "experience": "2+ years"}'),
-- Edge case: 6 required skills
(4, 'Cloud Infrastructure Engineer', 'Full-time', 110000, 145000, 'https://www.nimbuscloud.io/careers/cloud-infrastructure-engineer', '2025-02-10', '{"skills": ["AWS", "Docker", "Kubernetes", "Terraform", "Python", "Linux"], "experience": "4+ years"}'),
-- Edge case: duplicate skill with different capitalization ("Python" and "python")
(4, 'Site Reliability Engineer', 'Full-time', 120000, 160000, 'https://www.nimbuscloud.io/careers/sre', '2025-02-12', '{"skills": ["Linux", "Kubernetes", "Python", "Monitoring", "python"], "experience": "3+ years"}'),
-- Edge case: no salary, no date posted, no URL
(4, 'DevOps Intern', 'Internship', NULL, NULL, NULL, NULL, '{"skills": ["Linux", "Git"], "experience": "None"}'),
-- Edge case: minimum salary only, and requirements with no "skills" key
(4, 'Technical Writer (Developer Docs)', 'Contract', 60000, NULL, 'https://www.nimbuscloud.io/careers/technical-writer', '2025-01-28', '{"experience": "2+ years"}'),
-- Edge case: 10 required skills
(5, 'Data Scientist', 'Full-time', 115000, 150000, 'https://www.oreillydatalabs.com/jobs/data-scientist', '2025-02-03', '{"skills": ["Python", "SQL", "Machine Learning", "Pandas", "Tableau", "Statistics", "R", "Spark", "Airflow", "Jupyter"], "experience": "3+ years"}'),
-- Edge case: extra whitespace inside skill names, part-time role
(5, 'Junior Data Analyst (Entry-Level)', 'Part-time', 45000, 55000, 'https://www.oreillydatalabs.com/jobs/junior-data-analyst', '2025-02-18', '{"skills": ["  SQL ", "Excel", "Tableau"], "experience": "0-1 years"}'),
-- Edge case: no job type, no minimum salary, skill name with a dot
(6, 'Full-Stack Developer (React / Node.js)', NULL, NULL, 130000, 'https://www.zuerichcloud.example.ch/en/careers/full-stack', '2025-01-15', '{"skills": ["JavaScript", "React", "Node.js", "SQL"], "experience": "3+ years"}'),
-- Edge case: minimum salary equals maximum salary, and NULL requirements
(6, 'Mobile App Developer', 'Contract', 90000, 90000, NULL, '2025-02-05', NULL),
-- Edge case: requirements stored as a plain JSON array instead of an object
(8, 'Security Analyst', 'Full-time', 85000, 105000, 'https://www.cybershield.example/careers/security-analyst', '2025-02-08', '["Networking", "SIEM", "Python", "Incident Response"]'),
-- Edge case: unicode and parentheses in the title, empty skills list, large salary
(8, 'Penetration Tester (Red Team) – Senior', 'Full-time', 130000, 170000, 'https://www.cybershield.example/careers/senior-penetration-tester-red-team?source=jobtracker', '2025-11-10', '{"skills": [], "experience": "5+ years"}');

INSERT INTO applications (job_id, application_date, status, resume_version, cover_letter_sent, interview_data) VALUES
(1, '2024-06-05', 'Applied', 'v1', TRUE, '{"interview_date": "2024-06-10", "interviewers": ["John Doe"], "feedback": "Positive"}'),
(2, '2024-05-20', 'Interview', 'v2', FALSE, '{"interview_date": "2024-05-25", "interviewers": ["Jane Smith", "Ally Wallis"], "feedback": "Needs improvement"}'),
(3, '2024-04-25', 'Offer', 'v1', TRUE, '{"interview_date": "2024-04-30", "interviewers": ["Dr. Emily Johnson", "Bill Murray", "Dave Wilson"], "feedback": "Excellent candidate"}'),
-- Edge case: NULL interview data
(4, '2025-03-01', 'Applied', 'v3', TRUE, NULL),
-- Edge case: second application to the same job; NULL resume and cover letter; apostrophes and non-ASCII text in the JSON
(4, '2025-01-10', 'Rejected', NULL, NULL, '{"interview_date": "2025-01-20", "interviewers": ["Siobhán O''Neil"], "feedback": "Candidate''s Kubernetes experience was thin; suggested reapplying after a café chat in the spring"}'),
-- Edge case: empty interviewers list
(5, '2025-02-14', 'Screening', 'v2-sre', FALSE, '{"interviewers": []}'),
-- Edge case: four interviewers and long feedback
(5, '2025-02-20', 'Interview', 'v2-sre', TRUE, '{"interview_date": "2025-03-04", "interviewers": ["Raj Patel", "Dana Kim", "Luis Ortega", "Amara Okafor"], "feedback": "Strong systems-design round. Struggled slightly on the Linux networking questions. Panel wants a follow-up conversation about on-call expectations and the team''s incident process before making a decision."}'),
-- Edge case: JSON without the "interviewers" key
(8, '2024-12-30', 'Withdrawn', 'v1', TRUE, '{"interview_date": "2025-01-08", "feedback": "Withdrew after accepting another offer"}'),
(12, '2025-02-01', 'Offer', 'v4', TRUE, '{"interview_date": "2025-02-12", "interviewers": ["Priya Natarajan", "Chen Wei"], "feedback": "Offer extended: $98k base plus equity"}'),
-- Edge case: most recent application date, so it appears first on the dashboard
(13, '2026-11-17', 'Applied', 'v4', TRUE, NULL);

INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes) VALUES
(2, 'Hugo Boss', 'Software Engineer I', 'hboss@greenenergy.com', NULL, 'https://www.linkedin.com/hboss', 'Provided letter of recommendation'),
(2, 'Kathy Thomas', 'SE Manager', 'kthomas@greenenergy.com', '954-213-2090', 'https://www.linkedin.com/kathythomas', 'Scheduled a coffee chat to discuss interview tips'),
(3, 'Jerry Watts', 'QA Analyst', 'jerrywatts@healthcareplus.com', '713-265-2753', 'https://www.linkedin.com/jerrywatts', 'Discussed potential job opportunities and company culture'),
-- Edge case: non-ASCII name with an apostrophe, "+" tag in the email, long LinkedIn URL and long notes
(4, 'Siobhán O''Neil', 'Engineering Manager', 'siobhan.oneil+recruiting@nimbuscloud.io', '+1 (206) 555-0142', 'https://www.linkedin.com/in/siobhan-oneil-engineering-leader-seattle-cloud-infrastructure-a1b2c3d4', 'Met at a cloud meetup. Hiring manager for the Cloud Infrastructure Engineer role. Prefers email over LinkedIn messages and usually replies within two days.'),
-- Edge case: only a name, title and email; phone, LinkedIn and notes are NULL
(4, 'Raj Patel', 'Senior SRE', 'raj@nimbuscloud.io', NULL, NULL, NULL),
-- Edge case: phone number with an extension; email is NULL
(8, 'Dr. Mei-Ling Zhou', 'CISO', NULL, '305-555-0188 x204', 'https://www.linkedin.com/in/meilingzhou', 'Speaks at security conferences; connected through the campus career fair.'),
-- Edge case: only the required name is filled in
(5, 'Tom', NULL, NULL, NULL, NULL, NULL);

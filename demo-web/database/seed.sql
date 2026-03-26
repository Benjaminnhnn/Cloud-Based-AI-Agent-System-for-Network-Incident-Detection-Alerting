-- Seed sample data
INSERT INTO users (email, username, password_hash, full_name, is_active) VALUES
('admin@example.com', 'admin', '$2b$12$abcdefghijklmnopqrstuvwxyz', 'Admin User', TRUE),
('user@example.com', 'user', '$2b$12$abcdefghijklmnopqrstuvwxyz', 'Demo User', TRUE)
ON CONFLICT DO NOTHING;

INSERT INTO projects (user_id, name, description, status) VALUES
(1, 'AIOps Platform', 'AI-powered monitoring and alerting platform', 'active'),
(1, 'Cloud Infrastructure', 'AWS hybrid cloud setup', 'active'),
(2, 'Demo Application', 'Full stack demo application', 'active')
ON CONFLICT DO NOTHING;

INSERT INTO tasks (project_id, title, description, status, priority) VALUES
(1, 'Setup monitoring', 'Configure Prometheus and Grafana', 'completed', 'high'),
(1, 'Deploy AI Agent', 'Deploy AI agent for incident analysis', 'in_progress', 'high'),
(1, 'Setup alerting', 'Configure alert rules and notifications', 'pending', 'medium'),
(2, 'Terraform setup', 'Create infrastructure as code', 'completed', 'high'),
(3, 'Frontend dev', 'Build React frontend', 'in_progress', 'high'),
(3, 'Backend API', 'Develop FastAPI backend', 'in_progress', 'high'),
(3, 'Database setup', 'Configure PostgreSQL', 'pending', 'high')
ON CONFLICT DO NOTHING;

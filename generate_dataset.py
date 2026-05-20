"""
Generates all synthetic enterprise datasets under data/.
Run once before ingestion: python generate_dataset.py
"""

import json
import csv
import random
from pathlib import Path
from datetime import datetime, timedelta
from fpdf import FPDF

BASE = Path(__file__).parent / "data"


# ── PDF helpers ──────────────────────────────────────────────────────────────

class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, self.title, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def chapter(self, title: str, body: str):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", size=10)
        self.multi_cell(0, 6, body)
        self.ln(4)


def make_hr_policy_pdf(path: Path):
    pdf = PDF()
    pdf.title = "Acme Corp - HR Policy Manual v3.2"
    pdf.add_page()

    pdf.chapter(
        "1. Annual & Sick Leave",
        (
            "All full-time employees are entitled to 20 days of paid annual leave per calendar year. "
            "Leave accrues at 1.67 days per month and unused leave may be carried forward up to 5 days. "
            "Sick leave is capped at 10 days per year; a medical certificate is required for absences exceeding 3 consecutive days. "
            "Leave requests must be submitted via the HR portal at least 5 business days in advance for planned absences."
        ),
    )
    pdf.chapter(
        "2. Maternity & Paternity Leave",
        (
            "Primary caregivers are entitled to 16 weeks of fully paid maternity leave, extendable by 4 weeks unpaid. "
            "Secondary caregivers (paternity leave) receive 4 weeks of fully paid leave within the first 12 months after birth or adoption. "
            "Shared parental leave allows couples to split up to 37 weeks of paid leave between them. "
            "Employees must notify HR at least 8 weeks before the expected leave start date."
        ),
    )
    pdf.chapter(
        "3. Remote Work Policy",
        (
            "Employees may work remotely up to 3 days per week, subject to manager approval. "
            "Remote work is not permitted during the first 90 days of employment. "
            "All remote workers must maintain a secure home office environment and connect via the company VPN. "
            "Core hours for collaboration are 10:00-15:00 in the employee's local timezone. "
            "Equipment allowance: up to $500 for home office setup, reimbursed upon submission of receipts."
        ),
    )
    pdf.chapter(
        "4. Performance Reviews",
        (
            "Formal performance reviews are conducted bi-annually: mid-year in June and end-of-year in December. "
            "Each review includes a self-assessment, peer feedback (360 degrees), and manager evaluation. "
            "Ratings: Exceptional (5), Exceeds Expectations (4), Meets Expectations (3), Needs Improvement (2), Unsatisfactory (1). "
            "Employees rated Exceptional or Exceeds Expectations are eligible for discretionary bonuses of 10-20% of base salary. "
            "Performance Improvement Plans (PIPs) are issued when an employee receives two consecutive Needs Improvement ratings."
        ),
    )
    pdf.chapter(
        "5. Code of Conduct",
        (
            "All employees must act with integrity, respect colleagues, and protect company assets. "
            "Harassment, discrimination, and retaliation are strictly prohibited and may result in immediate termination. "
            "Conflicts of interest must be declared to the Ethics Committee within 5 business days of arising. "
            "Confidential company information must not be shared outside the organisation without written authorisation. "
            "Violations should be reported to hr@acmecorp.com or via the anonymous ethics hotline: 1-800-ETHICS."
        ),
    )
    pdf.chapter(
        "6. Expense Reimbursement",
        (
            "Business expenses up to $100 require manager approval and must be submitted within 30 days. "
            "Expenses between $100 and $500 require manager and finance approval. "
            "Expenses exceeding $500 require VP-level approval plus finance sign-off. "
            "Travel expenses: economy class for flights under 6 hours; business class permitted for longer journeys. "
            "Expense reports must include original receipts and a brief business justification."
        ),
    )
    pdf.output(str(path))


def make_finance_report_pdf(path: Path):
    pdf = PDF()
    pdf.title = "Acme Corp - Q4 2024 Financial Report (CONFIDENTIAL)"
    pdf.add_page()

    pdf.chapter(
        "1. Executive Summary",
        (
            "Acme Corp delivered strong Q4 2024 results, with total revenue of $12.5 million, up 15% year-over-year. "
            "Operating expenses were contained at $8.2 million, resulting in a net income of $4.3 million (34.4% margin). "
            "Cash and cash equivalents at quarter-end: $18.7 million. "
            "The Board approved a $2 million share buyback programme for Q1 2025."
        ),
    )
    pdf.chapter(
        "2. Revenue Breakdown by Product",
        (
            "Enterprise Suite: $6.2M (49.6% of total revenue, +22% YoY). "
            "Professional Services: $3.1M (24.8%, +8% YoY). "
            "SMB Cloud Tier: $2.4M (19.2%, +11% YoY). "
            "Legacy On-Premise Licences: $0.8M (6.4%, -18% YoY - phasing out). "
            "New contracts signed in Q4: 47 enterprise, 132 SMB."
        ),
    )
    pdf.chapter(
        "3. Department Budgets (Annual)",
        (
            "Engineering: $2.1M (headcount: 42 FTEs). "
            "Sales & Marketing: $1.5M (headcount: 28 FTEs). "
            "Human Resources: $0.8M (headcount: 12 FTEs). "
            "IT Operations: $1.2M (headcount: 18 FTEs). "
            "Finance & Legal: $0.9M (headcount: 15 FTEs). "
            "Customer Success: $0.7M (headcount: 14 FTEs). "
            "Total headcount: 129 FTEs. Average cost per FTE: $57,364."
        ),
    )
    pdf.chapter(
        "4. Operating Expenses",
        (
            "Personnel costs: $5.8M (71% of opex). "
            "Cloud infrastructure (AWS + GCP): $0.9M. "
            "Software licences & SaaS tools: $0.4M. "
            "Office & facilities: $0.6M. "
            "Marketing & events: $0.3M. "
            "Legal & compliance: $0.2M."
        ),
    )
    pdf.chapter(
        "5. Outlook for Q1 2025",
        (
            "Revenue guidance: $13.0-13.5M (+4-8% QoQ). "
            "Key growth drivers: Enterprise Suite expansion, new APAC partnerships, and the upcoming v4.0 platform release. "
            "Planned headcount additions: 8 engineers, 3 sales representatives, 2 customer success managers. "
            "Capital expenditure: $350K for data-centre hardware refresh."
        ),
    )
    pdf.output(str(path))


def make_it_security_pdf(path: Path):
    pdf = PDF()
    pdf.title = "Acme Corp - IT Security & Compliance Policy v2.1"
    pdf.add_page()

    pdf.chapter(
        "1. Password Policy",
        (
            "All passwords must be a minimum of 12 characters and include at least one uppercase letter, "
            "one lowercase letter, one digit, and one special character. "
            "Passwords must be changed every 90 days. Password reuse (last 10 passwords) is prohibited. "
            "Multi-Factor Authentication (MFA) is mandatory for all accounts with access to production systems or sensitive data. "
            "Password managers are approved and encouraged; storing passwords in plaintext is a policy violation."
        ),
    )
    pdf.chapter(
        "2. Data Classification",
        (
            "Public: Marketing materials, press releases - no restrictions. "
            "Internal: General business documents - accessible to all employees, not for external sharing. "
            "Confidential: Financial records, HR data, customer PII - role-based access only. "
            "Restricted: Source code, encryption keys, security configs - minimum-privilege access, audit-logged. "
            "All data must be labelled at creation. Misclassification incidents must be reported within 24 hours."
        ),
    )
    pdf.chapter(
        "3. Incident Response Procedure",
        (
            "P1 (Critical): System-wide outage or data breach - respond within 15 minutes, escalate to CTO + CEO. "
            "P2 (High): Service degradation or security anomaly - respond within 1 hour, notify IT Manager. "
            "P3 (Medium): Non-critical bug or minor unauthorised access attempt - resolve within 24 hours. "
            "P4 (Low): Cosmetic issues, informational alerts - resolve within 5 business days. "
            "All incidents must be logged in the incident tracker (Jira project: ITSEC) within 30 minutes of detection."
        ),
    )
    pdf.chapter(
        "4. Remote Access & VPN",
        (
            "All remote access to internal systems requires an active VPN connection (WireGuard on port 51820). "
            "VPN split-tunnelling is disabled; all traffic routes through the corporate gateway. "
            "Personal devices must pass endpoint compliance checks (OS patch level, AV active, disk encrypted). "
            "VPN session timeout: 8 hours of inactivity. "
            "USB storage devices are blocked on all corporate endpoints by MDM policy."
        ),
    )
    pdf.chapter(
        "5. Audit & Compliance",
        (
            "Quarterly security audits are conducted by the IT Operations team with external pen-tests annually. "
            "Access logs for privileged accounts are retained for 12 months and reviewed monthly. "
            "The company is SOC 2 Type II and ISO 27001 certified. "
            "GDPR compliance: Data Subject Access Requests (DSARs) must be fulfilled within 30 days. "
            "Next external audit: March 2025 (scheduled with SecureAudit Inc.)."
        ),
    )
    pdf.output(str(path))


# ── Structured CSV data ───────────────────────────────────────────────────────

DEPARTMENTS = ["Engineering", "Finance", "HR", "IT Operations", "Sales", "Customer Success", "Legal"]
ROLES_EMP = {
    "Engineering": ["Software Engineer", "Senior Engineer", "Tech Lead", "Engineering Manager"],
    "Finance": ["Financial Analyst", "Senior Analyst", "Finance Manager", "CFO"],
    "HR": ["HR Coordinator", "HR Business Partner", "HR Manager", "CHRO"],
    "IT Operations": ["IT Support", "SysAdmin", "Security Engineer", "IT Manager"],
    "Sales": ["Sales Rep", "Account Executive", "Sales Manager", "VP Sales"],
    "Customer Success": ["CSM", "Senior CSM", "CS Team Lead", "VP Customer Success"],
    "Legal": ["Legal Counsel", "Senior Counsel", "General Counsel"],
}
SALARY_BANDS = {
    "Engineering": (80000, 180000),
    "Finance": (70000, 150000),
    "HR": (60000, 120000),
    "IT Operations": (65000, 130000),
    "Sales": (55000, 140000),
    "Customer Success": (55000, 120000),
    "Legal": (90000, 200000),
}

FIRST_NAMES = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Hank",
               "Iris", "Jack", "Karen", "Leo", "Mia", "Nate", "Olivia", "Paul",
               "Quinn", "Rachel", "Sam", "Tara", "Uma", "Victor", "Wendy", "Xander",
               "Yara", "Zoe", "Aaron", "Beth", "Caleb", "Diana"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
              "Davis", "Martinez", "Wilson", "Anderson", "Taylor", "Thomas", "Jackson",
              "White", "Harris", "Martin", "Thompson", "Robinson", "Clark"]


def make_employees_csv(path: Path):
    random.seed(42)
    rows = []
    for i in range(1, 51):
        dept = random.choice(DEPARTMENTS)
        role = random.choice(ROLES_EMP[dept])
        low, high = SALARY_BANDS[dept]
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        rows.append({
            "employee_id": f"EMP{i:04d}",
            "name": name,
            "department": dept,
            "role": role,
            "salary": random.randint(low // 1000, high // 1000) * 1000,
            "start_date": f"20{random.randint(18,23):02d}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "status": random.choice(["Active", "Active", "Active", "On Leave"]),
        })
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


SERVICES = ["auth-service", "payment-gateway", "api-gateway", "user-service",
            "reporting-service", "db-primary", "db-replica", "cache-redis",
            "email-worker", "file-storage"]
INCIDENT_TYPES = [
    "CPU spike detected on {svc} (usage: {pct}%)",
    "Memory usage high on {svc} ({pct}% of 16 GB)",
    "Database connection pool exhausted on {svc}",
    "SSL certificate for {svc} expires in {days} days",
    "Latency spike: {svc} P99 = {ms}ms (threshold: 500ms)",
    "Failed login attempt on {svc} from IP 192.168.{a}.{b}",
    "Disk usage on {svc} at {pct}%",
    "Service {svc} restarted after OOM kill",
    "Scheduled backup completed successfully on {svc}",
    "Health check passed for {svc}",
    "Config change deployed to {svc} by admin",
    "Rate limit triggered on {svc}: {n} requests/min",
]


def make_incidents_csv(path: Path):
    random.seed(7)
    severities = ["Critical", "High", "Medium", "Low"]
    statuses = ["Open", "In Progress", "Resolved", "Closed"]
    depts = ["IT Operations", "Engineering", "IT Operations", "Engineering", "Security"]
    rows = []
    base = datetime(2024, 12, 1)
    for i in range(1, 31):
        sev = random.choices(severities, weights=[1, 3, 5, 4])[0]
        rows.append({
            "incident_id": f"INC{i:04d}",
            "severity": sev,
            "department": random.choice(depts),
            "service": random.choice(SERVICES),
            "description": random.choice(INCIDENT_TYPES).format(
                svc=random.choice(SERVICES), pct=random.randint(75, 99),
                days=random.randint(1, 30), ms=random.randint(500, 5000),
                a=random.randint(1, 254), b=random.randint(1, 254),
                n=random.randint(100, 1000),
            ),
            "status": random.choice(statuses),
            "date": (base + timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
            "assigned_to": f"dave@acmecorp.com",
        })
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


# ── JSON logs ─────────────────────────────────────────────────────────────────

LOG_MESSAGES = [
    ("INFO",     "auth-service",       "User login successful for user_id={uid}"),
    ("INFO",     "payment-gateway",    "Payment processed: txn_id={txn}, amount=${amt}"),
    ("WARNING",  "api-gateway",        "High latency detected: {ms}ms on /api/v2/reports"),
    ("ERROR",    "db-primary",         "Connection timeout after 30s - retrying ({n}/3)"),
    ("CRITICAL", "auth-service",       "Multiple failed login attempts from IP 10.0.{a}.{b} - account locked"),
    ("INFO",     "reporting-service",  "Report generation completed in {ms}ms"),
    ("WARNING",  "cache-redis",        "Cache hit rate dropped to {pct}% (threshold: 70%)"),
    ("ERROR",    "email-worker",       "SMTP connection refused - queued {n} messages"),
    ("INFO",     "file-storage",       "File uploaded: {fname} ({size}MB) by user {uid}"),
    ("CRITICAL", "db-replica",         "Replication lag exceeds 30 seconds — failover triggered"),
    ("INFO",     "user-service",       "Profile updated for user_id={uid}"),
    ("WARNING",  "api-gateway",        "Rate limit approaching for client_id={uid} ({n}/1000 req/min)"),
    ("ERROR",    "payment-gateway",    "Payment declined: txn_id={txn}, reason=insufficient_funds"),
    ("INFO",     "auth-service",       "Password reset completed for user_id={uid}"),
    ("WARNING",  "db-primary",         "Slow query detected ({ms}ms): SELECT * FROM audit_logs WHERE..."),
    ("INFO",     "cache-redis",        "Cache eviction: {n} keys removed (LRU policy)"),
    ("CRITICAL", "auth-service",       "Brute-force attack detected - WAF rule triggered, IP blocked"),
    ("INFO",     "reporting-service",  "Scheduled job 'daily_summary' completed successfully"),
    ("ERROR",    "file-storage",       "Disk usage at {pct}% - alert sent to IT Operations"),
    ("INFO",     "api-gateway",        "Deployment v3.4.1 rolled out to production ({n} instances)"),
]


def make_system_logs(path: Path):
    random.seed(99)
    entries = []
    base = datetime(2024, 12, 15, 0, 0, 0)
    for i in range(100):
        level, svc, tmpl = random.choice(LOG_MESSAGES)
        msg = tmpl.format(
            uid=f"U{random.randint(1000,9999)}",
            txn=f"TXN{random.randint(100000,999999)}",
            amt=round(random.uniform(10, 5000), 2),
            ms=random.randint(50, 8000),
            n=random.randint(1, 500),
            pct=random.randint(40, 99),
            a=random.randint(1, 254),
            b=random.randint(1, 254),
            fname=f"report_{random.randint(1,100)}.pdf",
            size=round(random.uniform(0.1, 50), 1),
        )
        entries.append({
            "timestamp": (base + timedelta(minutes=i * 14 + random.randint(0, 13))).isoformat(),
            "level": level,
            "service": svc,
            "message": msg,
            "host": f"prod-{svc}-{random.randint(1,4):02d}",
        })
    with open(path, "w") as f:
        json.dump(entries, f, indent=2)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    docs = BASE / "documents"
    structured = BASE / "structured"
    logs = BASE / "logs"

    print("Generating HR Policy PDF …")
    make_hr_policy_pdf(docs / "hr_policy.pdf")

    print("Generating Finance Report PDF …")
    make_finance_report_pdf(docs / "finance_report.pdf")

    print("Generating IT Security PDF …")
    make_it_security_pdf(docs / "it_security.pdf")

    print("Generating employees.csv …")
    make_employees_csv(structured / "employees.csv")

    print("Generating incidents.csv …")
    make_incidents_csv(structured / "incidents.csv")

    print("Generating system_logs.json …")
    make_system_logs(logs / "system_logs.json")

    print("\nDone — all synthetic data generated under data/")


if __name__ == "__main__":
    main()

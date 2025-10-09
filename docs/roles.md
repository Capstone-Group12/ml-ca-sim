# Team Roles and Responsibilities

We are approaching the Capstone project with a **role-based structure**. Each team member will lead a specific feature area, while collaborating across boundaries where needed. This ensures accountability, balanced workload, and modular development.

---

## 1. Frontend Lead

### Responsibilities

- Build the UI/UX of the website.
- Integrate frontend with backend endpoints.
- Ensure responsive design and usability.

### Deliverables

- Production-ready frontend for running attack simulations.

### Technologies

- Next.js / React
- Tailwind CSS
- MaterialUI (recommended for rapid component development)

---

## 2. Backend Lead

### Responsibilities

- Convert frontend requests into sanitized payloads.
- Validate requests against schemas before passing to the ML service.
- Provide clear and secure endpoints to interact with ML models.

### Deliverables

- API endpoints for simulation traffic.
- Request/response schemas and validation logic.

### Technologies

- Next.js (API routes) / Node.js / Express
- Common schema/model-based design patterns

---

## 3. ML Lead

### Responsibilities

- Design and train machine learning models to detect cyberattacks.
- Integrate trained models into FastAPI endpoints.
- Ensure models follow best practices in Python development (typing, separation of concerns, conventions).

### Deliverables

- ML models for detecting attacks (brute force, scraper surge, XSS, [stretch: Slowloris]).
- Exposed FastAPI endpoints for predictions.

### Technologies

- Python
- FastAPI
- Scikit-learn / ONNX or similar ML libraries

---

## 4. QA / Tests Lead

### Responsibilities

- Create simulations and test harnesses for cyberattacks.
- Validate that ML models detect and respond correctly under load.
- Optimize performance, ensuring quick response times.
- Document testing plans and results.

### Deliverables

- Scripts for load testing and attack simulation (e.g., brute force, scraper, replay traffic).
- Reports verifying model performance and system reliability.

### Technologies

- k6 load tests
- Custom attack simulation scripts
- Integration test frameworks

---

## 5. PM Lead (Floating Contributor)

### Responsibilities

- Coordinate project timeline, task delegation, and communication.
- Maintain GitHub Project board, milestones, and CODEOWNERS mappings.
- Document architecture, workflow, and final report materials.
- Provide development support across all areas to balance workload.

### Deliverables

- Project documentation (README, architecture diagrams, final report).
- Assistance in high-demand areas (e.g., Python model development, API integration, frontend tasks).
- Ensure timely delivery and balanced team contributions.

### Technologies

- GitHub Projects / Issues / CODEOWNERS
- Markdown / diagrams for documentation
- Familiarity with all tech stacks for cross-support

---

## Notes

- Roles are **primary ownerships**, but collaboration is expected.
- The **PM Lead** serves as a **floating contributor**, assisting whichever role is most overloaded.
- All code changes will go through PRs, with CODEOWNERS ensuring the appropriate lead is requested as a reviewer.
- Equal contribution is required; workload will be balanced throughout the project.

---

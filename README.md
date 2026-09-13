# HSIMS (Inventory Management System)

A full-stack Inventory Management System built with a FastAPI/Python backend and a Next.js (TypeScript) frontend, fully containerized using Docker. This system tracks product recipes, materials, inventory ledgers, and lot allocations.

---

## 🏗️ Project Architecture

The application is split into two primary components and containerized for consistent development and deployment:

* **Frontend (`/frontend`)**
  * Built with Next.js (App Router) and TypeScript.
  * Fetches and displays production inventory and material ledgers.
* **Backend (`/backend`)**
  * Powered by Python/FastAPI.
  * Interacts directly with a PostgreSQL database to manage product definitions, recipes, and material quantities.

---

## 🛠️ Tech Stack

* **Frontend:** Next.js, React, TypeScript, Tailwind CSS
* **Backend:** FastAPI, Python
* **Database:** PostgreSQL
* **DevOps:** Docker, Docker Compose

---

## 🚀 Getting Started

### Prerequisites
Make sure you have the following installed on your machine:
* [Docker Desktop](https://docker.com)
* [Docker Compose](https://docker.com)

### Installation & Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd HSIMS
   ```

2. **Spin up the containers:**
   Run the following command to build images and launch the containers (Database, Backend, and Frontend) all at once:
   ```bash
   docker compose up --build
   ```

3. **Access the application:**
   * **Next.js Frontend:** `http://localhost:3000`
   * **FastAPI Backend Documentation:** `http://localhost:8000/docs`

---

## 📡 API Endpoints (Quick Reference)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/products/ledger/` | Fetches the full product inventory ledger. |
| **POST** | `/production/inventory/` | Submits material issue requests. |

---

## 💡 Troubleshooting Docker Networking

* **"Fetch Failed" in Server Components:** 
  If your Next.js frontend fails to communicate with the backend, ensure you are not using `localhost:8000` inside Server-Side fetches. Instead, use your Docker network service identifier defined in `docker-compose.yml`:
  ```typescript
  // Inside server components, use the service container name
  const res = await fetch('http://backend:8000/products/ledger/');
  ```

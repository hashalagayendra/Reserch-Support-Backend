# Database Structure & Entity Relationships

This document details the database architecture, schema models, table columns, constraints, and entity relationships defined in [`app/db/models.py`](file:///d:/personal%20project/reserch2/app/db/models.py).

---

## 1. Visual Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    users ||--o{ projects : "owns (1:N)"
    projects ||--o{ ai_tools : "contains (1:N)"
    projects ||--o{ api_keys : "owns (1:N)"

    users {
        int id PK "Primary Key"
        string email UK "Unique, Not Null"
        string hashed_password "Not Null"
        datetime created_at "Timestamp"
        datetime updated_at "Timestamp"
    }

    projects {
        int id PK "Primary Key"
        int user_id FK "Foreign Key -> users.id"
        string name "Indexed, Not Null"
        datetime created_at "Timestamp"
        datetime updated_at "Timestamp"
    }

    api_keys {
        int id PK "Primary Key"
        int project_id FK "Foreign Key -> projects.id (CASCADE)"
        string key_value UK "Unique, Indexed, Not Null"
        datetime created_at "Timestamp"
        datetime updated_at "Timestamp"
    }

    ai_tools {
        int id PK "Primary Key"
        int project_id FK "Foreign Key -> projects.id (CASCADE)"
        string tool_title "Indexed, Not Null"
        string description "Nullable"
        json argument "JSON schema of tool parameters"
        string api_url "Target REST API endpoint URL"
        string http_method "GET / POST / PUT etc."
        json headers "JSON HTTP Headers"
        vector_1024 vector_data "pgvector vector (1024 dimensions)"
        datetime created_at "Timestamp"
        datetime updated_at "Timestamp"
    }

    students {
        int id PK "Primary Key (Legacy / Demo)"
        string first_name "Indexed, Not Null"
        string last_name "Indexed, Not Null"
        string email UK "Unique, Indexed, Not Null"
        int age "Nullable"
        boolean is_active "Default: True"
        datetime created_at "Timestamp"
        datetime updated_at "Timestamp"
    }
```

---

## 2. Architecture Flowchart Graph

```mermaid
graph TD
    classDef primary fill:#1e293b,stroke:#64748b,color:#f8fafc,stroke-width:2px;
    classDef vector fill:#0f172a,stroke:#38bdf8,color:#38bdf8,stroke-width:2px;
    classDef standalone fill:#1e293b,stroke:#475569,color:#94a3b8,stroke-width:1px;

    UserTable["👤 User<br/><i>(users)</i>"]
    ProjectTable["📁 Project<br/><i>(projects)</i>"]
    ApiKeyTable["🔑 ApiKey<br/><i>(api_keys)</i>"]
    AIToolTable["🤖 AITool<br/><i>(ai_tools)</i>"]
    VectorCol["🧠 vector_data<br/><i>pgvector (1024 dims)</i>"]
    StudentTable["🎓 Student<br/><i>(students)</i>"]

    class UserTable,ProjectTable,ApiKeyTable primary;
    class VectorCol vector;
    class AIToolTable primary;
    class StudentTable standalone;

    UserTable -->|"1 : N (Owns)"| ProjectTable
    ProjectTable -->|"1 : N (Owns)"| ApiKeyTable
    ProjectTable -->|"1 : N (Contains)"| AIToolTable
    AIToolTable --- VectorCol
```

---

## 3. Table Schemas & Specifications

### 👤 Table: `users`
Stores system user accounts.

| Column | Type | Constraints / Key | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key, Indexed | Unique identifier for user |
| `email` | `VARCHAR` | Unique, Indexed, Not Null | Account email address |
| `hashed_password` | `VARCHAR` | Not Null | Hashed account password |
| `created_at` | `TIMESTAMP` | Server Default `NOW()` | Account creation timestamp |
| `updated_at` | `TIMESTAMP` | On Update `NOW()` | Last record modification timestamp |

---

### 📁 Table: `projects`
Workspaces created by users to group resources, API keys, and tools.

| Column | Type | Constraints / Key | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key, Indexed | Unique identifier for project |
| `user_id` | `INTEGER` | Foreign Key (`users.id`), Not Null | Owner of this project |
| `name` | `VARCHAR` | Indexed, Not Null | Display name of the project |
| `created_at` | `TIMESTAMP` | Server Default `NOW()` | Project creation timestamp |
| `updated_at` | `TIMESTAMP` | On Update `NOW()` | Last record modification timestamp |

---

### 🔑 Table: `api_keys`
API authentication keys scoped directly to a single project (**One-to-Many**).

| Column | Type | Constraints / Key | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key, Indexed | Unique identifier for API key |
| `project_id` | `INTEGER` | Foreign Key (`projects.id` CASCADE), Not Null | Associated Project ID |
| `key_value` | `VARCHAR` | Unique, Indexed, Not Null | Secret key string (e.g. `sk-dummy-...`) |
| `created_at` | `TIMESTAMP` | Server Default `NOW()` | Key generation timestamp |
| `updated_at` | `TIMESTAMP` | On Update `NOW()` | Last record modification timestamp |

---

### 🤖 Table: `ai_tools`
Stores REST API tools discovered or registered for autonomous agent execution.

| Column | Type | Constraints / Key | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key, Indexed | Unique tool identifier |
| `project_id` | `INTEGER` | Foreign Key (`projects.id` CASCADE), Not Null | Project owning this tool |
| `tool_title` | `VARCHAR` | Indexed, Not Null | Short identifier / name of the tool |
| `description` | `VARCHAR` | Nullable | Functional description of tool capabilities |
| `argument` | `JSON` | Nullable | Parameter definitions (types, descriptions, locations) |
| `api_url` | `VARCHAR` | Nullable | Target REST endpoint URL |
| `http_method` | `VARCHAR` | Nullable | HTTP verb (`GET`, `POST`, `PUT`, etc.) |
| `headers` | `JSON` | Nullable | Required HTTP headers dictionary |
| `vector_data` | `Vector(1024)` | PostgreSQL `pgvector` | Embedding vector for semantic similarity search |
| `created_at` | `TIMESTAMP` | Server Default `NOW()` | Tool registration timestamp |
| `updated_at` | `TIMESTAMP` | On Update `NOW()` | Last record modification timestamp |

---

### 🎓 Table: `students` *(Standalone / Legacy)*
Demo table for initial CRUD endpoints.

| Column | Type | Constraints / Key | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key, Indexed | Unique student identifier |
| `first_name` | `VARCHAR` | Indexed, Not Null | First name |
| `last_name` | `VARCHAR` | Indexed, Not Null | Last name |
| `email` | `VARCHAR` | Unique, Indexed, Not Null | Email address |
| `age` | `INTEGER` | Nullable | Student age |
| `is_active` | `BOOLEAN` | Default `True` | Active status flag |
| `created_at` | `TIMESTAMP` | Server Default `NOW()` | Record creation timestamp |
| `updated_at` | `TIMESTAMP` | On Update `NOW()` | Last record modification timestamp |

---

## 4. Entity Relationships Summary

1. **User ➔ Projects (`1 : N`)**
   - A single `User` can own zero, one, or multiple `Projects`.
   - `User.projects` cascade-deletes all associated projects if the user is deleted (`cascade="all, delete-orphan"`).

2. **Project ➔ ApiKeys (`1 : N`)**
   - A single `Project` can have one or multiple `ApiKey`s.
   - Each `ApiKey` belongs strictly to **one** `Project`.
   - If a project is deleted, its keys are cascade-deleted (`cascade="all, delete-orphan"`).

3. **Project ➔ AI Tools (`1 : N`)**
   - A single `Project` can contain multiple `AITools`.
   - `Project.ai_tools` cascade-deletes all associated tools if the project is deleted (`cascade="all, delete-orphan"`).

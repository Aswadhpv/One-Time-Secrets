# One-Time Secrets Service

This repository contains a FastAPI-based service that allows storing confidential secrets which can be retrieved only once. After the first retrieval—or upon deletion—the secret becomes unavailable. All secrets are stored in an encrypted form and cached in memory with a minimum TTL of 5 minutes. Actions (create, retrieve, delete) are logged in a PostgreSQL database.

## Features

- **Create Secret**: `POST /secret`
  - **Request Body**: 
    - `secret` (string, required)
    - `passphrase` (string, optional)
    - `ttl_seconds` (number, optional; minimum 300 seconds)
  - **Response**: `{ "secret_key": "unique identifier" }`

- **Retrieve Secret**: `GET /secret/{secret_key}`
  - **Response**: `{ "secret": "confidential data" }`
  - The secret is returned only on the first request.

- **Delete Secret**: `DELETE /secret/{secret_key}`
  - **Response**: `{ "status": "secret_deleted" }`

- **PostgreSQL Logging**: All actions are logged.
- **Encryption**: Secrets are stored in encrypted form.
- **No Client Caching**: HTTP headers prevent client and proxy caching.

## Technologies Used

- **Python 3.9**
- **FastAPI**
- **PostgreSQL**
- **Docker & Docker Compose**
- **SQLAlchemy**
- **cryptography**

## Setup and Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/Aswadhpv/One-Time-Secrets.git
   cd one-time-secrets
   
2. **To access the swagger you can go to the link:**
   ```bash
    http://localhost:8000/docs 

# WrAFT (**Wr**iting **A**ssessment and **F**eedback **T**ool)

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

License: MIT

## Overview

WrAFT is an automated Writing Assessment and Feedback Tool built with Django and Vue.js. This project uses modern web technologies to provide automated writing assessment and feedback capabilities.

## Table of Contents

- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [User Management](#user-management)
- [Testing](#testing)
- [Deployment](#deployment)
- [Additional Resources](#additional-resources)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js and npm (for local frontend development)
- Python 3.8+ (for local backend development)

### Running with Docker

1. Copy and configure the secrets file:
```sh
cp ./envs/.local/.secrets.example ./envs/.local/.secrets
```

2. Start the development environment:
```sh
docker-compose -f docker-compose.local.yml up
```

3. Access the services:
- Frontend: http://localhost:5173/
- Backend Admin: http://localhost:8000/admin/
- Celery Dashboard: http://localhost:5555/
- Email Testing (Mailpit): http://localhost:8025/

### Running Frontend Locally

```sh
cd frontend
npm install
npm run dev
```

## Development Setup

### Initial Data Setup

Initialize the LLM configurations for local environment:

```sh
make init-data-local
```

The settings are defined in `config/settings/base.py`. For more details, check `backend/llm_caller/management/commands/init_llm_data.py`.

### Email Testing

The project uses Mailpit for email testing in development. When running with Docker, Mailpit is automatically available at http://localhost:8025. This allows you to:
- View all outgoing emails
- Test email verification flows
- Debug email-related features

## User Management

### Creating Users

1. **Normal User Account**:
   - Go to Sign Up and complete the registration form
   - Check Mailpit (http://localhost:8025) for verification email
   - Use the verification code to activate your account

2. **Superuser Account**:
   - Created automatically by Docker using credentials from `.envs/.local/.django`
   - Or create manually using:
     ```sh
     make csu-local
     ```

### LLM Testing Mode

To enable fake LLM responses for testing:

1. Visit http://localhost:8000/admin/llm_caller/llmsettings/
2. Add a new LLMSetting record
3. Set "Fake LLM request" to True
4. Configure example outputs in http://localhost:8000/admin/llm_caller/llmconfig/

## Testing

Run the test suite:

```sh
make pytest
```

## Deployment

### Production Build

For production deployment, the Vue frontend must be built into static resources. This is handled automatically in the Docker production configuration.

To build static assets:

```sh
make build-production
```

Start the production server:

```sh
make start-production
```

## Additional Resources

- [Vue3 Vite Django Project](https://github.com/ilikerobots/cookiecutter-vue-django)
- [Cookie Cutter Django Documentation](https://cookiecutter-django.readthedocs.io/)

## License

MIT

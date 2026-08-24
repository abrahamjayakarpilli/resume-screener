# Decision Record: FastAPI for Backend REST Layer

## Status
Approved

## Context
We need a high-performance Python web framework to serve the REST API endpoints, handle multi-file uploads, and coordinate background parser workers.

## Alternatives Considered
1. **Django / Django REST Framework**: Offers a full ORM and admin dashboard out of the box, but adds significant boilerplate, possesses slower request handling speeds, and is less suited for lightweight microservice architectures.
2. **Flask**: Minimalist and highly flexible, but lacks built-in asynchronous request handling (`async/await`) and Pydantic response/request serialization validation, requiring multiple external dependencies.
3. **FastAPI**: Modern, asynchronous, built on Starlette and Pydantic, offering automatic OpenAPI generation and excellent performance.

## Decision
We chose **FastAPI** because:
- **Asynchronous natively**: Native support for `async/await` and `BackgroundTasks` makes multi-resume background parsing simple to execute without requiring external queue setups.
- **Pydantic Validation**: Automatic schema validation of LLM outputs and JSON payloads.
- **OpenAPI Integration**: Out-of-the-box `/docs` interactive API playground reduces testing friction.
- **High Performance**: Ranks among the fastest Python frameworks available.

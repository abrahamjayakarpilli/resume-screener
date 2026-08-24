# Decision Record: SQLite for Local Persistence

## Status
Approved

## Context
The platform must store jobs, candidates, parsed details, and match results. The system must support instant developer setup without external infrastructure dependencies, yet be ready for multi-tenant production scaling.

## Alternatives Considered
1. **PostgreSQL**: Highly powerful relational database. Required for multi-tenant SaaS environments, but requires installation, environment setup, and credentials management, which raises barrier to entry for local testing and demos.
2. **MongoDB**: Document store. Fits nested candidate resumes, but makes complex tabular reports, analytical candidate comparisons, and structured job requirements mapping hard to query cleanly.
3. **SQLite**: Zero-config, serverless, local database storing data in a single file on the filesystem.

## Decision
We chose **SQLite** via **SQLAlchemy ORM** because:
- **Zero-Install Setup**: Runs immediately out of the box on any developer's machine with no PostgreSQL instance required.
- **ORM abstraction**: By defining our schema in SQLAlchemy, we write dialect-independent SQL. Migrating to PostgreSQL is a 1-line environment variable adjustment: `DATABASE_URL=postgresql://user:pass@host/db`.
- **ACID compliance**: Perfectly preserves relational integrity between jobs, matches, requirements, and candidates.

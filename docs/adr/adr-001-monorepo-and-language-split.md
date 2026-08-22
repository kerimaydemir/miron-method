# ADR-001: Monorepo and language split

- Status: Accepted
- Decision: Next.js/TypeScript UI and FastAPI/Python backend in a pnpm/Turborepo monorepo.
- Consequence: Transport contracts are generated and domain objects never depend on frontend or provider SDK types.
- Revisit trigger: Measured deployment or ownership cost makes coordinated releases materially unsafe.


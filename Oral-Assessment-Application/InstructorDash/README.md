# InstructorDash

The VivāVoce web front end — a React app where instructors create assignments,
schedule and review oral interviews, and view suggested grades, and where
students view and trigger their interviews.

Built with Create React App (React 19, react-router-dom 7, axios). Authentication
uses AWS Cognito via aws-amplify.

## Source layout (`src/`)

- `App.js` — top-level app, routing, and auth gating
- `pages/` — top-level pages (e.g. `Login.jsx`)
- `components/instructor/` — instructor dashboard components
- `components/student/` — student dashboard components
- `components/gradebook/` — gradebook / interview review components
- `hooks/` — shared React hooks (`useAuth.js`)
- `config/` — configuration (`awsConfig.js`)
- `styles/` — CSS

## Running locally

```bash
npm install
npm start
```

Opens at http://localhost:3000 with hot reload.

## Building

```bash
npm run build
```

Produces an optimised static build in `build/`.

## Deploying

The live site is a static build hosted on AWS S3 + CloudFront — not a git push.
See [DEPLOY.md](DEPLOY.md) for access and the `npm run deploy` workflow.

# API Reference

Base path: `/api/v1`. All routes except `/auth/*` and `/health*` require a
`Bearer` access token.

## Auth
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/auth/signup` | Register a recruiter |
| POST | `/auth/login` | Obtain access + refresh tokens |
| POST | `/auth/refresh` | Rotate refresh → new token pair |
| POST | `/auth/logout` | Revoke all refresh tokens |

## Users
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/users/me` | Current user |
| PUT | `/users/me` | Update profile |
| GET | `/users` | List users (admin) |
| PUT | `/users/{id}/role` | Change role (admin) |

## Jobs
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/jobs` | Create job (embeds JD in background) |
| GET | `/jobs` | List jobs (filter by `status`) |
| GET | `/jobs/{id}` | Job detail |
| PUT | `/jobs/{id}` | Update job |
| PATCH | `/jobs/{id}/status` | Change status |
| DELETE | `/jobs/{id}` | Archive (soft delete) |
| POST | `/jobs/{id}/rank` | Rank all completed candidates |

## Resumes
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/jobs/{job_id}/resumes` | Upload (multipart, batch) → 202 |
| GET | `/jobs/{job_id}/resumes` | List resumes for a job |
| GET | `/resumes/{id}` | Resume detail + parse status |
| DELETE | `/resumes/{id}` | Delete resume |

## Candidates
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/jobs/{job_id}/candidates` | Ranked candidates |
| GET | `/candidates/{id}` | Candidate profile |
| GET | `/jobs/{job_id}/candidates/{candidate_id}` | Scores + status for a job |
| PATCH | `/jobs/{job_id}/candidates/{candidate_id}/status` | Update status |
| PUT | `/jobs/{job_id}/candidates/{candidate_id}/notes` | Recruiter notes |

## Interview & Reports (SSE)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/jobs/{job_id}/candidates/{candidate_id}/questions` | Generate (SSE stream) |
| GET | `/jobs/{job_id}/candidates/{candidate_id}/questions` | Saved questions |
| POST | `/jobs/{job_id}/candidates/{candidate_id}/report` | Generate (SSE stream) |
| GET | `/jobs/{job_id}/candidates/{candidate_id}/report` | Saved report |
| GET | `/jobs/{job_id}/candidates/{candidate_id}/report/pdf` | Report PDF |

The SSE endpoints emit `start`, `progress`, `complete`, and `error` events. Use a
fetch-based reader (not `EventSource`) so the `Authorization` header is sent.

## Analytics
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/analytics/dashboard` | Counts, avg score, funnel |
| GET | `/analytics/jobs/{id}` | Per-job distribution + status breakdown |

## Tasks & Health
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/tasks/{id}` | Background task status |
| GET | `/health` | Liveness |
| GET | `/health/ready` | Readiness (DB check) |

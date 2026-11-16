---
title: Handoff — Interview Practice App
updated: 2026-11-16
sources:
  - DEPLOYMENT.md
  - 03_Sources/turing-college/interview-practice-app-brief-2026-11-16.md
tags:
  - handoff
  - github
  - turing-college
---

# Handoff

## Current state

- Project: `/mnt/knowledge/AIengin/06_Projects/interview-practice-app/`
- Private repo: `https://github.com/reallife-spark/interview_app`
- Pushed commit: `730a934` (`docs: add security, demo and deployment guides`)
- Course remote: `https://github.com/TuringCollegeSubmissions/rmobil-AE.1.5.git`
- Checks: 69 tests, Ruff 0, headless Streamlit HTTP 200, vault validation passes.
- Demo evaluation: 18 rows; `json_schema` ranks first in the offline fixture.

## Current blocker

`git ls-remote course` returns:

```text
remote: Write access to repository not granted.
fatal: unable to access 'https://github.com/TuringCollegeSubmissions/rmobil-AE.1.5.git/': The requested URL returned error: 403
```

`gh repo view TuringCollegeSubmissions/rmobil-AE.1.5` cannot resolve the
repository. The private `interview_app` repo is pushed, but the course mirror is
not. Do not push to a different account and do not force-push.

## User action: course repository

1. Open the Turing College LMS project page.
2. Click the GitHub icon for the project. The LMS should show the
   student-specific repository URL.
3. If the URL differs from `rmobil-AE.1.5`, update the `course` remote.
4. Authorize `TuringCollegeSubmissions` if the LMS asks.
5. Confirm the active GitHub account is the intended one:

   ```bash
   gh auth status
   gh api user --jq .login
   ```

6. Re-check access without writing:

   ```bash
   git ls-remote course
   ```

7. If the course repo has an initial commit:

   ```bash
   git fetch course
   git rebase course/main
   ```

   If the histories are unrelated, merge and resolve conflicts normally.

8. Push:

   ```bash
   git push -u course main
   ```

9. Refresh the course repository page and confirm the files are present.
10. Only then click **Submit Project** and schedule the review.

## If the course URL changes

```bash
git remote set-url course <new-course-url>
git ls-remote course
git push -u course main
```

## What not to do

- Do not read or echo `.env`.
- Do not commit `.env`, `.venv`, keys or tokens.
- Do not force-push.
- Do not push to the course repo before access is verified.
- Do not claim a public deployment or a completed review from this host.

## After the course push

- Update `DEPLOYMENT.md` and the LMS evidence with the actual course URL.
- Deploy to Streamlit Community Cloud with `OPENROUTER_API_KEY` in secrets.
- Add the `real-life.dev` project card.
- Submit and schedule the review.

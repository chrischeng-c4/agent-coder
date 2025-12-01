---
name: git-commit
description: Generate a conventional commit message based on changes.
---
# Git Commit Skill

## Instructions
1. Check the status of the repository using `git status`.
2. View the changes using `git diff` or `git diff --cached`.
3. Generate a commit message following the Conventional Commits specification:
   - `feat`: A new feature
   - `fix`: A bug fix
   - `docs`: Documentation only changes
   - `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc)
   - `refactor`: A code change that neither fixes a bug nor adds a feature
   - `perf`: A code change that improves performance
   - `test`: Adding missing tests or correcting existing tests
   - `chore`: Changes to the build process or auxiliary tools and libraries such as documentation generation
4. Propose the commit command to the user.

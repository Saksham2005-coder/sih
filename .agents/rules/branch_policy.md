# Git & Branching Policy (Single Main Branch Architecture)

1. **Single Working Branch**: `main` is the sole working branch for this entire project.
2. **Direct Implementation on Main**: All future phases (Phase 3 through Phase 6) are implemented directly on `main`.
3. **No Unrequested Feature Branches**: Do not create or switch to feature branches (e.g. `sih-26262` or others) for subsequent phases unless explicitly requested by the user.
4. **Phase Commits**: Each completed phase receives one meaningful, verified commit on `main`.
5. **Direct Remote Push**: Push completed phase commits directly to `origin/main`.
6. **No Premature Commits**: Never commit unfinished work as a completed phase.
7. **No History Rewrites**: Never force-push or rewrite existing commit history.
8. **Working Tree Safety**: Always inspect the working tree (`git status`) before starting and before committing a phase.
9. **Functionality Preservation**: Preserve the existing commit history and all current application functionality across all phases.
10. **Phase Gate Adherence**: Do not start subsequent phases until the preceding phase is fully consolidated, tested, and verified.

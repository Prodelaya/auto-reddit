# Archive Report: reddit-candidate-collection

## Result

- Archive date: 2026-03-27
- Archive mode: hybrid (openspec + engram)
- Final verification verdict: PASS
- Task completion: 21/21 complete
- Runtime evidence: 50 tests passed, 0 failed

## Source of Truth Sync

| Domain | Action | Details |
|--------|--------|---------|
| `reddit-candidate-collection` | Created main spec | No prior `openspec/specs/reddit-candidate-collection/spec.md` existed, so the delta spec was promoted as the initial source of truth. |

## Archived OpenSpec Artifacts

- `proposal.md`
- `specs/reddit-candidate-collection/spec.md`
- `design.md`
- `tasks.md`
- `verify-report.md`
- `state.yaml`
- `archive-report.md`

## Engram Lineage

| Artifact | Topic key | Observation ID |
|----------|-----------|----------------|
| Proposal | `sdd/reddit-candidate-collection/proposal` | 736 |
| Spec | `sdd/reddit-candidate-collection/spec` | 742 |
| Design | `sdd/reddit-candidate-collection/design` | 774 |
| Tasks | `sdd/reddit-candidate-collection/tasks` | 778 |
| Apply progress | `sdd/reddit-candidate-collection/apply-progress` | 795 |
| Verify report | `sdd/reddit-candidate-collection/verify-report` | 798 |

## Final Notes / Deltas

- OpenSpec artifacts are the authoritative final archive for this change.
- Engram proposal/spec memories (#736, #742) still preserve an earlier wording that referenced a downstream cut to 10 candidates; the finalized OpenSpec spec, tasks, design alignment, and verify evidence all reflect the corrected downstream cut to 8.
- The verification report recommends occasional smoke validation against live Reddit providers because pagination/cursor behavior is currently covered by mocks rather than live calls.
- `candidate-memory-and-uniqueness` is the direct downstream consumer of the normalized in-memory candidate list produced by this archived change.

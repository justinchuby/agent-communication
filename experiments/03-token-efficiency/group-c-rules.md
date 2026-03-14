# Group C Rules — AECP v2 (Scoped Views + Delta Re-reads)

## Protocol — Optimized for Token Efficiency
- Master blackboard: experiments/03-token-efficiency/blackboard-c.md (architect writes)
- Role-scoped views: blackboard-c-{deva,devb,reviewer,tester}.md
- Changelog: blackboard-c-changelog.md (for re-reads)
- Structured messages only: DONE(component), VERDICT(pass|fail), BUG(id, severity)
- Message budget: ≤5 per agent
- Silence = working

## Key Optimization: You NEVER re-read the full blackboard
- **First read**: Read ONLY your role-scoped view file
- **Re-reads**: Read ONLY the changelog (blackboard-c-changelog.md)
- If changelog mentions something you need in full, read that specific section from your scoped view

## Architect Workflow
1. Read task spec
2. Resolve all 8 ambiguities
3. Write full master blackboard (blackboard-c.md)
4. Generate 4 scoped view files:
   - blackboard-c-deva.md: Task header + types.py-relevant decisions + interface contract + Dev A's assignment row
   - blackboard-c-devb.md: Task header + emitter.py-relevant decisions + interface contract + Dev B's assignment row  
   - blackboard-c-reviewer.md: Task header + all decisions + interface contract + all assignments + findings
   - blackboard-c-tester.md: Task header + interface contract + assignment statuses only
5. Initialize changelog with v1 entry
6. Send DONE(design)

## Developer Workflow (Dev A and Dev B)
1. First read: your scoped view (blackboard-c-dev{a,b}.md)
2. Implement your assigned files
3. When done: update master blackboard status + append to changelog
4. Send DONE(component)
5. On re-reads: read ONLY changelog, not full blackboard

## Reviewer Workflow
1. First read: blackboard-c-reviewer.md
2. Read all code files
3. Post findings to master blackboard + changelog
4. Send VERDICT(pass|fail)

## Tester Workflow
1. First read: blackboard-c-tester.md
2. Read all code files
3. Write and run tests
4. Post results to master blackboard + changelog
5. Send VERDICT(pass|fail)

## Code Directory
experiments/03-token-efficiency/group-c-code/

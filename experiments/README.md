# AECP Experiments

Controlled experiments testing the Agent-Efficient Communication Protocol.

## Experiments

| # | Name | Type | Agents | Result |
|---|------|------|--------|--------|
| 00a | Bug Hunt | Live AECP test | 3 | 92% token reduction |
| 00b | 30-Agent Scale | Scalability test | 28 | 50 msgs for 28 agents (1.79/agent) |
| 01 | URL Shortener A/B | Controlled A/B | 10 | 77% message reduction, equal quality |
| 02 | Ambiguous Spec A/B | Controlled A/B | 10 | (pending) |

## Key Metrics
- RS (Readability Score): message quality
- CE (Communication Efficiency): task_success / messages_sent  
- CR (Coordination Residual): clarifications / tasks

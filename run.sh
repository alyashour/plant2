#/bin/bash -e

python leaderboard_autopilot/leaderboard/leaderboard_evaluator_local.py \
  --routes=leaderboard/data/longest6_split/longest6_00.xml \
  --track=MAP \
  --agent=PlanT/PlanT_agent.py \
  --checkpoint=results.json \
  --timeout=300

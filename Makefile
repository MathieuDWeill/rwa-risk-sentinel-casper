SHELL := /bin/bash

.PHONY: install setup test agent demo frontend zip clean

install:
	$(MAKE) setup

setup:
	python3.13 -m venv .venv
	source .venv/bin/activate && pip install -r agent/requirements.txt

test:
	source .venv/bin/activate && python -m pytest agent/tests -q

agent:
	source .venv/bin/activate && python -m agent.app.main

demo:
	source .venv/bin/activate && python scripts/run_demo_cycle.py --asset invoice-2026-001 --count 3

frontend:
	cd frontend && npm install && npm run dev

dev:
	source .venv/bin/activate && python -m agent.app.main & \
	PID=$$! ; \
	cd frontend && npm install && npm run dev ; \
	kill $$PID

zip:
	cd .. && zip -r casper-agentic-buildathon-repo.zip casper-agentic-buildathon-repo -x '*/node_modules/*' '*/.venv/*' '*/target/*' '*/.next/*' '*/evidence/*'

clean:
	rm -rf .venv frontend/node_modules frontend/.next contracts/rwa_risk_registry/target evidence

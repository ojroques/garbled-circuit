ALICE = python3 main.py alice  # circuit generator (client)
BOB = python3 main.py bob      # circuit evaluator (server)
LOCAL = python3 main.py local  # local tests
ONEFILE = ${ALICE}             # choose ALICE or LOCAL

default:
	@echo 'Usage 1: make {alice, bob, local}'
	@echo 'Usage 2: make {circuit}'

clean:
	rm -rf __pycache__

alice:
	${ALICE} -c circuits/add.json
	${ALICE} -c circuits/bool.json
	${ALICE} -c circuits/cmp.json
	${ALICE} -c circuits/max.json
	${ALICE} -c circuits/million.json
	${ALICE} -c circuits/min.json
	${ALICE} -c circuits/nand.json
	${ALICE} -c circuits/smart.json


bob:
	${BOB}

local:
	${LOCAL} -c circuits/add.json
	${LOCAL} -c circuits/bool.json
	${LOCAL} -c circuits/cmp.json
	${LOCAL} -c circuits/max.json
	${LOCAL} -c circuits/million.json
	${LOCAL} -c circuits/min.json
	${LOCAL} -c circuits/nand.json

add:
	${ONEFILE} -c circuits/add.json

bool:
	${ONEFILE} -c circuits/bool.json

cmp:
	${ONEFILE} -c circuits/cmp.json

max:
	${ONEFILE} -c circuits/max.json

million:
	${ONEFILE} -c circuits/million.json

min:
	${ONEFILE} -c circuits/min.json

nand:
	${ONEFILE} -c circuits/nand.json

rich:
	${ONEFILE} -c circuits/rich.json

smart:
	${ONEFILE} -c circuits/smart.json


# yao garbled circuit evaluation v1. simple version based on smart
# naranker dulay, dept of computing, imperial college, october 2018

ALICE   = python3 main.py alice	# circuit generator (client)
BOB     = python3 main.py bob	# circuit evaluator (server)
LOCAL   = python3 main.py local	# local, not client-server, no transfers
ONEFILE	= ${ALICE}		# test 1 file, choose ALICE or LOCAL

default:
	@echo '  >> make {alice, bob, local}'

clean:
	rm -rf __pycache__ .mypy_cache

main.py: yao.py ot.py util.py
yao.py: util.py crypto.py
ot.py:	util.py

alice:	main.py
	${ALICE} json/f.bool.json
	${ALICE} json/f.nand.json
	${ALICE} json/f.add.json
	${ALICE} json/f.cmp.json
	${ALICE} json/f.max.json
	${ALICE} json/f.min.json
	${ALICE} json/f.smart.json

bob:	main.py
	${BOB}

local:	main.py
	${LOCAL} json/f.bool.json
	${LOCAL} json/f.nand.json
	${LOCAL} json/f.add.json
	${LOCAL} json/f.cmp.json
	${LOCAL} json/f.max.json
	${LOCAL} json/f.min.json
	${LOCAL} json/f.smart.json
     
bool:	main.py
	${ONEFILE} json/f.bool.json

nand:	main.py
	${ONEFILE} json/f.nand.json

add:	main.py
	${ONEFILE} json/f.add.json

cmp:	main.py
	${ONEFILE} json/f.cmp.json

max:	main.py
	${ONEFILE} json/f.max.json

min:	main.py
	${ONEFILE} json/f.min.json

rich:   main.py
	$(ONEFILE) json/f.rich.json

smart:	main.py
	${ONEFILE} json/f.smart.json

million:main.py
	${ONEFILE} json/f.million.json

test:	main.py
	${ONEFILE} json/f.test.json



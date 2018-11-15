"""
Emmanuelle Risson : ear
Olivier Roques    : or518
"""

# yao garbled circuit evaluation v1. simple version based on smart
# naranker dulay, dept of computing, imperial college, october 2018

import json	# load
import sys	# argv

import util	# ClientSocket, log, ServerSocket
import ot	# alice, bob
import yao	# Circuit

import garble as gb

# Alice is the circuit generator (client) __________________________________

def alice(filename):
    socket = util.ClientSocket()

    with open(filename) as json_file:
        json_circuits = json.load(json_file)

    for json_circuit in json_circuits['circuits']:
        outputs   = json_circuit["out"]
        g_circuit = gb.GarbledCircuit(json_circuit)
        g_tables  = g_circuit.get_garbled_tables()
        keys      = g_circuit.get_keys()
        pbits     = g_circuit.get_pbits()
        print_evaluation(json_circuit, g_tables, keys, pbits)
    print()

def print_evaluation(circuit, g_tables, keys, pbits):
    outputs   = circuit["out"]
    a_wires   = circuit.get("alice", [])
    b_wires   = circuit.get("bob", [])
    a_inputs  = {}
    b_inputs  = {}
    pbits_out = {w: pbits[w] for w in outputs}

    print("\n======= {0} =======".format(circuit["name"]))

    len_a_wires, len_b_wires = len(a_wires), len(b_wires)
    N = len_a_wires + len_b_wires

    for bits in [format(n, 'b').zfill(N) for n in range(2**N)]:
        bits_a = [int(b) for b in bits[:len_a_wires]]
        bits_b = [int(b) for b in bits[len_a_wires:]]

        for i in range(len_a_wires):
            a_inputs[a_wires[i]] = \
                (keys[(a_wires[i], bits_a[i])], pbits[a_wires[i]] ^ bits_a[i])
        for i in range(len_b_wires):
            # TODO: retrieve bob's keys instead
            b_inputs[b_wires[i]] = \
                (keys[(b_wires[i], bits_b[i])], pbits[b_wires[i]] ^ bits_b[i])

        # TODO: evaluation is on Bob's side
        evaluation = gb.evaluate(circuit, g_tables, pbits_out, a_inputs, b_inputs)

        str_bits_a     = ' '.join(bits[:len_a_wires]) + ' '*bool(len_a_wires)
        str_bits_b     = ' '.join(bits[len_a_wires:]) + ' '*bool(len_b_wires)
        str_evaluation = ' '.join([str(v) for v in evaluation.values()]) + ' '
        line           = "  Alice{0} = {1} Bob{2} = {3}  Outputs{4} = {5}".\
            format(a_wires, str_bits_a, b_wires, str_bits_b, \
                   outputs, str_evaluation)
        print(line)

# Bob is the circuit evaluator (server) ____________________________________

def bob():
    socket = util.ServerSocket()
    util.log(f'Bob: Listening ...')
    while True:
        pass

# local test of circuit generation and evaluation, no transfers_____________

def local_test(filename):
    with open(filename) as json_file:
        json_circuits = json.load(json_file)

    for json_circuit in json_circuits['circuits']:
        pass

# main _____________________________________________________________________

def main():
    behaviour = sys.argv[1]
    if   behaviour == 'alice': alice(filename=sys.argv[2])
    elif behaviour == 'bob':   bob()
    elif behaviour == 'local': local_test(filename=sys.argv[2])

if __name__ == '__main__':
    main()

# __________________________________________________________________________

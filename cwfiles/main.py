"""
Emmanuelle Risson : ear
Olivier Roques    : or518
"""

# yao garbled circuit evaluation v1. simple version based on smart
# naranker dulay, dept of computing, imperial college, october 2018

import json         # load
import sys          # argv

import util         # ClientSocket, log, ServerSocket
import ot           # alice, bob
import yao          # Circuit

# Alice is the circuit generator (client) __________________________________

def alice(filename):
    socket = util.ClientSocket()
    util.log('CLIENT STARTED')

    with open(filename) as json_file:
        json_circuits = json.load(json_file)

    for json_circuit in json_circuits['circuits']:
        g_circuit = yao.GarbledCircuit(json_circuit)
        g_tables  = g_circuit.get_garbled_tables()
        keys      = g_circuit.get_keys()
        pbits     = g_circuit.get_pbits()
        pbits_out = {w: pbits[w] for w in json_circuit["out"]}
        util.log('Sending yao circuit...')
        ot.send_yao_circuit(socket, json_circuit, g_tables, pbits_out)
        util.log('Waiting for circuit evaluation...')
        print_evaluation(socket, json_circuit, keys, pbits)
        util.log('Done.\n')
    print()

def print_evaluation(socket, circuit, keys, pbits):
    outputs   = circuit["out"]
    a_wires   = circuit.get("alice", [])
    a_inputs  = {}
    b_wires   = circuit.get("bob", [])
    b_keys    = {(w, bit): (key, bit ^ pbits[w])\
                 for (w, bit), key in keys.items() if w in b_wires}

    print("\n======= {0} =======".format(circuit["name"]))

    len_a_wires, len_b_wires = len(a_wires), len(b_wires)
    N = len_a_wires + len_b_wires

    for bits in [format(n, 'b').zfill(N) for n in range(2**N)]:
        bits_a = [int(b) for b in bits[:len_a_wires]]
        bits_b = [int(b) for b in bits[len_a_wires:]]

        for i in range(len_a_wires):
            a_inputs[a_wires[i]] = \
                (keys[(a_wires[i], bits_a[i])], pbits[a_wires[i]] ^ bits_a[i])

        result = ot.get_result(socket, a_inputs, b_keys)

        str_bits_a = ' '.join(bits[:len_a_wires]) + ' '*bool(len_a_wires)
        str_bits_b = ' '.join(bits[len_a_wires:]) + ' '*bool(len_b_wires)
        str_result = ' '.join([str(result[w]) for w in outputs]) + ' '
        line       = "  Alice{0} = {1} Bob{2} = {3}  Outputs{4} = {5}".\
            format(a_wires, str_bits_a, b_wires, str_bits_b, \
                   outputs, str_result)
        print(line)


# Bob is the circuit evaluator (server) ____________________________________

def bob():
    socket = util.ServerSocket()
    util.log(f'SERVER STARTED')

    while True:
        util.log('Waiting for yao circuit...')
        circuit, g_tables, pbits_out = ot.receive_yao_circuit(socket)
        util.log('Sending circuit evaluation...')
        send_evaluation(socket, circuit, g_tables, pbits_out)
        util.log('Done.\n')

def send_evaluation(socket, circuit, g_tables, pbits_out):
    outputs   = circuit["out"]
    a_wires   = circuit.get("alice", [])
    b_wires   = circuit.get("bob", [])

    len_a_wires, len_b_wires = len(a_wires), len(b_wires)
    N = len_a_wires + len_b_wires

    for bits in [format(n, 'b').zfill(N) for n in range(2**N)]:
        bits_a = [int(b) for b in bits[:len_a_wires]]
        bits_b = [int(b) for b in bits[len_a_wires:]]

        b_inputs_clear = {b_wires[i]: bits_b[i] for i in range(len_b_wires)}
        ot.send_result(socket, circuit, g_tables, pbits_out, b_inputs_clear)


# local test of circuit generation and evaluation, no transfers_____________

def local_test(filename):
    with open(filename) as json_file:
        json_circuits = json.load(json_file)

    for json_circuit in json_circuits['circuits']:
        g_circuit = yao.GarbledCircuit(json_circuit)
        g_tables  = g_circuit.get_garbled_tables()
        keys      = g_circuit.get_keys()
        pbits     = g_circuit.get_pbits()
        print_evaluation_local(json_circuit, g_tables, keys, pbits)

def print_evaluation_local(circuit, g_tables, keys, pbits):
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
            b_inputs[b_wires[i]] = \
                (keys[(b_wires[i], bits_b[i])], pbits[b_wires[i]] ^ bits_b[i])

        result = yao.evaluate(circuit, g_tables, pbits_out, a_inputs, b_inputs)

        str_bits_a = ' '.join(bits[:len_a_wires]) + ' '*bool(len_a_wires)
        str_bits_b = ' '.join(bits[len_a_wires:]) + ' '*bool(len_b_wires)
        str_result = ' '.join([str(result[w]) for w in outputs]) + ' '
        line       = "  Alice{0} = {1} Bob{2} = {3}  Outputs{4} = {5}".\
            format(a_wires, str_bits_a, b_wires, str_bits_b, \
                   outputs, str_result)
        print(line)

# main _____________________________________________________________________

def main():
    behaviour = sys.argv[1]
    if   behaviour == 'alice': alice(filename=sys.argv[2])
    elif behaviour == 'bob':   bob()
    elif behaviour == 'local': local_test(filename=sys.argv[2])

if __name__ == '__main__':
    main()

# __________________________________________________________________________

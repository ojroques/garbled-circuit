"""
Emmanuelle Risson : ear3218
Olivier Roques    : or518
"""

# yao garbled circuit evaluation v1. simple version based on smart
# naranker dulay, dept of computing, imperial college, october 2018

import random
import pickle
from cryptography.fernet import Fernet

def encrypt(key, data):
    f = Fernet(key)
    return f.encrypt(data)

def decrypt(key, data):
    f = Fernet(key)
    return f.decrypt(data)

def evaluate(circuit, garbled_table, pbits_out, a_inputs, b_inputs={}):
    gates        = circuit["gates"]
    wire_outputs = circuit["out"]
    wire_inputs  = {}
    evaluation   = {}

    wire_inputs.update(a_inputs)
    wire_inputs.update(b_inputs)

    for gate in sorted(gates, key=lambda g: g["id"]):
        gate_id, gate_in, msg = gate["id"], gate["in"], None
        if (len(gate_in) < 2) and (gate_in[0] in wire_inputs):
            key_in, encr_bit_in = wire_inputs[gate_in[0]]
            encr_msg            = garbled_table[gate_id][(encr_bit_in, )]
            msg                 = decrypt(key_in, encr_msg)
        elif (gate_in[0] in wire_inputs) and (gate_in[1] in wire_inputs):
            key_a, encr_bit_a = wire_inputs[gate_in[0]]
            key_b, encr_bit_b = wire_inputs[gate_in[1]]
            encr_msg          = garbled_table[gate_id][(encr_bit_a, encr_bit_b)]
            msg               = decrypt(key_b, decrypt(key_a, encr_msg))
        if msg: wire_inputs[gate_id] = pickle.loads(msg)

    for out in wire_outputs:
        evaluation[out] = wire_inputs[out][1] ^ pbits_out[out]

    return evaluation


class GarbledGate:
    """A representation of a garbled gate."""

    def __init__(self, gate, keys, pbits):
        self.keys                = keys
        self.pbits               = pbits
        self.input               = gate["in"]
        self.output              = gate["id"]
        self.gate_type           = gate["type"]
        self.garbled_table       = {}
        self.clear_garbled_table = {}

        switch = {
            "OR"   : lambda b1, b2: b1 or b2,
            "AND"  : lambda b1, b2: b1 and b2,
            "XOR"  : lambda b1, b2: b1 ^ b2,
            "NOR"  : lambda b1, b2: not(b1 or b2),
            "NAND" : lambda b1, b2: not(b1 and b2),
            "XNOR" : lambda b1, b2: not(b1 ^ b2)
        }

        if (self.gate_type == "NOT"):
            self._gen_not_garbled_table()
        else:
            operator = switch[self.gate_type]
            self._gen_garbled_table(operator)

    def _gen_not_garbled_table(self):
        inp, out = self.input[0], self.output

        for encr_bit_in in (0, 1):
            bit_in        = encr_bit_in ^ self.pbits[inp]
            bit_out       = int(not(bit_in))
            encr_bit_out  = bit_out ^ self.pbits[out]
            key_in        = self.keys[(inp, bit_in)]
            key_out       = self.keys[(out, bit_out)]

            self.clear_garbled_table[(encr_bit_in, )] = \
                [(inp, bit_in), (out, bit_out), encr_bit_out]
            msg = pickle.dumps((key_out, encr_bit_out))
            self.garbled_table[(encr_bit_in, )] = encrypt(key_in, msg)

    def _gen_garbled_table(self, operator):
        in_a, in_b, out = self.input[0], self.input[1], self.output

        for encr_bit_a in (0, 1):
            for encr_bit_b in (0, 1):
                bit_a         = encr_bit_a ^ self.pbits[in_a]
                bit_b         = encr_bit_b ^ self.pbits[in_b]
                bit_out       = int(operator(bit_a, bit_b))
                encr_bit_out  = bit_out ^ self.pbits[out]
                key_a         = self.keys[(in_a, bit_a)]
                key_b         = self.keys[(in_b, bit_b)]
                key_out       = self.keys[(out, bit_out)]

                self.clear_garbled_table[(encr_bit_a, encr_bit_b)] = \
                    [(in_a, bit_a), (in_b, bit_b), (out, bit_out), encr_bit_out]
                msg = pickle.dumps((key_out, encr_bit_out))
                self.garbled_table[(encr_bit_a, encr_bit_b)] = \
                    encrypt(key_a, encrypt(key_b, msg))

    def print_garbled_table(self):
        print("GATE: {0}, TYPE: {1}".format(self.output, self.gate_type))
        for k, v in self.clear_garbled_table.items():
            if len(k) > 1:
                key_a        = v[0]
                key_b        = v[1]
                key_out      = v[2]
                encr_bit_out = v[3]
                print("[{0}, {1}]: [{2}, {3}][{4}, {5}]([{6}, {7}], {8})".\
                      format(k[0], k[1], key_a[0], key_a[1], key_b[0], \
                             key_b[1], key_out[0], key_out[1], encr_bit_out))
            else:
                key_in       = v[0]
                key_out      = v[1]
                encr_bit_out = v[2]
                print("[{0}]: [{1}, {2}]([{3}, {4}], {5})".\
                      format(k[0], key_in[0], key_in[1], key_out[0], \
                             key_out[1], encr_bit_out))

    def get_garbled_table(self):
        return self.garbled_table


class GarbledCircuit:
    """A representation of a garbled circuit."""

    def __init__(self, circuit, pbits = {}):
        self.circuit        = circuit
        self.gates          = circuit["gates"]
        self.wires          = set()

        self.pbits          = {}
        self.keys           = {}
        self.garbled_tables = {}

        for gate in self.gates:
            self.wires.add(gate["id"])
            self.wires.update(set(gate["in"]))
        self.wires = list(self.wires)

        self._gen_pbits(pbits)
        self._gen_keys()
        self._gen_garbled_tables()

    def _gen_pbits(self, pbits):
        if pbits:
            self.pbits = pbits
        else:
            self.pbits = {wire:random.randint(0, 1) for wire in self.wires}

    def _gen_keys(self):
        for wire in self.wires:
            self.keys[(wire, 0)] = Fernet.generate_key()
            self.keys[(wire, 1)] = Fernet.generate_key()

    def _gen_garbled_tables(self):
        for gate in self.gates:
            garbled_gate = GarbledGate(gate, self.keys, self.pbits)
            self.garbled_tables[gate["id"]] = garbled_gate.get_garbled_table()

    def print_garbled_tables(self):
        print("NAME: {0}".format(self.circuit["name"]))
        print("PBITS:".format(self.pbits))
        for wire, pbit in self.pbits.items():
            print("* {0}: {1}".format(wire, pbit))
        print()

        for gate in self.gates:
            garbled_table = GarbledGate(gate, self.keys, self.pbits)
            garbled_table.print_garbled_table()
            print()

    def get_pbits(self):
        return self.pbits

    def get_garbled_tables(self):
        return self.garbled_tables

    def get_keys(self):
        return self.keys

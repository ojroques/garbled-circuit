"""
Emmanuelle Risson : ear3218
Olivier Roques    : or518

yao garbled circuit evaluation v1. simple version based on smart
naranker dulay, dept of computing, imperial college, october 2018
"""

import util
import yao
import pickle

# yao garbled circuit evaluation v1. simple version based on smart
# naranker dulay, dept of computing, imperial college, october 2018

OBLIVIOUS_TRANSFERS = True

# YAO PROTOCOL WITH OBLIVIOUS TRANSFER
if OBLIVIOUS_TRANSFERS: # __________________________________________________

    def get_result(socket, a_inputs, b_keys):
        """Send Alice's inputs and retrieve Bob's result of evaluation.

        Keyword arguments:
        socket   -- socket for exchanges between A and B
        a_inputs -- dict mapping Alice's wires to (key, encr_bit) inputs
        b_keys   -- dict mapping each Bob's wire to a pair (key, encr_bit)

        Returns
        result -- received result of the yao circuit evaluation
        """
        socket.send(a_inputs)

        for _ in range(len(b_keys)):
            # Receive the gate ID on which to perform OT
            w = socket.receive()
            # Perform oblivious transfer
            util.log('OT Request received')
            pair = (pickle.dumps(b_keys[w][0]), pickle.dumps(b_keys[w][1]))
            ot_alice(socket, pair)

        result = socket.receive()
        return result

    def ot_alice(socket, msgs):
        """Oblivious transfer, Alice's side.

        Keyword arguments:
        socket -- socket for exchanges between A and B
        msgs   -- a pair (msg1, msg2) to suggest to Bob
        """
        G = util.PrimeGroup()
        socket.send(G)
        socket.receive()
        c = G.gen_pow(G.rand_int())
        socket.send(c)
        h0 = socket.receive()
        h1 = G.mul(c, G.inv(h0))
        k = G.rand_int()
        c1 = G.gen_pow(k)
        e_0 = util.xor_bytes(msgs[0], util.ot_hash(G.pow(h0, k),len(msgs[0])))
        e_1 = util.xor_bytes(msgs[1], util.ot_hash(G.pow(h1, k),len(msgs[1])))
        to_send = (c1, e_0, e_1)
        socket.send(to_send)

    def send_result(socket, circuit, g_tables, pbits_out, b_inputs):
        """Evaluate circuit and send the result to Alice.

        Keyword arguments:
        socket    -- socket for exchanges between A and B
        circuit   -- dict containing circuit spec
        g_tables  -- garbled tables of yao circuit
        pbits_out -- p-bits of outputs
        b_inputs  -- dict mapping Bob's wires to (clear) input bits
        """
        # dict mapping Alice's wires to (key, encr_bit) inputs
        a_inputs      = socket.receive()
        # dict mapping Bob's wires to (key, encr_bit) inputs
        b_inputs_encr = {}

        for w, b_input in b_inputs.items():
            # Send the gate ID on which to perform OT
            socket.send(w)
            # Perform oblivious transfer
            util.log('OT Request sent')
            b_inputs_encr[w] = pickle.loads(ot_bob(socket, b_input))

        # Evaluate circuit using Alice and Bob's inputs
        result = yao.evaluate(circuit, g_tables, pbits_out, \
                              a_inputs, b_inputs_encr)
        socket.send(result)

    def ot_bob(socket, b):
        """Oblivious transfer, Bob's side.

        Keyword arguments:
        socket -- socket for exchanges between A and B
        b      -- Bob's input bit used to select one of Alice's messages

        Returns:
        msg -- the message selected by Bob
        """
        G = socket.receive()
        socket.send(True)
        c = socket.receive()
        x = G.rand_int()
        hb = G.gen_pow(x)
        h1_b = G.mul(c, G.inv(hb))
        if b==0:
            h = [hb, h1_b]
        elif b==1:
            h = [h1_b, hb]
        else:
            print('Error in b (neither 0 nor 1) in first if condition')
            return
        socket.send(h[0])
        being_received = socket.receive()
        c1 = being_received[0]
        e_0 = being_received[1]
        e_1 = being_received[2]
        if b==0:
            mb = util.xor_bytes(e_0, util.ot_hash(G.pow(c1, x),len(e_0)))
        elif b==1:
            mb = util.xor_bytes(e_1, util.ot_hash(G.pow(c1, x),len(e_1)))
        else:
            print('Error in b (neither 0 nor 1) in second if condition')
            return
        return mb

# YAO PROTOCOL WITHOUT OBLIVIOUS TRANSFER -- FOR LOCAL TESTS
else: # ____________________________________________________________________

    def get_result(socket, a_inputs, b_keys):
        socket.send(a_inputs)

        for _ in range(len(b_keys)):
            w = socket.receive()
            pair = (b_keys[w][0], b_keys[w][1])
            # The pair of keys is directly sent to Bob
            socket.send(pair)

        result = socket.receive()
        return result

    def send_result(socket, circuit, g_tables, pbits_out, b_inputs):
        a_inputs      = socket.receive()
        b_inputs_encr = {}

        for w, b_input in b_inputs.items():
            socket.send(w)
            pair = socket.receive()
            # Bob receives the pair of keys and choose one of them
            b_inputs_encr[w] = pair[b_input]

        result = yao.evaluate(circuit, g_tables, pbits_out, \
                              a_inputs, b_inputs_encr)
        socket.send(result)

# __________________________________________________________________________

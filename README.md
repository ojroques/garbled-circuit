# Secure Multi-Party Computation

## Contents

## Introduction
This project implements a [two-party secure function evaluation](https://en.wikipedia.org/wiki/Secure_two-party_computation) using Yao's [garbled circuit](https://en.wikipedia.org/wiki/Garbled_circuit) protocol. It has been developed on November 2018 for the Privacy Engineering course of Imperial College London (CO408). 

In our model, two parties Alice and Bob compute a function on their inputs without sharing the value of their inputs with the opposing party. Alice is the circuit creator while Bob is the circuit evaluator: Alice creates the yao circuit and sends it to Bob along with her encrypted inputs. Bob then computes the results and sends them back to Alice.

## Installation
Code is written in **Python 3+**. Dependencies are:
* **ZeroMQ** for communications: `pip3 install pyzmq`
* **Fernet** for encryption of garbled tables: `pip3 install cryptography`
* **SymPy** for prime number manipulation: `pip3 install sympy`

Clone this repository wherever you want and follow the instructions in the next section.

## Usage

#### Over the network
1. Replace network info with your own in `util.py`
2. Make sure `OBLIVIOUS_TRANSFERS` is set to `True` in `ot.py`.
3. Run the server (Bob):
```sh
make bob
```
4. Run the client with the path of the json circuit as argument:
```sh
make alice <json_circuit>
```

You can also run:
```sh
make alice
```
to evaluate all basic circuits present in `json/`.

Alice will print the truth table of the circuit for all combination of Alice-Bob inputs. Alice does not know Bob's inputs but for the purpose of printing the truth table only, Alice assumes that Bob's inputs follow a specific order.

#### Local tests
1. To print the truth table of a circuit, set `PRINT_MODE` to `0` in `main.py`
2. To print a clear representation of the garbled tables of a circuit, set `PRINT_MODE` to `1` in `main.py`
3. Run:
```sh
python3 main.py local <json_circuit>
```

## Architecture
The project is composed of 4 python files:
* `main.py`: implements Alice side, Bob side and local tests.
* `yao.py`: implements:
    * Encryption and decryption functions
    * Evaluation function used by Bob to get the results of a yao circuit
    * `GarbledCircuit` which generates the keys, p-bits and garbled gates of the circuit
    * `GarbledGate` which generates the garbled table of a gate
* `ot.py`: implements the oblivious transfer protocol as well as wrappers to send and receive yao circuit, inputs and results.
* `util.py`: implements many functions related to network communications and asymmetric key generation

A `Makefile` is present to make execution easier. A few basic function converted into boolean circuits are given as examples in `json/`.

## JSON Circuit
A function is represented as a boolean circuit using the gates available:
* NOT (1-input gate)
* AND
* OR
* XOR
* NAND
* NOR
* NXOR

A few assumptions are made:
* Bob knows the boolean representation of the function. Thus we respect the principle of "No security through obscurity".
* All gates have one or two inputs and only one output.
* The outputs of lower numbered gates will always be wired to higher numbered gates and/or be defined as circuit outputs.
* The gate id is the id of the gate's output.

Here is an example of a function represented as a json circuit:
```json
{ 
    "circuits" : [
        {
            "name"  : "Example circuit",
            "alice" : [1, 2],
            "bob"   : [3, 4],
            "out"   : [7],
            "gates" : [
                {"id" : 5, "type" : "AND", "in" : [1, 3]},
                {"id" : 6, "type" : "XOR", "in" : [2, 4]},
                {"id" : 7, "type" : "OR",  "in" : [5, 6]}
            ]
        }
    ]
}
```

## Example
Here is the truth table given by `python3 main.py local json/test.json` where `test.json` is the previous json circuit:
```sh
======= Example circuit =======
  Alice[1, 2] = 0 0  Bob[3, 4] = 0 0   Outputs[7] = 0
  Alice[1, 2] = 0 0  Bob[3, 4] = 0 1   Outputs[7] = 1
  Alice[1, 2] = 0 0  Bob[3, 4] = 1 0   Outputs[7] = 0
  Alice[1, 2] = 0 0  Bob[3, 4] = 1 1   Outputs[7] = 1
  Alice[1, 2] = 0 1  Bob[3, 4] = 0 0   Outputs[7] = 1
  Alice[1, 2] = 0 1  Bob[3, 4] = 0 1   Outputs[7] = 0
  Alice[1, 2] = 0 1  Bob[3, 4] = 1 0   Outputs[7] = 1
  Alice[1, 2] = 0 1  Bob[3, 4] = 1 1   Outputs[7] = 0
  Alice[1, 2] = 1 0  Bob[3, 4] = 0 0   Outputs[7] = 0
  Alice[1, 2] = 1 0  Bob[3, 4] = 0 1   Outputs[7] = 1
  Alice[1, 2] = 1 0  Bob[3, 4] = 1 0   Outputs[7] = 1
  Alice[1, 2] = 1 0  Bob[3, 4] = 1 1   Outputs[7] = 1
  Alice[1, 2] = 1 1  Bob[3, 4] = 0 0   Outputs[7] = 1
  Alice[1, 2] = 1 1  Bob[3, 4] = 0 1   Outputs[7] = 0
  Alice[1, 2] = 1 1  Bob[3, 4] = 1 0   Outputs[7] = 1
  Alice[1, 2] = 1 1  Bob[3, 4] = 1 1   Outputs[7] = 1
```

And here is the clear representation of the garbled gates (`PRINT_MODE` set to `1`):
```
NAME: Example circuit
P-BITS:
* 1: 0
* 2: 1
* 3: 0
* 4: 0
* 5: 1
* 6: 1
* 7: 0

GATE: 5, TYPE: AND
[0, 0]: [1, 0][3, 0]([5, 0], 1)
[0, 1]: [1, 0][3, 1]([5, 0], 1)
[1, 0]: [1, 1][3, 0]([5, 0], 1)
[1, 1]: [1, 1][3, 1]([5, 1], 0)

GATE: 6, TYPE: XOR
[0, 0]: [2, 1][4, 0]([6, 1], 0)
[0, 1]: [2, 1][4, 1]([6, 0], 1)
[1, 0]: [2, 0][4, 0]([6, 0], 1)
[1, 1]: [2, 0][4, 1]([6, 1], 0)

GATE: 7, TYPE: OR
[0, 0]: [5, 1][6, 1]([7, 1], 1)
[0, 1]: [5, 1][6, 0]([7, 1], 1)
[1, 0]: [5, 0][6, 1]([7, 1], 1)
[1, 1]: [5, 0][6, 0]([7, 0], 0)
```

## Authors
* Olivier Roques: or518@imperial.ac.uk
* Emmanuelle Risson: ear3218@imperial.ac.uk

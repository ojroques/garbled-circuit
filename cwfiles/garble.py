from cryptography.fernet import Fernet

class GarbledTable:
    """A representation of a garbled table."""

    def __init__(self, gate, pbits):
        self.garbtable = {}
        self.keys      = {}
        self.pbits     = pbits
        self.input     = gate["in"]
        self.output    = gate["id"]
        gateType       = gate["type"]

        switch = {
            "NOT"  : garbledNOT,
            "OR"   : garbledOR,
            "AND"  : garbledAND,
            "XOR"  : garbledXOR,
            "NOR"  : garbledNOR,
            "NAND" : garbledNAND,
            "XNOR" : garbledXNOR
        }
        garbledGATE = switch.get(gateType, "Invalid gate")
        garbledGATE()

    def generateKeys():
        for ids in self.input + self.output:
            self.keys[(ids, 0)] = Fernet.generate_key()
            self.keys[(ids, 1)] = Fernet.generate_key()

    def garbledAND():
        pass

    def getGarbledTable(self):
        return self.garbtable

    def getKeys(self):
        return self.keys

class GarbledCircuit:
    """A representation of a garbled circuit."""

    def __init__(self, circuit):
        self.pbits = []

    def getPbits(self):
        return self.pbits

from pymodbus.datastore import ModbusBaseSlaveContext

class JSONModbusSlaveContext(ModbusBaseSlaveContext):
    def read_defs_from_json_and_dump(self, dump_file):
        res = {}
        for i, d in enumerate(dump_file.readlines()):
            if not d.strip() == 'None':
                res[i] = int(d)

        return res
        
    def __init__(self, input_dump, holding_dump):
        with open(input_dump) as dump:
            self.input_regs = self.read_defs_from_json_and_dump(dump)
        with open(holding_dump) as dump:
            self.holding_regs = self.read_defs_from_json_and_dump(dump)

    def validate(self, fc_as_hex, address, count=1):
        if(fc_as_hex == 4):
            for i in range(count):
                if not address + i in self.input_regs:
                    return False
            return True
        if(fc_as_hex == 3):
            for i in range(count):
                if not address + i in self.holding_regs:
                    return False
            return True

    def getValues(self, fc_as_hex, address, count=1):
        if(fc_as_hex == 4):
            res = [self.input_regs[address + i] for i in range(count)]
            return res
        if(fc_as_hex == 3):
            res = [self.holding_regs[address + i] for i in range(count)]
            return res

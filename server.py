import argparse
import yaml
import asyncio
import subprocess
import os
from pymodbus.server import StartAsyncTcpServer, StartAsyncSerialServer
from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext
from JSONModbusSlaveContext import JSONModbusSlaveContext

parser = argparse.ArgumentParser(prog='pyModbus testing server',
                    description='Expose modbus server with test values')

parser.add_argument("-c", "--config", type=argparse.FileType('r'), required=True)

args = parser.parse_args()

conf = yaml.load(args.config, Loader = yaml.Loader)

def start_server(conf):
    slavectx = JSONModbusSlaveContext(conf["input_dump"], conf["holding_dump"])
    ctx = ModbusServerContext(slaves=slavectx, single=True)
    if isinstance(conf["port"], int):
        print(f"Starting tcp server on {conf['port']}")
        return StartAsyncTcpServer(context = ctx, framer = "socket", identity = {}, address = ["0.0.0.0", conf['port']])
    else:
        print(f"Starting serial server on {conf['port']}")

        subprocess.Popen(["/usr/bin/socat", f"pty,raw,echo=0,link={conf["port"]}_master,group={conf["groupid"]},mode=660", f"pty,raw,echo=0,link={conf["port"]},group={conf["groupid"]},mode=660"])

        while not os.path.exists(f"{conf["port"]}_master"):
            pass
        
        return StartAsyncSerialServer(context = ctx, framer = "rtu", identity = {}, port = f"{conf["port"]}_master", stopbits = 2, bytesize = 8, parity = "N", baudrate = 19200)

async def main():
    servers = [start_server(conf[c]) for c in conf]
    await asyncio.gather(
        *servers
    )

if __name__ == "__main__":
    asyncio.run(main())

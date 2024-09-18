import argparse
import yaml
import asyncio
import os
import termios
import tty
import concurrent.futures
import fcntl
from contextlib import contextmanager

from pymodbus.server import StartAsyncTcpServer, StartAsyncSerialServer
from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext
from JSONModbusSlaveContext import JSONModbusSlaveContext

parser = argparse.ArgumentParser(prog='pyModbus testing server',
                    description='Expose modbus server with test values')

parser.add_argument("-c", "--config", type=argparse.FileType('r'), required=True)

args = parser.parse_args()

conf = yaml.load(args.config, Loader = yaml.Loader)

@contextmanager
def open_pty(port, groupid, **kwds):
    # if there is an old broken symlink, remove it
    if not os.path.exists(os.readlink(port)):
        print("Removing broken symlink")
        os.remove(port)

    master, slave = os.openpty()
    slave_path = os.ttyname(slave)

    os.symlink(slave_path, port)

    os.chmod(slave, mode = 0o660)
    os.chown(slave, 0, groupid)

    tty.setraw(master)
    tty.setraw(slave)

    lflag  = 3
    cc     = 6

    termAttr = termios.tcgetattr(slave)
    termAttr[lflag] &= ~termios.ICANON & ~termios.ECHO
    # disable interrupt, quit, and suspend character processing 
    termAttr[cc][termios.VINTR] = b'\x00' 
    termAttr[cc][termios.VQUIT] = b'\x00'
    termAttr[cc][termios.VSUSP] = b'\x00'
    # set revised pty attributes immeaditely
    termios.tcsetattr( master, termios.TCSANOW, termAttr )

    flags = fcntl.fcntl( master, fcntl.F_GETFL ) 
    flags |= os.O_NONBLOCK               
    fcntl.fcntl( master, fcntl.F_SETFL, flags )

    try:
        yield master
    finally:
        os.remove(port)
        os.close(master)
        os.close(slave)

async def pty_bridge(src, dst):
    while True:
        await asyncio.sleep(0.01)
        try:
            din = os.read(src, 1)
        except Exception:
            continue
        if len(din) != 0:
            os.write(dst, din)            

async def start_server(conf):
    slavectx = JSONModbusSlaveContext(conf["input_dump"], conf["holding_dump"])
    ctx = ModbusServerContext(slaves=slavectx, single=True)
    if isinstance(conf["port"], int):
        print(f"Starting tcp server on {conf['port']}")
        return await StartAsyncTcpServer(context = ctx, framer = "socket", identity = {}, address = ["0.0.0.0", conf['port']])
    else:
        print(f"Starting serial server on {conf['port']}")

    with open_pty(f"{conf["port"]}_master", conf["groupid"]) as server, open_pty(conf["port"], conf["groupid"]) as client:
        asyncio.create_task(pty_bridge(server, client))
        asyncio.create_task(pty_bridge(client, server))
        await StartAsyncSerialServer(context = ctx, framer = "rtu", identity = {}, port = f"{conf["port"]}_master", stopbits = 2, bytesize = 8, parity = "N", baudrate = 19200)

async def main():
    server = [start_server(conf[c]) for c in conf]
    await asyncio.gather(*server)

if __name__ == "__main__":
    asyncio.run(main())

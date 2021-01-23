import shutil
from contextlib import contextmanager
from os import environ
from os.path import join, isfile, isdir, dirname

import stem.process
from stem import CircStatus
from stem.control import Controller
from stem import Signal
from stem.util import term
import common as cm
import time

class TorController(object):
    def __init__(self,
                 torrc_path=None,
                 control_port=9051,
                 socks_port = 9050,):

        self.controller = None
        self.tor_process = None 
        self.torrc_path = torrc_path
        self.control_port = control_port
        self.socks_port = socks_port


    def get_guard_ip(self):
        addresses = set()
        for circ in sorted(self.controller.get_circuits()):
            if circ.status != CircStatus.BUILT:
                continue
            fingerprint, nickname = circ.path[0]
            desc = self.controller.get_network_status(fingerprint, None)
            address = desc.address if desc else None
            if address:
                addresses.add(address)
        if len(addresses) == 0:
            addresses = set(cm.My_Bridge_Ips)
        return list(addresses)
    # def get_guard_ips(self):
    #     ips = []
    #     for circ in self.controller.get_circuits():
    #         # filter empty circuits out
    #         if len(circ.path) == 0:
    #             continue
    #         ip = self.controller.get_network_status(circ.path[0][0]).address
    #         if ip not in ips:
    #             ips.append(ip)
    #     return ips

    # def get_all_guard_ips(self):
    #     for router_status in self.controller.get_network_statuses():
    #         if 'Guard' in router_status.flags:
    #             yield router_status.address

    def tor_log_handler(self, line):
        print(term.format(line))

    def restart_tor(self):
        """Kill current Tor process and run a new one."""
        self.quit()
        self.launch_tor_service()


    def quit(self):
        """Kill Tor process."""
        if self.tor_process:
            print("Killing tor process")
            self.tor_process.kill()

    def launch_tor_service(self):
        """Launch Tor service and return the process."""
        # the following may raise, make sure it's handled
        self.tor_process = stem.process.launch_tor(
            torrc_path=self.torrc_path,
            init_msg_handler=self.tor_log_handler,
            timeout=100
        )
        self.controller = Controller.from_port(port=self.control_port)
        self.controller.authenticate()
        return self.tor_process

    def change_identity(self):
        self.controller.signal(Signal.NEWNYM)
        time.sleep(self.controller.get_newnym_wait())

    # def close_all_streams(self):
    #     """Close all streams of a controller."""
    #     print("Closing all streams")
    #     try:
    #         with ut.timeout(cm.STREAM_CLOSE_TIMEOUT):
    #             for stream in self.controller.get_streams():
    #                 print("Closing stream %s %s %s " %
    #                       (stream.id, stream.purpose, stream.target_address))
    #                 self.controller.close_stream(stream.id)  # MISC reason
    #     except ut.TimeoutException:
    #         print("Closing streams timed out!")
    #     except:
    #         print("Exception closing stream")

    @contextmanager
    def launch(self):
        self.launch_tor_service()
        yield
        self.quit()



"""Sprawdza odświeżanie polecenia przez rzeczywiste zapisy Modbus FC05."""

import socket
import time
import unittest

from pyModbusTCP.client import ModbusClient
from pyModbusTCP.server import ModbusServer

from process_server import COMMAND_TIMEOUT_S, CommandBank


class CommandWatchdogTest(unittest.TestCase):
    def test_repeated_write_of_unchanged_coil_refreshes_command(self):
        bank = CommandBank(coils_size=1, d_inputs_size=0,
                           h_regs_size=0, i_regs_size=1)
        bank.set_coils(0, [False])
        self.assertFalse(bank.command_is_fresh(time.monotonic()))

        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]

        server = ModbusServer(host="127.0.0.1", port=port,
                              no_block=True, data_bank=bank)
        server.start()
        client = ModbusClient(host="127.0.0.1", port=port, unit_id=1,
                              timeout=1.0)
        try:
            for _ in range(20):
                if client.write_single_coil(0, True):
                    break
                time.sleep(0.05)
            else:
                self.fail("Serwer testowy Modbus nie przyjął zapisu cewki")
            first_write_at = time.monotonic()
            self.assertTrue(bank.command_is_fresh(first_write_at))

            time.sleep(0.15)
            self.assertTrue(client.write_single_coil(0, True))
            self.assertEqual(bank.get_coils(0, 1), [True])
            self.assertTrue(bank.command_is_fresh(
                first_write_at + COMMAND_TIMEOUT_S + 0.05))
            self.assertFalse(bank.command_is_fresh(
                time.monotonic() + COMMAND_TIMEOUT_S + 0.05))
        finally:
            client.close()
            server.stop()


if __name__ == "__main__":
    unittest.main()

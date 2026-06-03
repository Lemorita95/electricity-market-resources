import shutil
import sys
import threading


class TerminalMonitor:

    def __init__(self):
        self._lock = threading.Lock()
        self._render_lock = threading.Lock()
        self._monitor_msgs = {"entso-e": "waiting...", "copernicus": "waiting..."}
        self._zones: dict[str, dict[str, str]] = {}
        self._line_count = 0

    def update(self, zone: str, msg: str, query_name: str = "") -> None:
        with self._lock:
            if zone in self._monitor_msgs:
                self._monitor_msgs[zone] = msg
            elif zone in self._zones and query_name in self._zones[zone]:
                self._zones[zone][query_name] = msg
        self._render()

    def make_monitor_callback(self, client: str):
        return lambda msg: self.update(client, msg)

    def make_zone_callback(self, zone: str, query_name: str):
        return lambda msg: self.update(zone, msg, query_name)

    def init_display(self, zones: list[str]) -> None:
        with self._lock:
            for zone in sorted(zones):
                self._zones[zone] = {
                    "entsoe_price": "waiting...",
                    "entsoe_demand": "waiting...",
                    "copernicus": "waiting...",
                }
        print("\033[2J\033[H", end="", flush=True)
        n = 1 + len(zones)
        sys.stdout.write("\n" * n)
        sys.stdout.flush()
        with self._lock:
            self._line_count = n
        self._render()

    def _render(self) -> None:
        with self._render_lock:  # only one render at a time
            with self._lock:
                monitor_msg = self._monitor_msg
                zones = dict(self._zones)
                last_lines = self._line_count

            width = shutil.get_terminal_size().columns
            lines = [f"  [{k}] {v}" for k, v in self._monitor_msgs.items()]
            for zone, queries in sorted(zones.items()):
                parts = " / ".join(f"{k}: {v}" for k, v in queries.items())
                lines.append(f"  [{zone}] {parts}")

            padded = [f"{line:<{width}}" for line in lines]

            def terminal_rows(line: str) -> int:
                return max(1, -(-len(line) // width))

            total_rows = sum(terminal_rows(line) for line in padded)

            if last_lines:
                sys.stdout.write(f"\033[{last_lines}A")
            sys.stdout.write("\n".join(padded) + "\n")
            sys.stdout.flush()

            with self._lock:
                self._line_count = total_rows
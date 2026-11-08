"""
ForeShock Hardware Bridge
Listens to the Arduino over USB (serial) and forwards every SOS payload
to the FastAPI backend as an HTTP POST.

Usage:
    py bridge.py                # real hardware mode (auto-detects the Arduino port)
    py bridge.py --simulate     # no hardware needed - fakes button presses every 5s
    py bridge.py --port COM5    # force a specific COM port

Pipeline:  Arduino -> (USB serial) -> bridge.py -> POST /api/alert -> Leaflet map
"""

import json
import random
import sys
import time

import requests

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    print("Missing dependency. Run:  py -m pip install pyserial requests")
    sys.exit(1)

# ----------------- Configuration -----------------
API_URL = "http://localhost:8000/api/alert"
BAUD_RATE = 9600                     # must match the Arduino sketch's Serial.begin(...)
CAMPUS_CENTER = (32.985, -96.750)    # fallback GPS if the Arduino doesn't send coords

# Default urgency per alert type (used when the Arduino payload has no urgency field)
DEFAULT_URGENCY = {
    "MEDICAL": 10,
    "TRAPPED": 8,
    "SUPPLIES": 4,
    "SAFE": 0,
}


def send_alert(alert: dict) -> bool:
    """POST one alert to the backend. Returns True on success."""
    try:
        r = requests.post(API_URL, json=alert, timeout=3)
        if r.ok:
            print(f"   -> Delivered {alert['type']} at ({alert['lat']:.4f}, {alert['lon']:.4f})")
            return True
        print(f"   -> Backend rejected alert (HTTP {r.status_code}): {r.text}")
    except requests.ConnectionError:
        print("   -> Backend not reachable. Is 'py main.py' still running?")
    return False


def enrich(raw: dict) -> dict:
    """Fill in any fields the Arduino didn't provide so the API always accepts it."""
    alert_type = str(raw.get("type", "UNKNOWN")).upper()
    return {
        "type": alert_type,
        "lat": float(raw.get("lat", CAMPUS_CENTER[0])),
        "lon": float(raw.get("lon", CAMPUS_CENTER[1])),
        "urgency": int(raw.get("urgency", DEFAULT_URGENCY.get(alert_type, 5))),
    }


def parse_line(line: str):
    """
    Accept whatever the Arduino sends:
      1. Clean JSON:      {"type": "MEDICAL", "lat": 32.98, "lon": -96.75}
      2. A bare keyword:  MEDICAL
    Returns an enriched alert dict, or None for unrecognizable noise.
    """
    line = line.strip()
    if not line:
        return None
    try:
        return enrich(json.loads(line))
    except (json.JSONDecodeError, ValueError):
        pass
    # Not valid JSON - look for a known SOS keyword anywhere in the line
    upper = line.upper()
    for keyword in DEFAULT_URGENCY:
        if keyword in upper:
            return enrich({"type": keyword})
    return None


def find_arduino_port():
    """Look for a connected Arduino; returns its COM port name or None."""
    for p in list(list_ports.comports()):
        desc = (p.description or "").lower()
        if "arduino" in desc or "usb serial" in desc or "ch340" in desc:
            return p.device
    return None


def run_simulate():
    """No hardware? Pretend to be an Arduino. Cycles through all alert types."""
    types = list(DEFAULT_URGENCY)
    print("SIMULATION MODE - fake button presses every 5 seconds. Ctrl+C to stop.\n")
    i = 0
    while True:
        alert_type = types[i % len(types)]
        i += 1
        lat, lon = CAMPUS_CENTER
        alert = enrich({
            "type": alert_type,
            "lat": lat + random.uniform(-0.01, 0.01),
            "lon": lon + random.uniform(-0.01, 0.01),
        })
        print(f"[SIM] Button pressed: {alert_type}")
        send_alert(alert)
        time.sleep(5)


def run_serial(port_name: str):
    print(f"Connecting to {port_name} at {BAUD_RATE} baud...")
    try:
        ser = serial.Serial(port_name, BAUD_RATE, timeout=1)
    except serial.SerialException as e:
        print(f"Could not open {port_name}: {e}")
        print("Gotchas: close the Arduino IDE Serial Monitor (only one app can use a port),")
        print("check Device Manager > Ports, or run 'py bridge.py' to auto-detect.")
        sys.exit(1)

    print(f"Listening on {port_name}. Press a button on the Arduino! Ctrl+C to stop.\n")
    while True:
        try:
            raw = ser.readline().decode("utf-8", errors="ignore")
            alert = parse_line(raw)
            if alert:
                print(f"[ARDUINO] {raw.strip()}")
                send_alert(alert)
            elif raw.strip():
                print(f"[ARDUINO] Unrecognized serial data at {BAUD_RATE} baud: {raw.strip()!r}")
        except serial.SerialException:
            print("Serial port lost (unplugged?). Reconnecting in 3s...")
            time.sleep(3)
            try:
                ser = serial.Serial(port_name, BAUD_RATE, timeout=1)
            except serial.SerialException:
                continue


def main():
    args = sys.argv[1:]
    if "--simulate" in args:
        run_simulate()
        return
    if "--port" in args:
        port_name = args[args.index("--port") + 1]
    else:
        port_name = find_arduino_port()
        if not port_name:
            all_ports = list(list_ports.comports())
            print("No Arduino found. Devices I can see:")
            if all_ports:
                for p in all_ports:
                    print(f"   {p.device} - {p.description}")
                print(f"\nRetry with an explicit port, e.g.:  py bridge.py --port {all_ports[0].device}")
            else:
                print("   (none at all - is the USB cable plugged in?)")
                print("\nOr test the whole pipeline without hardware:  py bridge.py --simulate")
            sys.exit(1)
    run_serial(port_name)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBridge stopped.")

import hid
import time
import colorsys
import json
import sys
import math
import random
import os
import queue
import threading

# ==============================================================
# MAD68 Pro R - Python RGB Engine
# ==============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MATRIX_MAP_PATH = os.path.join(SCRIPT_DIR, 'matrix_map.json')

LAYOUT_X = {
    'esc': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
    '8': 8, '9': 9, '0': 10, '-': 11, '=': 12, 'backspace': 13,
    'ins': 14.2, 'tab': 0, 'q': 1.5, 'w': 2.5, 'e': 3.5, 'r': 4.5,
    't': 5.5, 'y': 6.5, 'u': 7.5, 'i': 8.5, 'o': 9.5, 'p': 10.5,
    '[': 11.5, ']': 12.5, '\\': 13.5, 'delete': 14.2,
    'caps lock': 0, 'a': 1.75, 's': 2.75, 'd': 3.75, 'f': 4.75, 'g': 5.75,
    'h': 6.75, 'j': 7.75, 'k': 8.75, 'l': 9.75, ';': 10.75, "'": 11.75,
    'enter': 13.2, 'pgup': 14.5,
    'shift': 0, 'z': 2.25, 'x': 3.25, 'c': 4.25, 'v': 5.25, 'b': 6.25,
    'n': 7.25, 'm': 8.25, ',': 9.25, '.': 10.25, '/': 11.25,
    'right shift': 12.5, 'up': 13.5, 'pgdn': 14.5,
    'ctrl': 0, 'left windows': 1.25, 'alt': 2.5, 'space': 6,
    'alt gr': 10, 'fn': 11, 'right ctrl': 12, 'left': 13, 'down': 14, 'right': 14.8
}

def calculate_checksum(payload):
    return sum(payload[4:]) & 0xFF

# ==================== HID CONTROLLER ====================
class HIDController:
    def __init__(self, vid=0x373B, pid=0x1058, interface=1):
        self.vid = vid
        self.pid = pid
        self.interface = interface
        self.device = None
        self.last_chunks = {}

    def is_device_present(self):
        for d in hid.enumerate(self.vid, self.pid):
            if d['interface_number'] == self.interface:
                return True
        return False

    def connect(self):
        target_path = None
        for d in hid.enumerate(self.vid, self.pid):
            if d['interface_number'] == self.interface:
                target_path = d['path']
                break
        if not target_path:
            raise Exception("Nie znaleziono klawiatury / Keyboard not found!")
        self.device = hid.device()
        self.device.open_path(target_path)

    def disconnect(self):
        if self.device:
            try:
                self.device.close()
            except: pass
        self.device = None

    def send_frame(self, matrix):
        offset = 0
        chunk_index = 0
        while offset < 384:
            chunk_size = min(56, 384 - offset)
            chunk = matrix[offset:offset + chunk_size]
            if chunk_index not in self.last_chunks or self.last_chunks[chunk_index] != chunk:
                payload = bytearray(64)
                payload[0:2] = b'\x55\x0B'
                payload[4] = chunk_size
                payload[5] = offset & 0xFF
                payload[6] = (offset >> 8) & 0xFF
                payload[7] = 0x01 if offset == 0 else 0x00
                for i in range(chunk_size):
                    payload[8 + i] = chunk[i]
                payload[3] = calculate_checksum(payload)
                self.device.write(b'\x00' + bytes(payload))
                time.sleep(0.005)
                self.last_chunks[chunk_index] = bytearray(chunk)
            offset += chunk_size
            chunk_index += 1

    def clear(self):
        self.last_chunks = {}
        self.send_frame(bytearray(384))

# ==================== MAIN ENGINE ====================
def main():
    try:
        with open(MATRIX_MAP_PATH, 'r') as f:
            key_map = json.load(f)
    except Exception as e:
        print(json.dumps({"error": f"Error matrix_map.json: {e}"}), flush=True)
        sys.exit(1)

    hid_ctrl = HIDController()
    try:
        hid_ctrl.connect()
        print(json.dumps({"status": "connected"}), flush=True)
    except Exception as e:
        print(json.dumps({"error": str(e)}), flush=True)

    last_reconnect_attempt = 0.0
    last_presence_check = 0.0
    current_code = ""
    current_params = {
        'fps': 10, 'speed': 0.015, 'width': 0.03,
        'brightness': 1.0, 'rainbow': True, 'color': [255, 0, 0]
    }
    t = 0.0

    exec_globals = {
        'math': math, 'colorsys': colorsys, 'random': random, 'LAYOUT_X': LAYOUT_X,
    }

    stdin_queue = queue.Queue()
    def stdin_reader():
        while True:
            try:
                line = sys.stdin.readline()
                if not line: break
                line = line.strip()
                if line: stdin_queue.put(line)
            except: break

    threading.Thread(target=stdin_reader, daemon=True).start()

    while True:
        frame_start = time.time()
        fps = max(1, min(30, current_params.get('fps', 10)))
        frame_time = 1.0 / fps

        while not stdin_queue.empty():
            try:
                line = stdin_queue.get_nowait()
                cmd = json.loads(line)
                if 'code' in cmd:
                    if cmd['code'] != current_code:
                        current_code = cmd['code']
                        t = 0.0
                        hid_ctrl.last_chunks = {}
                if 'params' in cmd:
                    current_params.update(cmd['params'])
            except: pass

        matrix = bytearray(384)
        try:
            exec_locals = {'matrix': matrix, 't': t, 'params': current_params, 'key_map': key_map}
            exec(current_code, exec_globals, exec_locals)
            matrix = exec_locals.get('matrix', matrix)
        except: pass

        now = time.time()
        if hid_ctrl.device:
            if now - last_presence_check >= 2.0:
                last_presence_check = now
                if not hid_ctrl.is_device_present():
                    print(json.dumps({"error": "Klawiatura odłączona / Keyboard disconnected"}), flush=True)
                    hid_ctrl.disconnect()

        if hid_ctrl.device:
            try:
                hid_ctrl.send_frame(matrix)
            except Exception as e:
                print(json.dumps({"error": f"Błąd/Error: {e}"}), flush=True)
                hid_ctrl.disconnect()
        else:
            if now - last_reconnect_attempt >= 2.0:
                last_reconnect_attempt = now
                try:
                    hid_ctrl.connect()
                    hid_ctrl.last_chunks = {}
                    print(json.dumps({"status": "connected"}), flush=True)
                except: pass

        colors = {}
        for key_name, virtual_id in key_map.items():
            base = virtual_id * 3
            if base + 2 < 384:
                colors[key_name] = [matrix[base], matrix[base + 1], matrix[base + 2]]
        print(json.dumps({"frame": colors}), flush=True)

        t += current_params.get('speed', 0.015)
        elapsed = time.time() - frame_start
        sleep_time = frame_time - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

if __name__ == '__main__':
    main()

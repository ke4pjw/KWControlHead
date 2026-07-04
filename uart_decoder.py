"""
TM-D700 head/body UART decoder for Saleae Logic CSV exports.

Confirmed protocol parameters (from real boot capture, 2026-06-30):
  - Baud rate: 57600 (measured bit period 17.369us vs theoretical 17.361us
    for 57600 — matches the 11.0592MHz crystal: 11,059,200 / 192 = 57,600)
  - Format: 8 data bits, no parity, 1 stop bit (8N1)
  - Idle level: HIGH
  - Framing: ASCII tag byte + ASCII payload, terminated by 0x0D (CR)
  - No checksum observed
  - Idle/keepalive: lone 0xFF byte sent by both sides roughly every 1.4s

Usage:
    python uart_decoder.py capture.csv
    python uart_decoder.py capture.csv --baud 57600
    python uart_decoder.py capture.csv --ch0-name TXD --ch1-name RXD
"""

import argparse
import bisect
import csv
import sys
from dataclasses import dataclass


DEFAULT_BAUD = 57600


@dataclass
class Message:
    timestamp: float
    channel: str
    tag: int          # first byte of message (may have high bit set)
    payload: bytes     # remaining bytes (excludes terminating CR)

    @property
    def tag_char(self) -> str:
        return chr(self.tag) if 32 <= self.tag < 127 else f'[0x{self.tag:02X}]'

    @property
    def payload_str(self) -> str:
        out = ''
        for v in self.payload:
            out += chr(v) if 32 <= v < 127 else f'[0x{v:02X}]'
        return out

    def __repr__(self):
        return f'{self.timestamp:9.6f}s {self.channel:4s} {self.tag_char}{self.payload_str}'


def load_csv(path: str):
    """Load a Saleae transition-list CSV. Returns (times, ch0_vals, ch1_vals)."""
    times, ch0, ch1 = [], [], []
    with open(path, newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            times.append(float(row[0]))
            ch0.append(int(row[1]))
            ch1.append(int(row[2]))
    return times, ch0, ch1


def build_transitions(times, ch):
    """Collapse to (time, value) pairs only at real level changes."""
    trans = [(times[0], ch[0])]
    for i in range(1, len(times)):
        if ch[i] != trans[-1][1]:
            trans.append((times[i], ch[i]))
    return trans


def get_level(trans, t):
    times_only = [x[0] for x in trans]
    idx = bisect.bisect_right(times_only, t) - 1
    if idx < 0:
        idx = 0
    return trans[idx][1]


def decode_uart_bytes(trans, baud: int):
    """Decode 8N1 UART bytes from a transition list. Returns list of
    (start_time, byte_value, stop_bit_ok)."""
    bit = 1.0 / baud
    bytes_out = []
    i = 1
    n = len(trans)
    while i < n:
        ttime, tval = trans[i]
        prevval = trans[i - 1][1]
        if prevval == 1 and tval == 0:           # falling edge = start bit
            start = ttime
            bits = []
            for b in range(8):
                sample_t = start + (1.5 + b) * bit
                bits.append(get_level(trans, sample_t))
            stop_bit = get_level(trans, start + 9.5 * bit)
            byte_val = 0
            for b in range(8):
                byte_val |= (bits[b] << b)        # LSB first
            bytes_out.append((start, byte_val, stop_bit == 1))
            frame_end = start + 10 * bit
            while i < n and trans[i][0] < frame_end:
                i += 1
            continue
        i += 1
    return bytes_out


def split_messages(bytelist, channel_name: str, terminator: int = 0x0D):
    """Split a decoded byte stream into Message objects on the terminator byte.

    A lone terminator byte with nothing collected before it (e.g. a bare
    0x0D sync byte at link startup) is recorded as a Message with tag=0x0D
    and an empty payload, rather than silently dropped."""
    msgs = []
    cur = []
    cur_start = None
    for t, v, ok in bytelist:
        if cur_start is None:
            cur_start = t
        if v == terminator:
            if cur:
                msgs.append(Message(cur_start, channel_name, cur[0], bytes(cur[1:])))
            else:
                # bare terminator with no preceding bytes -- record it,
                # don't drop it (e.g. the power-on sync byte)
                msgs.append(Message(cur_start, channel_name, terminator, b''))
            cur = []
            cur_start = None
        else:
            cur.append(v)
    if cur:
        msgs.append(Message(cur_start, channel_name, cur[0], bytes(cur[1:])))
    return msgs


def decode_csv(path: str, baud: int = DEFAULT_BAUD,
               ch0_name: str = 'CH0', ch1_name: str = 'CH1'):
    """Full pipeline: load CSV -> decode UART -> split into messages.
    Returns (messages_ch0, messages_ch1), both lists of Message, time-sorted."""
    times, ch0, ch1 = load_csv(path)
    t0 = build_transitions(times, ch0)
    t1 = build_transitions(times, ch1)
    b0 = decode_uart_bytes(t0, baud)
    b1 = decode_uart_bytes(t1, baud)
    m0 = split_messages(b0, ch0_name)
    m1 = split_messages(b1, ch1_name)
    return m0, m1


def merged_timeline(m0, m1):
    """Merge both channels into one time-ordered list for easy reading."""
    return sorted(m0 + m1, key=lambda m: m.timestamp)


def framing_error_report(trans, baud):
    bytelist = decode_uart_bytes(trans, baud)
    bad = sum(1 for t, v, ok in bytelist if not ok)
    return len(bytelist), bad


def main():
    p = argparse.ArgumentParser(description='Decode TM-D700 head/body UART capture CSV')
    p.add_argument('csv_file')
    p.add_argument('--baud', type=int, default=DEFAULT_BAUD)
    p.add_argument('--ch0-name', default='TXD(head)')
    p.add_argument('--ch1-name', default='RXD(body)')
    p.add_argument('--merged', action='store_true',
                   help='Print one merged time-ordered timeline instead of per-channel')
    p.add_argument('--scan-baud', action='store_true',
                   help='Try common baud rates and report framing-error counts for each')
    args = p.parse_args()

    if args.scan_baud:
        times, ch0, ch1 = load_csv(args.csv_file)
        t0 = build_transitions(times, ch0)
        t1 = build_transitions(times, ch1)
        print(f'{"baud":>8s}  {"ch0 bytes":>10s}  {"ch0 errs":>9s}  '
              f'{"ch1 bytes":>10s}  {"ch1 errs":>9s}')
        for baud in [4800, 9600, 19200, 38400, 57600, 115200]:
            n0, e0 = framing_error_report(t0, baud)
            n1, e1 = framing_error_report(t1, baud)
            print(f'{baud:8d}  {n0:10d}  {e0:9d}  {n1:10d}  {e1:9d}')
        return

    m0, m1 = decode_csv(args.csv_file, args.baud, args.ch0_name, args.ch1_name)

    if args.merged:
        for m in merged_timeline(m0, m1):
            print(m)
    else:
        print(f'=== {args.ch0_name}: {len(m0)} messages ===')
        for m in m0:
            print(m)
        print(f'\n=== {args.ch1_name}: {len(m1)} messages ===')
        for m in m1:
            print(m)


if __name__ == '__main__':
    main()

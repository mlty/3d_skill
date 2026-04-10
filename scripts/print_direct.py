#!/usr/bin/env python3
"""
Direct print to Bambu Lab printer via implicit FTPS + MQTT.

Workflow: Upload sliced 3MF → Send MQTT project_file command → Printer starts.

Bambu Lab printers use implicit FTPS (port 990) which requires:
  1. Immediate TLS wrapping on connect (not STARTTLS)
  2. TLS session reuse for data connections

Usage:
    python scripts/print_direct.py <file.3mf> [--ip IP] [--code ACCESS_CODE] [--serial SERIAL]

The 3MF must contain sliced G-code (use Bambu Studio CLI to slice first).
"""
import argparse
import json
import os
import socket
import ssl
import sys
import time
from ftplib import FTP_TLS, FTP

# ─── Load config defaults ────────────────────────────────────────────

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)

def _load_config():
    """Load config.json and .secrets.json for default values."""
    config = {}
    for name in ("config.json", ".secrets.json"):
        path = os.path.join(_SKILL_DIR, name)
        if os.path.exists(path):
            with open(path) as f:
                config.update(json.load(f))
    return config

_config = _load_config()

DEFAULT_IP = os.environ.get("BAMBU_IP", _config.get("printer_ip", "172.20.10.2"))
DEFAULT_SERIAL = os.environ.get("BAMBU_SERIAL", _config.get("serial", ""))
DEFAULT_ACCESS_CODE = os.environ.get("BAMBU_ACCESS_CODE", _config.get("access_code", ""))


# ─── Implicit FTPS ───────────────────────────────────────────────────

class ImplicitFTP_TLS(FTP_TLS):
    """
    FTP_TLS subclass for implicit FTPS (port 990).

    Standard FTP_TLS uses explicit FTPS (connect plaintext, then STARTTLS).
    Bambu Lab printers require implicit FTPS: TLS is established immediately
    on connect, and data connections must reuse the control TLS session.
    """

    def connect(self, host='', port=990, timeout=-999, source_address=None):
        if host:
            self.host = host
        if port > 0:
            self.port = port
        if timeout != -999:
            self.timeout = timeout
        if source_address:
            self.source_address = source_address

        self.sock = socket.create_connection(
            (self.host, self.port), self.timeout,
            source_address=self.source_address
        )
        self.af = self.sock.family
        # Wrap with TLS immediately (implicit FTPS)
        self.sock = self.context.wrap_socket(self.sock, server_hostname=self.host)
        self.file = self.sock.makefile('r', encoding=self.encoding)
        self.welcome = self.getresp()
        return self.welcome

    def ntransfercmd(self, cmd, rest=None):
        conn, size = FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            # Reuse TLS session from control connection (required by Bambu printers)
            conn = self.context.wrap_socket(
                conn, server_hostname=self.host,
                session=self.sock.session
            )
        return conn, size


def _make_ssl_context():
    """Create a permissive SSL context for Bambu Lab's self-signed certs."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        ctx.set_ciphers('DEFAULT:@SECLEVEL=0')
    except ssl.SSLError:
        pass
    return ctx


# ─── FTP Upload ──────────────────────────────────────────────────────

def ftp_upload(ip, access_code, local_path, remote_filename=None, timeout=30):
    """
    Upload a file to Bambu Lab printer via implicit FTPS (port 990).

    Args:
        ip: Printer LAN IP address
        access_code: Printer LAN access code
        local_path: Path to local file
        remote_filename: Filename on printer (default: basename of local_path)
        timeout: Connection timeout in seconds

    Returns:
        Remote filename on success

    Raises:
        RuntimeError on failure
    """
    if not os.path.exists(local_path):
        raise RuntimeError(f"File not found: {local_path}")

    if remote_filename is None:
        remote_filename = os.path.basename(local_path)

    ctx = _make_ssl_context()
    ftp = ImplicitFTP_TLS(context=ctx)

    try:
        ftp.connect(ip, 990, timeout=timeout)
        ftp.login('bblp', access_code)
        ftp.prot_p()

        remote_path = f'/{remote_filename}'
        with open(local_path, 'rb') as f:
            ftp.storbinary(f'STOR {remote_path}', f)

        ftp.quit()
        return remote_filename
    except Exception as e:
        raise RuntimeError(f"FTP upload failed: {e}") from e


# ─── MQTT Print Command ─────────────────────────────────────────────

def mqtt_start_print(ip, access_code, serial, remote_filename,
                     plate_number=1, use_ams=False, ams_mapping=None,
                     timeout=15):
    """
    Send project_file command via MQTT to start printing.

    Args:
        ip: Printer LAN IP address
        access_code: Printer LAN access code
        serial: Printer serial number
        remote_filename: Filename on printer (uploaded via FTP)
        plate_number: Plate number in 3MF (default: 1)
        use_ams: Whether to use AMS
        ams_mapping: AMS slot mapping list (e.g., [0, 1, 2])
        timeout: MQTT connection timeout in seconds

    Returns:
        True on success, False on timeout
    """
    import paho.mqtt.client as mqtt

    cmd = {
        "print": {
            "sequence_id": "0",
            "command": "project_file",
            "param": f"Metadata/plate_{plate_number}.gcode",
            "file": remote_filename,
            "url": f"ftp:///{remote_filename}",
            "subtask_name": remote_filename.replace('.3mf', ''),
            "project_id": "0",
            "profile_id": "0",
            "task_id": "0",
            "subtask_id": "0",
            "bed_type": "auto",
            "bed_leveling": True,
            "flow_cali": True,
            "vibration_cali": True,
            "layer_inspect": False,
            "timelapse": False,
            "use_ams": use_ams,
            "ams_mapping": ams_mapping if ams_mapping else [0]
        }
    }

    connected = [False]

    def on_connect(client, userdata, flags, rc, properties=None):
        connected[0] = True

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.username_pw_set('bblp', access_code)
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)

    try:
        client.connect(ip, 8883, keepalive=60)
    except Exception:
        pass  # MQTT may report SSL error but still connect

    client.loop_start()

    for _ in range(timeout):
        if connected[0]:
            break
        time.sleep(1)

    success = False
    if connected[0]:
        topic = f"device/{serial}/request"
        client.publish(topic, json.dumps(cmd))
        time.sleep(2)
        success = True

    client.loop_stop()
    client.disconnect()
    return success


# ─── Main ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Direct print to Bambu Lab printer (FTPS upload + MQTT command)"
    )
    parser.add_argument("file", help="Sliced 3MF file to print")
    parser.add_argument("--ip", default=DEFAULT_IP, help=f"Printer IP (default: {DEFAULT_IP})")
    parser.add_argument("--code", default=DEFAULT_ACCESS_CODE, help="LAN access code")
    parser.add_argument("--serial", default=DEFAULT_SERIAL, help="Printer serial number")
    parser.add_argument("--plate", type=int, default=1, help="Plate number (default: 1)")
    parser.add_argument("--ams-mapping", type=str, help="AMS slot mapping (comma-separated, e.g., 0,1,2)")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"❌ File not found: {args.file}")
        sys.exit(1)

    if not args.file.lower().endswith('.3mf'):
        print(f"⚠️ Warning: File is not .3mf — printer requires sliced 3MF with G-code.")
        print(f"   Slice first: bambu-studio.exe model.stl --load-settings ... --slice 0 --export-3mf out.3mf")

    if not args.code or not args.serial:
        print("❌ Missing credentials. Set via --code/--serial or env vars BAMBU_ACCESS_CODE/BAMBU_SERIAL")
        sys.exit(1)

    ams_mapping = None
    use_ams = False
    if args.ams_mapping:
        ams_mapping = [int(x.strip()) for x in args.ams_mapping.split(',')]
        use_ams = True

    # Step 1: Upload
    print(f"📤 Uploading {os.path.basename(args.file)} to {args.ip}...")
    try:
        remote = ftp_upload(args.ip, args.code, args.file)
        print(f"   ✅ Upload complete: {remote}")
    except RuntimeError as e:
        print(f"   ❌ {e}")
        sys.exit(1)

    # Step 2: Print
    print(f"📡 Sending print command...")
    ok = mqtt_start_print(
        args.ip, args.code, args.serial, remote,
        plate_number=args.plate,
        use_ams=use_ams, ams_mapping=ams_mapping
    )
    if ok:
        print(f"   ✅ Print started: {remote}")
    else:
        print(f"   ⚠️ MQTT timeout — file uploaded, start from printer touchscreen.")

    print(f"\n🖨️ Check printer for status.")


if __name__ == "__main__":
    main()

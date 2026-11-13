"""Headless ArduPilot conventional-helicopter SITL integration smoke.

Verifies real MAVLink telemetry and the helicopter FRAME_CLASS. No rotorcraft
hover/fidelity claim can be made from successfully launching a binary.
Runs with downloaded official firmware; no external actions or real hardware.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time

from pymavlink import mavutil

MAVLINK_PORT = 5760
FRAME_CLASS_HELI = 6
REQUIRED_MSGS = ("HEARTBEAT", "ATTITUDE", "GLOBAL_POSITION_INT")
MAX_WALL_S = 65


def _atomic(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp=None
    try:
        with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=path.parent,
                                         prefix=path.name+".",suffix=".tmp",
                                         delete=False) as f:
            temp=Path(f.name)
            json.dump(obj,f,indent=2,sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def connect_sitl(proc, deadline):
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError("SITL process exited before MAVLink connection")
        try:
            conn = mavutil.mavlink_connection(
                f"tcp:127.0.0.1:{MAVLINK_PORT}",
                autoreconnect=False, source_system=255, source_component=0,
            )
            hb=conn.wait_heartbeat(timeout=3)
            if hb is not None:
                return conn,hb
            conn.close()
        except (OSError, ConnectionError, socket.error):
            pass
        time.sleep(0.5)
    raise TimeoutError("no MAVLink heartbeat received")


def run(binary,defaults,logfile):
    cmd=[str(binary.resolve()),
         "--model","heli",
         "--defaults",str(defaults.resolve()),
         "--home","34.95416,-117.87323,690,180",
         "--wipe"]
    with logfile.open("w",encoding="utf-8",errors="replace") as log:
        proc=subprocess.Popen(cmd,cwd=binary.parent,stdin=subprocess.DEVNULL,
                              stdout=log,stderr=subprocess.STDOUT,
                              start_new_session=True)
        conn=None
        deadline=time.monotonic()+MAX_WALL_S
        try:
            conn,hb=connect_sitl(proc,deadline)
            messages={"HEARTBEAT": {
                "mav_type":int(hb.type),
                "autopilot":int(hb.autopilot),
                "mode":int(hb.custom_mode),
                "system_id":int(conn.target_system),
                "component_id":int(conn.target_component),
            }}
            # Request parameter independently of version assumptions.
            conn.mav.param_request_read_send(
                conn.target_system,conn.target_component,b"FRAME_CLASS",-1,
            )
            frame_class=None
            while time.monotonic() < deadline and (
                frame_class is None or not all(k in messages for k in REQUIRED_MSGS)
            ):
                m=conn.recv_match(blocking=True,timeout=2)
                if m is None:
                    continue
                kind=m.get_type()
                if kind=="PARAM_VALUE":
                    param=m.param_id
                    if isinstance(param,bytes):
                        param=param.decode("ascii","replace")
                    if str(param).strip("\x00")=="FRAME_CLASS":
                        frame_class=float(m.param_value)
                if kind=="ATTITUDE":
                    messages[kind]={
                        "roll_rad":float(m.roll), "pitch_rad":float(m.pitch),
                        "yaw_rad":float(m.yaw),
                    }
                if kind=="GLOBAL_POSITION_INT":
                    messages[kind]={
                        "lat_deg":float(m.lat)*1e-7,
                        "lon_deg":float(m.lon)*1e-7,
                        "relative_alt_m":float(m.relative_alt)*1e-3,
                    }
            status = ("HELICOPTER_TELEMETRY_READY"
                      if frame_class==FRAME_CLASS_HELI
                      and all(k in messages for k in REQUIRED_MSGS)
                      else "CONFIGURATION_OR_TELEMETRY_UNRESOLVED")
            return {
                "status":status,
                "verified_frame_class":frame_class,
                "expected_frame_class":FRAME_CLASS_HELI,
                "model_argument":"heli",
                "messages":messages,
                "startup_command":cmd,
            }
        finally:
            if conn is not None:
                conn.close()
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--binary",type=Path,required=True)
    ap.add_argument("--defaults",type=Path,required=True)
    ap.add_argument("--firmware-metadata",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    if not args.binary.is_file() or not args.defaults.is_file():
        raise SystemExit("SITL binary or helicopter defaults unavailable")
    info={
        "backend":"ArduPilot SITL",
        "binary_sha256":_sha(args.binary),
        "defaults_sha256":_sha(args.defaults),
        "firmware_metadata":args.firmware_metadata.read_text(encoding="utf-8"),
        "limitations":"MAVLink heartbeat+telemetry and FRAME_CLASS=6 only. "
          "No arming, takeoff, stable hover, numerical convergence or "
          "real-helicopter model validation has yet been demonstrated.",
    }
    try:
        result=run(args.binary,args.defaults,args.output.parent/"sitl-console.log")
        info.update(result)
    except Exception as error:
        info.update({"status":"UNRESOLVED", "error_type":type(error).__name__,
                     "reason":str(error)[:1000]})
    _atomic(args.output,info)
    print(json.dumps({k:v for k,v in info.items()
                      if k not in ("firmware_metadata",)},indent=2))
    if info["status"]!="HELICOPTER_TELEMETRY_READY":
        raise SystemExit("SITL helicopter startup gate unresolved; see artifact")


if __name__=="__main__":
    main()

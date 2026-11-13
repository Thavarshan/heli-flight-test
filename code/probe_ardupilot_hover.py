"""Exploratory fully isolated MAVLink GUIDED hover trial for ArduPilot heli SITL.

Never connects to a network vehicle. All host/ports are loopback, executable
is the downloaded official SITL binary, and commands affect only the process
spawned by this runner. The output is preliminary, not an aircraft validation.
"""
import argparse
import hashlib
import json
import math
import os
import subprocess
import tempfile
import time
from pathlib import Path

from pymavlink import mavutil
from heli_lib.sitl_validation import valid_navigation
from probe_ardupilot_sitl import connect_sitl, MAVLINK_PORT

FRAME_CLASS = 6
LOCATION = "34.95416,-117.87323,690,180"
ALTITUDE_TARGET_M = 8.0
TARGET_WINDOW_S = 20.0
WALL_BUDGET_S = 135.0
METER_PER_DEG_LAT = 111_195.0


def atomic_save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=None
    try:
        with tempfile.NamedTemporaryFile("w",dir=path.parent,encoding="utf-8",
                                         prefix=path.name+".",suffix=".tmp",
                                         delete=False) as f:
            temp=Path(f.name)
            json.dump(obj,f,sort_keys=True,indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def classify_hold(trace,target_reached):
    if not target_reached:
        return {"status":"NO_TAKEOFF_TARGET", "reason":
                "Never achieved target 8m altitude; no hover evaluation"}
    if len(trace)<5:
        return {"status":"UNRESOLVED", "reason":"insufficient_position_messages"}
    end=trace[-1]["time_boot_s"]
    window=[r for r in trace if r["time_boot_s"] >= end-TARGET_WINDOW_S]
    if window[-1]["time_boot_s"]-window[0]["time_boot_s"]<18:
        return {"status":"UNRESOLVED","reason":"insufficient_hover_window"}
    base=window[0]
    factor=math.cos(math.radians(base["lat_deg"]))
    errs=[
        math.hypot((r["lat_deg"]-base["lat_deg"])*METER_PER_DEG_LAT,
                   (r["lon_deg"]-base["lon_deg"])*METER_PER_DEG_LAT*factor)
        for r in window
    ]
    hs=[r["relative_alt_m"] for r in window]
    v=[math.hypot((r["lat_deg"]-prev["lat_deg"])*METER_PER_DEG_LAT,
                   (r["lon_deg"]-prev["lon_deg"])*METER_PER_DEG_LAT*factor)
       /max(1e-8,r["time_boot_s"]-prev["time_boot_s"])
       for prev,r in zip(window,window[1:])
       if r["time_boot_s"]>prev["time_boot_s"]]
    if not v:
        return {"status":"UNRESOLVED","reason":"no_positive_sample_deltas"}
    metrics={"horizontal_excursion_m":max(errs),
             "altitude_span_m":max(hs)-min(hs),
             "peak_sampled_horizontal_speed_mps":max(v),
             "min_relative_alt_m":min(hs),
             "window_duration_s":window[-1]["time_boot_s"]-window[0]["time_boot_s"],
             "window_samples":len(window)}
    thresholds={"horizontal_excursion_m":3.0,"altitude_span_m":2.0,
                "peak_sampled_horizontal_speed_mps":1.0,
                "min_relative_alt_m":5.0}
    accepted=(metrics["horizontal_excursion_m"]<=3.0
              and metrics["altitude_span_m"]<=2.0
              and metrics["peak_sampled_horizontal_speed_mps"]<=1.0
              and metrics["min_relative_alt_m"]>=5.0)
    return {"status":"PASS_CANDIDATE_NOT_VALIDATED" if accepted
            else "FAIL_CANDIDATE",
            "metrics":metrics,"thresholds":thresholds}


def stream_enable(conn):
    conn.mav.request_data_stream_send(
        conn.target_system,conn.target_component,
        mavutil.mavlink.MAV_DATA_STREAM_ALL,5,1,
    )
    for name in ("GLOBAL_POSITION_INT","GPS_RAW_INT","HEARTBEAT","ATTITUDE"):
        conn.mav.command_long_send(
            conn.target_system,conn.target_component,
            mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,0,
            getattr(mavutil.mavlink,"MAVLINK_MSG_ID_"+name),200000,
            0,0,0,0,0,
        )


def command(conn,command_id,p1=0,p2=0,p3=0,p4=0,p5=0,p6=0,p7=0):
    conn.mav.command_long_send(
        conn.target_system,conn.target_component,command_id,0,
        p1,p2,p3,p4,p5,p6,p7,
    )


def attempt(binary,defaults,console):
    args=[str(binary.resolve()),"--model","heli","--defaults",
          str(defaults.resolve()),"--home",LOCATION,"--wipe"]
    with console.open("w",encoding="utf-8",errors="replace") as logs:
        proc=subprocess.Popen(args,cwd=binary.parent,stdin=subprocess.DEVNULL,
                              stdout=logs,stderr=subprocess.STDOUT,
                              start_new_session=True)
        conn=None
        deadline=time.monotonic()+WALL_BUDGET_S
        notes=[]
        trace=[]
        acks=[]
        gps_fix=0
        guided=False
        armed=False
        takeoff_sent=False
        target_reached=False
        phase="start"
        try:
            conn,_=connect_sitl(proc,deadline)
            stream_enable(conn)
            conn.mav.param_request_read_send(conn.target_system,
                                             conn.target_component,
                                             b"FRAME_CLASS",-1)
            mapping=conn.mode_mapping() or {}
            guided_id=mapping.get("GUIDED",4)
            valid_pos=False
            frame_class=None
            last_update=time.monotonic()
            last_interlock_override=-100.0
            while time.monotonic()<deadline:
                now=time.monotonic()
                if proc.poll() is not None:
                    raise RuntimeError("SITL exited during GUIDED experiment")
                # MAVLink RC overrides expire unless periodically refreshed.
                # Keep RC8 LOW until armed; keep it HIGH during runup and
                # automated takeoff. This only targets our loopback SITL.
                if (phase in ("start","request_guided","request_arm",
                              "rotor_runup","request_takeoff","hold")
                        and now-last_interlock_override >= 0.75):
                    # Maintain throttle hold throughout GPS/EKF startup,
                    # before switching mode and requesting arm.
                    rc8 = 1000 if phase in (
                        "start","request_guided","request_arm"
                    ) else 2000
                    conn.mav.rc_channels_override_send(
                        conn.target_system,conn.target_component,
                        0,0,0,0,0,0,0,rc8,
                    )
                    last_interlock_override=now
                if now-last_update>6:
                    stream_enable(conn)
                    last_update=now
                m=conn.recv_match(blocking=True,timeout=1.5)
                if m is None:
                    continue
                kind=m.get_type()
                if kind=="STATUSTEXT":
                    notes.append(str(m.text)[:160])
                    notes=notes[-60:]
                if kind=="COMMAND_ACK":
                    acks.append({"command":int(m.command),
                                 "result":int(m.result),
                                 "phase":phase})
                if kind=="PARAM_VALUE":
                    name=m.param_id
                    if isinstance(name,bytes):
                        name=name.decode("ascii","replace")
                    if str(name).strip("\x00")=="FRAME_CLASS":
                        frame_class=int(m.param_value)
                        if frame_class!=FRAME_CLASS:
                            return {"status":"WRONG_FRAME_CLASS",
                                    "frame_class":frame_class,"notes":notes}
                if kind=="GPS_RAW_INT":
                    gps_fix=max(gps_fix,int(m.fix_type))
                if kind=="HEARTBEAT":
                    armed=bool(m.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
                    guided=int(m.custom_mode)==int(guided_id)
                if kind=="GLOBAL_POSITION_INT":
                    p={"time_boot_s":float(m.time_boot_ms)*.001,
                       "lat_deg":float(m.lat)*1e-7,
                       "lon_deg":float(m.lon)*1e-7,
                       "relative_alt_m":float(m.relative_alt)*.001}
                    if valid_navigation(p["lat_deg"],p["lon_deg"],
                                        p["relative_alt_m"]):
                        valid_pos=True
                        trace.append(p)
                        if p["relative_alt_m"]>=ALTITUDE_TARGET_M:
                            target_reached=True
                if phase=="start" and valid_pos and frame_class==6 and gps_fix>=3:
                    phase="request_guided"
                    conn.mav.set_mode_send(
                        conn.target_system,
                        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                        guided_id,
                    )
                if phase=="request_guided" and guided:
                    phase="request_arm"
                    # Traditional heli MUST have interlock DISABLED to arm.
                    # RC8=1000 is throttle hold (safe), not spool enabled.
                    conn.mav.rc_channels_override_send(
                        conn.target_system,conn.target_component,
                        0,0,0,0,0,0,0,1000,
                    )
                    command(conn,mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,1)
                if phase=="request_arm" and armed:
                    phase="rotor_runup"
                    runup_start=now
                    # Only AFTER positive arm confirmation, enable interlock.
                    conn.mav.rc_channels_override_send(
                        conn.target_system,conn.target_component,
                        0,0,0,0,0,0,0,2000,
                    )
                if phase=="rotor_runup" and now-runup_start>=18.0:
                    phase="request_takeoff"
                    command(conn,mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
                            p7=ALTITUDE_TARGET_M)
                    takeoff_sent=True
                if phase=="request_takeoff" and target_reached:
                    phase="hold"
                    hold_start=trace[-1]["time_boot_s"]
                if phase=="hold" and trace and (
                    trace[-1]["time_boot_s"]-hold_start>=TARGET_WINDOW_S+2
                ):
                    break
            status={
                "start":"GPS_OR_NAVIGATION_UNREADY",
                "request_guided":"GUIDED_MODE_NOT_ENGAGED",
                "request_arm":"ARMING_NOT_CONFIRMED",
                "rotor_runup":"ROTOR_RUNUP_NOT_FINISHED",
                "request_takeoff":"TAKEOFF_TARGET_NOT_REACHED",
                "hold":"HOVER_WINDOW_INCOMPLETE",
            }.get(phase,"UNRESOLVED")
            screen=classify_hold(trace,target_reached) if phase=="hold" else None
            if screen and screen["status"] not in (
                "UNRESOLVED","NO_TAKEOFF_TARGET"):
                status=screen["status"]
            return {
                "status":status, "phase":phase,
                "frame_class":frame_class,
                "gps_fix_type_max":gps_fix,
                "navigation_valid":valid_pos,
                "guided_mode_seen":guided,
                "armed_seen":armed,
                "takeoff_sent":takeoff_sent,
                "target_reached":target_reached,
                "screen":screen,
                "acks":acks,
                "last_messages":notes,
                "trace":trace,
                "spawn_args":args,
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
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    report={
        "backend":"ArduPilot traditional-heli SITL",
        "binary_sha256":hashlib.sha256(args.binary.read_bytes()).hexdigest(),
        "defaults_sha256":hashlib.sha256(args.defaults.read_bytes()).hexdigest(),
        "limitations":"One development-only local SITL launch and MAVLink "
          "experiment with autopilot in loop. Wall-clock command timing "
          "is not deterministic replay. Sampled GPS-derived positions are "
          "not ground truth. Published physical/model validation, "
          "integrator sensitivity and repeatability remain open.",
    }
    try:
        report.update(attempt(args.binary,args.defaults,
                             args.output.parent/"sitl-guided-console.log"))
    except Exception as err:
        report.update({"status":"UNRESOLVED",
                       "error":type(err).__name__+": "+str(err)[:500]})
    atomic_save(args.output,report)
    print(json.dumps({k:v for k,v in report.items()
                      if k not in ("trace","spawn_args")},indent=2))
    # A scientifically negative result is data; do not fail CI on it.
    # Any backend exception is an infrastructure problem that must be repaired.
    if report["status"]=="UNRESOLVED":
        raise SystemExit("SITL guided trial unresolved; inspect artifacts")


if __name__=="__main__":
    main()

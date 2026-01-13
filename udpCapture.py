import socket
import json
import asyncio
import websockets
import re
import time

#用这个来启动脚本& C:/Users/thuam/miniconda3/envs/cut-point/python.exe d:/GameDev/PoseCalibration/udpCapture.py
# 配置端口
HAND_PORT = 9000
HEAD_PORT = 5010
WEB_SOCKET_PORT = 8765

def parse_hand_data(raw_str):
    """解析手部数据 [JointData] Left 1:px,py,pz|qx,qy,qz,qw;..."""
    try:
        if not raw_str.startswith("[JointData]"): return None
        content = raw_str.replace("[JointData] ", "").strip()
        parts = content.split(" ")
        side = parts[0]
        joints_raw = parts[1].split(";")
        
        joints = []
        for j in joints_raw:
            if not j or ":" not in j: continue
            id_split = j.split(":")
            jid = int(id_split[0])
            pos_rot = id_split[1].split("|")
            p = [float(x) for x in pos_rot[0].split(",")]
            q = [float(x) for x in pos_rot[1].split(",")]
            joints.append({"id": jid, "pos": p, "rot": q})
        return {"type": "hand", "side": side, "joints": joints, "ts": time.time()}
    except: return None

import re
import time

_head_re = re.compile(
    r"\[HEAD_PROBE\]\s+frame=(?P<frame>\d+)\s+utc=(?P<utc>[^|]+)\|\s+"
    r"camPos=\((?P<cx>[-\d.]+),(?P<cy>[-\d.]+),(?P<cz>[-\d.]+)\)\s+"
    r"camRot=\((?P<crx>[-\d.]+),(?P<cry>[-\d.]+),(?P<crz>[-\d.]+),(?P<crw>[-\d.]+)\)\s*\|\s+"
    r"xrCenterEye\s+hasPos=(?P<hp>\w+)\s+hasRot=(?P<hr>\w+)\s+"
    r"pos=\((?P<x>[-\d.]+),(?P<y>[-\d.]+),(?P<z>[-\d.]+)\)\s+"
    r"rot=\((?P<qx>[-\d.]+),(?P<qy>[-\d.]+),(?P<qz>[-\d.]+),(?P<qw>[-\d.]+)\)"
)

def parse_head_data(raw_str):
    """
    解析 Unity HeadPoseProbeUdp 发来的文本：
    [HEAD_PROBE] frame=... utc=... | camPos=(x,y,z) camRot=(x,y,z,w) | xrCenterEye hasPos=... hasRot=... pos=(x,y,z) rot=(x,y,z,w)
    """
    try:
        s = raw_str.strip()
        m = _head_re.search(s)
        if not m:
            return None

        def to_bool(v): 
            return True if v.lower() == "true" else False

        cam_pos = [float(m.group("cx")), float(m.group("cy")), float(m.group("cz"))]
        cam_rot = [float(m.group("crx")), float(m.group("cry")), float(m.group("crz")), float(m.group("crw"))]

        xr_pos = [float(m.group("x")), float(m.group("y")), float(m.group("z"))]
        xr_rot = [float(m.group("qx")), float(m.group("qy")), float(m.group("qz")), float(m.group("qw"))]

        return {
            "type": "head_probe",
            "frame": int(m.group("frame")),
            "utc": m.group("utc").strip(),
            "cam": {"pos": cam_pos, "rot": cam_rot},
            "xr": {"hasPos": to_bool(m.group("hp")), "hasRot": to_bool(m.group("hr")), "pos": xr_pos, "rot": xr_rot},
            "ts": time.time(),
        }
    except:
        return None


async def handler(websocket):
    # 初始化 UDP
    hand_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    hand_sock.bind(("0.0.0.0", HAND_PORT))
    hand_sock.setblocking(False)

    head_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    head_sock.bind(("0.0.0.0", HEAD_PORT))
    head_sock.setblocking(False)

    print(f"Monitor active: Hand(9000), Head(5005)")

    while True:
        # 处理手部
        try:
            data, _ = hand_sock.recvfrom(8192)
            parsed = parse_hand_data(data.decode('utf-8', errors='ignore'))
            if parsed: await websocket.send(json.dumps(parsed))
        except BlockingIOError: pass

        # 处理头部
        try:
            data, _ = head_sock.recvfrom(8192)
            parsed = parse_head_data(data.decode('utf-8', errors='ignore'))
            if parsed: await websocket.send(json.dumps(parsed))
        except BlockingIOError: pass
        
        await asyncio.sleep(0.005)

async def main():
    async with websockets.serve(handler, "localhost", WEB_SOCKET_PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
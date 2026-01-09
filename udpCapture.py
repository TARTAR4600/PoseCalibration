import socket
import json
import asyncio
import websockets

HAND_PORT = 9000
WEB_SOCKET_PORT = 8765

def parse_hand_data(raw_str):
    try:
        # Example format: [JointData] Left 1:-0.229,-0.348,0.253|0.930,-0.315,0.063,0.178;...
        if not raw_str.startswith("[JointData]"): return None
        content = raw_str.replace("[JointData] ", "").strip()
        parts = content.split(" ")
        hand_side = parts[0]
        joints_raw = parts[1].split(";")
        
        joints = []
        for j in joints_raw:
            if not j or ":" not in j: continue
            id_split = j.split(":")
            joint_id = id_split[0]
            # Split position and rotation by |
            pos_rot = id_split[1].split("|")
            pos_vals = pos_rot[0].split(",")
            
            joints.append({
                "id": int(joint_id),
                "pos": [float(pos_vals[0]), float(pos_vals[1]), float(pos_vals[2])]
            })
        return {"type": "hand", "side": hand_side, "joints": joints}
    except Exception as e:
        return None

async def handler(websocket):
    print(f"Client connected to WebSocket")
    hand_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    hand_sock.bind(("0.0.0.0", HAND_PORT))
    hand_sock.setblocking(False)

    while True:
        try:
            data, addr = hand_sock.recvfrom(4096)
            decoded = data.decode('utf-8', errors='ignore')
            parsed = parse_hand_data(decoded)
            if parsed:
                await websocket.send(json.dumps(parsed))
        except BlockingIOError:
            await asyncio.sleep(0.001) # High frequency for XR data
        except websockets.ConnectionClosed:
            break

async def main():
    async with websockets.serve(handler, "localhost", WEB_SOCKET_PORT):
        print(f"Server started. WebSocket: ws://localhost:{WEB_SOCKET_PORT}")
        print(f"Listening for UDP Hand data on port {HAND_PORT}...")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
import socket, wave, json, os
from vosk import Model, KaldiRecognizer

HOME = "/data/data/com.termux/files/home"
MODEL_PATH = f"{HOME}/.shortcuts/vosk-model"

model = Model(MODEL_PATH)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("127.0.0.1", 2700))
server.listen(5)

while True:
    try:
        conn, addr = server.accept()
        wav_path = conn.recv(1024).decode("utf-8").strip()
        
        if not os.path.exists(wav_path):
            conn.sendall(b"")
            conn.close()
            continue

        wf = wave.open(wav_path, "rb")
        rec = KaldiRecognizer(model, wf.getframerate())
        
        while True:
            data = wf.readframes(4000)
            if len(data) == 0: break
            rec.AcceptWaveform(data)
            
        result = json.loads(rec.FinalResult())
        text = result.get("text", "")
        
        conn.sendall(text.encode("utf-8"))
        conn.close()
    except Exception as e:
        try:
            conn.sendall(b"")
            conn.close()
        except: pass

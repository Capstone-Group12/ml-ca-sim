# Python Machine Learning (ML) Models

FastAPI service exposing the port-probing detector.

## Quickstart

```bash
pip install -r requirements.txt
python main.py  # serves on http://localhost:8001
```

Example request payload:

```json
{
  "dst_port": 22,
  "src_port": 51515,
  "inter_arrival_time": 0.5,
  "stream_1_count": 12,
  "l4_tcp": true,
  "l4_udp": false
}
```

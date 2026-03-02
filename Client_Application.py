# client 

class client:
    def __init__(self):
        pass


"""

1. command message: 
{
  "header": {
    "msgType": "COMMAND",
    "command": "CREATE",
    "version": "MMMP/1.0",
    "seqNo": 2001,
    "senderId": "client_23",
    "timestamp": "2026-02-27T10:02:15Z",
    "bodyLength": 32
  },
  "body": {
    "group-name": "csc3002f",
    "members":["client_232", "client_222"]
  }
}

2. control message example

{
  "header": {
    "msgType": "CONTROL",
    "command": "ACK",
    "status_code":2,
    "version": "MMMP/1.0",
    "seqNo": 2001,
    "senderId": "server",
    "timestamp": "2026-02-27T10:02:15Z",
    "bodyLength": 0
  }
}


3. Data message

{
  "header": {
    "msgType": "DATA",
    "command": "GTEXT_MESSAGE",
    "version": "MMMP/1.0",
    "seqNo": 2002,
    "senderId": "client_23"
    "timestamp": "2026-02-27T10:02:15Z",
    "bodyLength": 32
  },
  "body": {
    "group-name": "csc3002f",
    "message":"Hello everyone."
  }
}


"""
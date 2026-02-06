from app.extensions import socketio

def broadcast(room, event, payload): socketio.emit(event, payload, room=room)

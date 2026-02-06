"""Socket.IO broadcast utilities.

Some segments call `broadcast_room_event(room, payload)`.
In dev or minimal deployments, SocketIO may be disabled.
This function becomes a safe no-op in that case.
"""

from __future__ import annotations

from typing import Any, Dict

from app.extensions import socketio


def broadcast_room_event(
    room: str,
    payload: Dict[str, Any],
    event: str = "event",
) -> bool:
    """Broadcast an event to a room.

    Returns True if emitted via SocketIO, False if SocketIO is disabled.
    """
    if socketio is None:
        return False

    try:
        socketio.emit(event, payload, room=room)
        return True
    except Exception:
        return False


def broadcast_feed_event(
    event: str,
    payload: Dict[str, Any],
    namespace: str = "/",
) -> bool:
    """Broadcast an event to all connected clients.

    Older segments sometimes refer to a feed-level broadcaster.
    """
    if socketio is None:
        return False

    try:
        socketio.emit(event, payload, broadcast=True, namespace=namespace)
        return True
    except Exception:
        return False

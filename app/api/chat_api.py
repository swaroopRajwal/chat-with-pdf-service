import socketio

from app.services.chat_service import sio

socket_app = socketio.ASGIApp(socketio_server=sio, socketio_path="/chat/socket.io")

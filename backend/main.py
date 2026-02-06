import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Must be 0.0.0.0 so emulator can reach it via 10.0.2.2
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLIPTRYBE_ENV", "dev") == "dev"

    app.run(host=host, port=port, debug=debug)
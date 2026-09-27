import sys
import uvicorn
from app.config import settings

def main():
    """CLI entrypoint for running Domus server."""
    port = settings.PORT
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    print(f"Starting Domus PWA server on port {port}...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)

if __name__ == "__main__":
    main()

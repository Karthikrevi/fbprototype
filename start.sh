
#!/bin/bash
# Kill any existing Python processes
pkill -f "python main.py" || true
sleep 2
# Start the Flask app
python main.py

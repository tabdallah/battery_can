from flask import Flask, render_template
import threading
import can
import cantools
import time

# Create the Flask app
app = Flask(__name__)

# This dictionary will hold the most recent values of each signal
signal_values = {}

def update_signal_values(bus, db):
    # Specify the message IDs you're interested in
    interested_ids = {0x123, 0x456, 0x789}

    while True:
        try:
            message = bus.recv(1.0)  # Timeout after 1 second if no message is received
            if message is not None and message.arbitration_id in interested_ids:
                # Decode the message using the DBC file
                data = db.decode_message(message.arbitration_id, message.data)

                # Convert enum signals to their enum strings and round non-enum signals
                for signal_name, signal_value in data.items():
                    signal = db.get_signal_by_name(signal_name)
                    if signal.is_multiplexer:
                        data[signal_name] = signal.choices[signal_value]
                    else:
                        data[signal_name] = round(signal_value, 3)

                # Update the signal values
                signal_values.update(data)
        except Exception as e:
            print(f"Error while receiving CAN message: {e}")
        #time.sleep(0.01)  # Prevent this loop from running too fast

@app.route('/')
def index():
    # Render the index.html template, passing in the signal values
    return render_template('index.html', signal_values=signal_values)

if __name__ == '__main__':
    # Connect to the CAN bus
    bus = can.interface.Bus(channel='can0', bustype='socketcan')

    # Load the DBC file
    db = cantools.db.load_file('your_dbc_file.dbc')

    # Start a background thread to update the signal values
    threading.Thread(target=update_signal_values, args=(bus, db), daemon=True).start()

    # Start the Flask server
    app.run(host='0.0.0.0')
#!/usr/bin/env python3
"""
MQTT Subscriber for file transfer experiments
Run this on the third computer
"""

import paho.mqtt.client as mqtt
import time
import json
import os
import sys

class MQTTSubscriber:
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client()
        self.setup_callbacks()
        self.received_files = 0
        self.results = []
        
    def setup_callbacks(self):
        def on_connect(client, userdata, flags, rc):
            print(f"Subscriber connected with result code {rc}")
            # Subscribe to file transfer topic
            client.subscribe("file_transfer")
            
        def on_message(client, userdata, msg):
            try:
                message = json.loads(msg.payload.decode())
                filename = message['filename']
                filesize = message['filesize']
                iteration = message['iteration']
                
                # Convert hex data back to binary
                file_data = bytes.fromhex(message['data'])
                
                # Verify file size
                if len(file_data) == filesize:
                    print(f"Received {filename} (iteration {iteration}) - {filesize} bytes")
                    self.received_files += 1
                else:
                    print(f"Error: File size mismatch for {filename}")
                    
            except Exception as e:
                print(f"Error processing message: {e}")
                
        self.client.on_connect = on_connect
        self.client.on_message = on_message
        
    def connect(self):
        self.client.connect(self.broker_host, self.broker_port, 60)
        self.client.loop_start()
        
    def wait_for_files(self, expected_count):
        """Wait for expected number of files to be received"""
        print(f"Waiting for {expected_count} files...")
        start_time = time.time()
        
        while self.received_files < expected_count:
            time.sleep(0.1)
            
        end_time = time.time()
        total_time = end_time - start_time
        print(f"Received {self.received_files} files in {total_time:.2f} seconds")
        
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

def main():
    if len(sys.argv) < 2:
        print("Usage: python mqtt_subscriber.py <broker_host> [broker_port]")
        print("Example: python mqtt_subscriber.py 192.168.1.100")
        sys.exit(1)
        
    broker_host = sys.argv[1]
    broker_port = int(sys.argv[2]) if len(sys.argv) > 2 else 1883
    
    subscriber = MQTTSubscriber(broker_host, broker_port)
    subscriber.connect()
    
    # Wait a moment for connection
    time.sleep(1)
    
    # Calculate expected file count
    expected_files = 10000 + 1000 + 100 + 10  # Total from all experiments
    print(f"Expected to receive {expected_files} files")
    
    try:
        subscriber.wait_for_files(expected_files)
        print("All files received successfully!")
        
    except KeyboardInterrupt:
        print("Subscriber stopped by user")
    finally:
        subscriber.disconnect()

if __name__ == "__main__":
    main()

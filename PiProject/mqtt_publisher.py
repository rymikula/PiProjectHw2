#!/usr/bin/env python3
"""
MQTT Publisher for file transfer experiments
Run this on the second computer
"""

import paho.mqtt.client as mqtt
import time
import json
import os
import sys
import csv

class MQTTPublisher:
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client()
        self.setup_callbacks()
        self.results = []
        
    def setup_callbacks(self):
        def on_connect(client, userdata, flags, rc):
            print(f"Publisher connected with result code {rc}")
            
        def on_publish(client, userdata, mid):
            print(f"Message {mid} published")
            
        self.client.on_connect = on_connect
        self.client.on_publish = on_publish
        
    def connect(self):
        self.client.connect(self.broker_host, self.broker_port, 60)
        self.client.loop_start()
        
    def publish_file(self, file_path, topic, qos=1, iterations=1):
        """Publish a file multiple times and measure performance"""
        if not os.path.exists(file_path):
            print(f"File {file_path} not found!")
            return
            
        file_size = os.path.getsize(file_path)
        print(f"Publishing {file_path} ({file_size} bytes) {iterations} times with QoS {qos}")
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
            
        for i in range(iterations):
            start_time = time.time()
            
            # Create message with metadata
            message = {
                'filename': os.path.basename(file_path),
                'filesize': file_size,
                'iteration': i + 1,
                'data': file_data.hex()  # Convert binary to hex string for JSON
            }
            
            # Publish the message
            result = self.client.publish(topic, json.dumps(message), qos=qos)
            
            # Wait for publish to complete
            result.wait_for_publish()
            
            end_time = time.time()
            transfer_time = end_time - start_time
            throughput = file_size / transfer_time if transfer_time > 0 else 0
            
            # Record results
            result_data = {
                'file': os.path.basename(file_path),
                'file_size': file_size,
                'iteration': i + 1,
                'transfer_time': transfer_time,
                'throughput': throughput,
                'qos': qos
            }
            self.results.append(result_data)
            
            print(f"Iteration {i+1}: {transfer_time:.4f}s, {throughput:.2f} bytes/s")
            
    def save_results(self, filename="mqtt_results.csv"):
        """Save results to CSV file"""
        with open(filename, 'w', newline='') as f:
            if self.results:
                writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
                writer.writeheader()
                writer.writerows(self.results)
        print(f"Results saved to {filename}")
        
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

def main():
    if len(sys.argv) < 2:
        print("Usage: python mqtt_publisher.py <broker_host> [broker_port]")
        print("Example: python mqtt_publisher.py 192.168.1.100")
        sys.exit(1)
        
    broker_host = sys.argv[1]
    broker_port = int(sys.argv[2]) if len(sys.argv) > 2 else 1883
    
    publisher = MQTTPublisher(broker_host, broker_port)
    publisher.connect()
    
    # Wait a moment for connection
    time.sleep(1)
    
    # File paths (adjust as needed)
    data_dir = "DataFiles"
    files = [
        ("100B", 10000),      # 100B file, 10k iterations
        ("10KB", 1000),       # 10KB file, 1k iterations  
        ("1MB", 100),         # 1MB file, 100 iterations
        ("10MB", 10)          # 10MB file, 10 iterations
    ]
    
    topic = "file_transfer"
    qos = 1  # Change to 2 for QoS 2 experiments
    
    try:
        for filename, iterations in files:
            file_path = os.path.join(data_dir, filename)
            publisher.publish_file(file_path, topic, qos, iterations)
            
        publisher.save_results(f"mqtt_qos{qos}_results.csv")
        
    except KeyboardInterrupt:
        print("Publisher stopped by user")
    finally:
        publisher.disconnect()

if __name__ == "__main__":
    main()

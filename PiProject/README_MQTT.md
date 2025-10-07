# MQTT File Transfer Experiment

This directory contains Python scripts for conducting MQTT file transfer experiments as described in the assignment.

## Files

- `mqtt_publisher.py` - MQTT publisher (run on computer 2) 
- `mqtt_subscriber.py` - MQTT subscriber (run on computer 3)

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure you have an MQTT broker running (e.g., Mosquitto)
3. Make sure all computers are on the same network

## Running the Experiment

### Step 1: Start the Subscriber  
On computer 3:
```bash
python mqtt_subscriber.py <broker_ip_address>
```
Example: `python mqtt_subscriber.py 192.168.1.100`

### Step 2: Start the Publisher
On computer 2:
```bash
python mqtt_publisher.py <broker_ip_address>
```
Example: `python mqtt_publisher.py 192.168.1.100`

## Experiment Details

The publisher will automatically:
- Transfer 100B file 10,000 times
- Transfer 10KB file 1,000 times  
- Transfer 1MB file 100 times
- Transfer 10MB file 10 times

Results are saved to `mqtt_qos1_results.csv` (or `mqtt_qos2_results.csv` for QoS 2).

## Modifying QoS

To test QoS 2, edit `mqtt_publisher.py` and change:
```python
qos = 2  # Change from 1 to 2
```

## Notes

- Make sure the DataFiles directory contains the test files (100B, 10KB, 1MB, 10MB)
- The experiment will take some time to complete (especially the 10,000 iterations of the 100B file)
- Results include transfer time and throughput calculations for each file transfer

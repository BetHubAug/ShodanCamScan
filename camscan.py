import os
import socket
import shodan
import cv2

# Disable SSL warnings (for testing purposes only)
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def get_environment_variable(var_name, prompt):
    value = os.getenv(var_name)
    if not value:
        value = input(prompt)
        os.environ[var_name] = value
    return value

def scan_for_cameras(api_key):
    """Scans the specified IP range for open cameras.

    Args:
        api_key: The Shodan API key.

    Returns:
        A list of camera IP addresses and their corresponding titles.
    """
    try:
        # Initialize Shodan API
        api = shodan.Shodan(api_key)

        # Search Shodan for cameras
        results = api.search(query='http.title:"Axis Camera" OR http.title:"Foscam Camera" OR http.title:"D-Link Camera" OR http.title:"Hikvision Camera" OR http.title:"Netgear Camera"')

        # Extract camera IP addresses and titles
        cameras = [(result['ip_str'], result['http']['title']) for result in results['matches']]

        return cameras

    except Exception as e:
        print(f"Error scanning for cameras: {e}")
        return []

def get_stream_url(ip_address):
    """Gets the stream URL from the camera.

    Args:
        ip_address: The IP address of the camera.

    Returns:
        The stream URL if successful, None otherwise.
    """
    try:
        # Connect to the camera
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip_address, 80))

        # Send a HTTP request to retrieve the camera's stream
        request = f"GET / HTTP/1.1\r\nHost: {ip_address}\r\n\r\n"
        sock.sendall(request.encode())

        # Receive the response
        response = sock.recv(4096).decode()

        # Check if the response contains a stream URL
        if "rtsp://" in response:
            # Extract the stream URL
            stream_url = response.split("rtsp://")[1].split('"')[0]
            return f"rtsp://{stream_url}"

        else:
            return None

    except Exception as e:
        print(f"Error getting stream URL: {e}")
        return None

    finally:
        sock.close()

def watch_stream(stream_url):
    """Watches the camera stream.

    Args:
        stream_url: The URL of the camera stream.
    """
    try:
        # Use OpenCV to watch the stream
        cap = cv2.VideoCapture(stream_url)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            cv2.imshow('Camera Stream', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    except Exception as e:
        print(f"Error watching stream: {e}")

def main():
    # Define the Shodan API key
    api_key = get_environment_variable('SHODAN_API_KEY', 'Enter your Shodan API key: ')

    # Scan for cameras
    cameras = scan_for_cameras(api_key)

    # Get stream URLs
    for ip_address, title in cameras:
        print(f"Getting stream URL for {title} at {ip_address}...")
        stream_url = get_stream_url(ip_address)
        if stream_url:
            print(f"Stream URL: {stream_url}")
            watch_stream(stream_url)
        else:
            print(f"Failed to get stream URL for {title} at {ip_address}")

if __name__ == "__main__":
    main()

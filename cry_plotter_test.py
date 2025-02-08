import matplotlib.pyplot as plt
from collections import Counter
import datetime
import io
from PIL import Image

def plotCryLogGraph():
    # Read the contents of the text file
    with open('crying_log.txt', 'r') as file:
        data = file.readlines()

    # Get the current time and generate the last 24 hours
    now = datetime.datetime.now()
    last_24_hours = [(now - datetime.timedelta(hours=i)).strftime('%H:00') for i in range(24)]
    last_24_hours.reverse()  # Make the list chronological from 24 hours ago to now

    # Extract the hour from each log line
    hours = []
    for line in data:
        # Split the line and extract the time
        parts = line.split("Detected at: ")
        if len(parts) == 2:
            time_str = parts[1].strip().rstrip('.')  # Remove the trailing period
            time_obj = datetime.datetime.strptime(time_str, "%H:%M on %m-%d")
            hours.append(time_obj.strftime('%H:00'))  # Extract and format only the hour

    # Count the occurrences of each hour
    hour_counts = Counter(hours)

    # Ensure all hours from the last 24 hours are included with a count of 0 if no detections
    counts = [hour_counts.get(hour, 0) for hour in last_24_hours]

    # Plot the data
    plt.figure(figsize=(10, 5))
    plt.bar(last_24_hours, counts, color='skyblue')
    plt.xlabel('Hour')
    plt.ylabel('Number of Detections')
    plt.title('Baby Crying Detections by Hour (Last 24 Hours)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    # Save the plot to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img = Image.open(buf)
    return img
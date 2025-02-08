import cv2
from PIL import Image
import torch
from transformers import OwlViTProcessor, OwlViTForObjectDetection

# Initialize the processor and model
processor = OwlViTProcessor.from_pretrained("google/owlvit-base-patch32")
model = OwlViTForObjectDetection.from_pretrained("google/owlvit-base-patch32")

# Open a connection to the webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

def constructClassList(filename):
    file = open(filename, "r")
    outputList = []
    # Read each line one by one
    for line in file:
        cat = line.strip()
        if cat[0] in ["a", "e", "i", "o", "u"]:
            outputList.append("picture of an " + cat)  # .strip() to remove newline characters
        else:
            outputList.append(" picture of a " + cat)
    # Close the file
    file.close()
    return [outputList]

def is_overlapping(box1, box2):
    # Unpack the bounding boxes
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2
    print(x1_min, x1_max)
    print(x2_min, x2_max)
    # Check if there is an overlap
    if x1_min < x2_max and x1_max > x2_min and y1_min < y2_max and y1_max > y2_min:
        return True
    return False

text_labels = constructClassList("Dangerous_Objects.txt")

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame.")
        break

    # Convert the frame to a PIL image
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    # Process the image and perform object detection
    inputs = processor(text=text_labels, images=image, return_tensors="pt")
    outputs = model(**inputs)

        # Target image sizes (height, width) to rescale box predictions [batch_size, 2]
    target_sizes = torch.tensor([(image.height, image.width)])
    # Convert outputs (bounding boxes and class logits) to Pascal VOC format (xmin, ymin, xmax, ymax)
    results = processor.post_process_grounded_object_detection(
        outputs=outputs, target_sizes=target_sizes, threshold=0.1, text_labels=text_labels
    )
    # Retrieve predictions for the first image for the corresponding text queries
    result = results[0]
    boxes, scores, result_labels = result["boxes"], result["scores"], result["text_labels"]
    
    baby_box = None
    baby_score = 0
    crib_box = None
    crib_score = 0
    # Draw the bounding boxes and labels on the frame
    for box, score, text_label in zip(boxes, scores, result_labels):
        if score.item() >= .2 or 'crib' in text_label:
            if ("baby" in text_label or "infant" in text_label or "person" in text_label or "child" in text_label) and score.item() > baby_score:
                baby_box = box
                baby_score = score.item()
            if "crib" in text_label and score.item() > crib_score:
                crib_box = box
                crib_score = score.item()
            box = [round(i, 2) for i in box.tolist()]
            cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (255, 0, 0), 2)
            cv2.putText(frame, f"{text_label[14:]}: {round(score.item(), 3)}", (int(box[0]), int(box[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

    if crib_box != None and baby_box != None:
        print("WE GOT BOTH")
        if not is_overlapping(crib_box, baby_box):
            cv2.putText(frame, "DANGER", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            print("DANGER")
        else:
            cv2.putText(frame, "SAFE", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            print("SAFE")
    # Display the resulting frame
    cv2.imshow('Webcam Object Detection', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, release the capture and close windows
cap.release()
cv2.destroyAllWindows()
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

text_labels = [["person", "cat", "lamp", "dog"]]

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
    print(results)
    # Retrieve predictions for the first image for the corresponding text queries
    result = results[0]
    boxes, scores, result_labels = result["boxes"], result["scores"], result["text_labels"]

    # Draw the bounding boxes and labels on the frame
    for box, score, text_label in zip(boxes, scores, result_labels):
        box = [round(i, 2) for i in box.tolist()]
        cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (255, 0, 0), 2)
        cv2.putText(frame, f"{text_label}: {round(score.item(), 3)}", (int(box[0]), int(box[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

    # Display the resulting frame
    cv2.imshow('Webcam Object Detection', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, release the capture and close windows
cap.release()
cv2.destroyAllWindows()
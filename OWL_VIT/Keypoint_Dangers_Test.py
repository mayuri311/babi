import cv2
import torch
import numpy as np
import datetime
from PIL import Image
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2 import model_zoo
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog
print("hurry tf up")
from transformers import OwlViTProcessor, OwlViTForObjectDetection

def constructDangerousObjectsList(filename):
    file = open(filename, "r")
    outputList = []
    # Read each line one by one
    for line in file:
        outputList.append("image of a " + line.strip())  # .strip() to remove newline characters
    # Close the file
    file.close()
    return [outputList]

# Initialize webcam feed using OpenCV
cap = cv2.VideoCapture(0)  # 0 for default camera

# Load the Detectron2 model configuration and weights
cfg = get_cfg()
cfg.merge_from_file(model_zoo.get_config_file("COCO-Keypoints/keypoint_rcnn_R_50_FPN_3x.yaml"))
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5  # Set threshold for this model
cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-Keypoints/keypoint_rcnn_R_50_FPN_3x.yaml")
cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"  # Use GPU if available

predictor = DefaultPredictor(cfg)


# Load OwlViT model from Hugging Face
processor = OwlViTProcessor.from_pretrained("google/owlvit-base-patch32")
model = OwlViTForObjectDetection.from_pretrained("google/owlvit-base-patch32")

# List of dangerous objects to detect with OwlViT
text_labels = constructDangerousObjectsList("Dangerous_Objects.txt")

counter = -1
while True:
    counter += 1
    ret, frame = cap.read()  # Read a frame from the webcam
    if not ret:
        break

    if counter == 0:
         # Pass the frame through Detectron2 model for inference
        detectron_outputs = predictor(frame)

    # Visualize the outputs on the frame
    v = Visualizer(frame[:, :, ::-1], MetadataCatalog.get(cfg.DATASETS.TRAIN[0]), scale=1.2)
    out_detectron = v.draw_instance_predictions(detectron_outputs["instances"].to("cpu"))

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
    out_detectron_img = out_detectron.get_image()[:, :, ::-1]
    out_detectron_img = np.ascontiguousarray(out_detectron_img, dtype=np.uint8)
    for box, score, text_label in zip(boxes, scores, result_labels):
        box = [round(i, 2)*1.2 for i in box.tolist()]

        cv2.rectangle(out_detectron_img, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (255, 0, 0), 2)
        cv2.putText(out_detectron_img, f"{text_label[11:]}: {round(score.item(), 3)}", (int(box[0]), int(box[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
    

    # Display the resulting frame
    cv2.imshow('Webcam Object Detection', out_detectron_img)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        breakg

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()
import cv2
import torch
from PIL import Image
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2 import model_zoo
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog

from transformers import OwlViTProcessor, OwlViTForObjectDetection

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

while True:
    ret, frame = cap.read()  # Read a frame from the webcam
    if not ret:
        break

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




    for box, score, label in zip(results["boxes"], results["scores"], results["text_labels"]):
        box = [int(b) for b in box.tolist()]
        label_text = dangerous_objects[label]
        score_text = f"{score:.2f}"
        
        # Draw bounding box for the detected dangerous object
        cv2.rectangle(out_detectron.get_image()[:, :, ::-1], (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
        cv2.putText(out_detectron.get_image()[:, :, ::-1], f"{label_text}: {score_text}", (box[0], box[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # Display the processed frame with both keypoints (Detectron2) and dangerous object detection (Owl-ViT)
    cv2.imshow("Keypoint and Object Detection", out_detectron.get_image()[:, :, ::-1])

    # Press 'q' to exit the webcam loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()



def constructDangerousObjectsList(filename):
    file = open(filename, "r")
    outputList = []
    # Read each line one by one
    for line in file:
        outputList.append(line.strip())  # .strip() to remove newline characters
    # Close the file
    file.close()
    print(outputList)
    return outputList
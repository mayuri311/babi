import cv2
import torch
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2 import model_zoo
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog

# Initialize webcam feed using OpenCV
cap = cv2.VideoCapture(0)  # 0 for default camera

# Load the Detectron2 model configuration and weights
cfg = get_cfg()
cfg.merge_from_file(model_zoo.get_config_file("COCO-Keypoints/keypoint_rcnn_R_50_FPN_3x.yaml"))
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5  # Set threshold for this model
cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-Keypoints/keypoint_rcnn_R_50_FPN_3x.yaml")
cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"  # Use GPU if available

predictor = DefaultPredictor(cfg)

while True:
    ret, frame = cap.read()  # Read a frame from the webcam
    if not ret:
        break

    # Pass the frame through Detectron2 model for inference
    outputs = predictor(frame)

    # Visualize the outputs on the frame
    v = Visualizer(frame[:, :, ::-1], MetadataCatalog.get(cfg.DATASETS.TRAIN[0]), scale=1.2)
    out = v.draw_instance_predictions(outputs["instances"].to("cpu"))

    # Display the processed frame
    cv2.imshow("Detectron2 Output", out.get_image()[:, :, ::-1])
    
    # Press 'q' to exit the webcam loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()
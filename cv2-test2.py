import cv2
import torch
import detectron2
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog

# Initialize Detectron2
cfg = get_cfg()
cfg.merge_from_file("detectron2/configs/COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml")
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5  # Confidence threshold
cfg.MODEL.WEIGHTS = "detectron2://COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x/137849600/model_final_f10217.pkl"
cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

predictor = DefaultPredictor(cfg)

# OpenCV Video Capture
cap = cv2.VideoCapture(0)  # Change to video file path if needed

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # Convert image to Detectron2 format
    outputs = predictor(frame)
    instances = outputs["instances"]
    
    # Filter for person class (COCO category 0 is 'person')
    persons = instances[instances.pred_classes == 0]
    
    # Visualize results
    v = Visualizer(frame[:, :, ::-1], MetadataCatalog.get(cfg.DATASETS.TRAIN[0]), scale=1.2)
    v = v.draw_instance_predictions(persons.to("cpu"))
    result = v.get_image()[:, :, ::-1]
    
    # Show output
    cv2.imshow("Person Detection", result)
    
    # Exit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

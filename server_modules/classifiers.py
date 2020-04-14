import pickle
import numpy
import copy
import json
import cv2
import os

class ImageClassifier:
    def __init__(self, config_file="image_classifier_config.json"):
        with open(config_file, "r") as config_file_object:
            self.__config = json.loads(config_file_object.read())
        self.__distance_calibrated = False
        self.__distance_reference = {}

    def __get_distance(self, classification_data):
        distance = None
        classification_label, (x, y, w, h) = classification_data
        if (self.__distance_calibrated and classification_label in self.__distance_reference.keys()):
            known_width, known_distance = self.__distance_reference[classification_label]
            distance = round((known_width*known_distance*self.__distance_reference[".inch-to-step-conv"])/w)
        return distance

    def __get_relative_postion(self, image_width, image_height, classification_data):
        classification_label, (x, y, w, h) = classification_data
        rel_x = x+(w//2)
        rel_y = y+(h//2)
        if (rel_x < image_width*(30/100)):
            pos_hint = "towards your left"
        elif (rel_x <= image_width*(45/100)):
            pos_hint = "slighly to your left"
        elif (rel_x < image_width*(55/100)):
            pos_hint = "ahead"
        elif (rel_x <= image_width*(70/100)):
            pos_hint = "slightly to your right"
        else:
            pos_hint = "towards your right"
        return pos_hint

    def __get_person_name(self, person_data, face_classifications):
        classification_label, (X, Y, W, H) = person_data
        for (name, (x, y, w, h)) in face_classifications:
            center_x = x+(w/2)
            center_y = x+(h/2)
            if (center_x in range(X, X+W) and center_y in range(Y, Y+H)):
                person_data[0] = str(name)
                break
        return person_data

    def load_image(self, file_path=None):
        return cv2.imread(file_path)

    def save_image(self, image_object, file_path=None):
        cv2.imwrite(file_path, image_object)

    def load_object_classifier(self):
        with open(self.__config["objectClassifier"]["labelsPath"], "r") as labels_file_object:
            self.__object_detection_labels = labels_file_object.read().split("\n")
        self.__object_detector = cv2.dnn.readNetFromDarknet(
            self.__config["objectClassifier"]["configPath"],
            self.__config["objectClassifier"]["weightsPath"]
        )
        layer_names = self.__object_detector.getLayerNames()
        self.__object_detection_layer_names = [layer_names[i[0]-1] for i in self.__object_detector.getUnconnectedOutLayers()]

    def classify_objects(self, image_object, image_width=400, image_height=400, min_confidence=0.5, threshold=0.3):
        result = []
        classification_boxes = []
        classification_class_ids = []
        classification_confidences = []
        box_factor = numpy.array([image_width, image_height, image_width, image_height])
        image_blob = cv2.dnn.blobFromImage(
            image_object,
            1.0/255.0,
            (416, 416),
            swapRB=True,
            crop=False
        )
        self.__object_detector.setInput(image_blob)
        layer_outputs = self.__object_detector.forward(copy.copy(self.__object_detection_layer_names))
        for layer_detections in layer_outputs:
            for detection in layer_detections:
                scores = detection[5:]
                class_id = numpy.argmax(scores)
                confidence = float(scores[class_id])
                if (confidence >= min_confidence):
                    (center_x, center_y, width, heigth) = (detection[:4] * box_factor).astype("int")
                    x = int(center_x-(width/2))
                    y = int(center_y-(heigth/2))
                    classification_class_ids.append(class_id)
                    classification_confidences.append(confidence)
                    classification_boxes.append([x, y, int(width), int(heigth)])
        idxs = cv2.dnn.NMSBoxes(
            classification_boxes,
            classification_confidences,
            min_confidence,
            threshold
        )
        if (len(idxs) > 0):
            for i in idxs.flatten():
                result.append([self.__object_detection_labels[classification_class_ids[i]], list(classification_boxes[i][:4])])
        return result

    def load_face_classifier(self):
        self.__face_detector = cv2.dnn.readNetFromCaffe(
            self.__config["faceClassifier"]["protoPath"], 
            self.__config["faceClassifier"]["modelPath"])
        self.__face_detection_data_embedder = cv2.dnn.readNetFromTorch(self.__config["faceClassifier"]["embedPath"])
        with open(self.__config["faceClassifier"]["recogPath"], "rb") as recog_file_object:
            self.__face_detection_image_recognizer = pickle.loads(recog_file_object.read())
        with open(self.__config["faceClassifier"]["encoderPath"], "rb") as encoder_file_object:
            self.__face_detection_label_encoder = pickle.loads(encoder_file_object.read())

    def classify_faces(self, image_object, image_width=400, image_height=400, min_confidence=0.5):
        box_factor = numpy.array([image_width, image_height, image_width, image_height])
        result = []
        image_blob = cv2.dnn.blobFromImage(
            cv2.resize(image_object, (300, 300)),
            1.0,
            (300,300),
            (104.0, 117.0, 123.0),
            swapRB=False,
            crop=False
            )
        self.__face_detector.setInput(image_blob)
        image_detections = self.__face_detector.forward()
        for i in range(image_detections.shape[2]):
            confidence = image_detections[0, 0, i, 2]
            if confidence > min_confidence:
                x0, y0, x1, y1 = (image_detections[0, 0, i, 3:7] * box_factor).astype("int")
                face_image = image_object[y0:y1, x0:x1]
                if min(face_image.shape[:2]) < 20:
                    continue
                face_image_blob = cv2.dnn.blobFromImage(
                    face_image, 
                    1.0/255, 
                    (96, 96), 
                    (0, 0, 0),
                    swapRB=True, 
                    crop=False)
                self.__face_detection_data_embedder.setInput(face_image_blob)
                visual_encoder = self.__face_detection_data_embedder.forward()
                prediction = self.__face_detection_image_recognizer.predict_proba(visual_encoder)[0]
                name = self.__face_detection_label_encoder.classes_[numpy.argmax(prediction)]
                result.append([name, (x0, y0, x1-x0, y1-y0)])
        return result

    def load_classifier(self):
        self.load_object_classifier()
        self.load_face_classifier()

    def classify(self, image_object, min_confidence=0.5):
        (image_height, image_width) = image_object.shape[:2]
        classified_objects = self.classify_objects(image_object, image_width, image_height, min_confidence)
        classified_faces = self.classify_faces(image_object, image_width, image_height, min_confidence)
        result = []
        for i in range(len(classified_objects)):
            classification_data = classified_objects[i]
            print(classification_data)
            if (classification_data[0].lower().strip() == "person"):
                classification_data = self.__get_person_name(classification_data, classified_faces)
            classification_result = {
                "label": classification_data[0],
                "bounding_box": classification_data[1],
                "distance": self.__get_distance(classification_data),
                "pos_hint": self.__get_relative_postion(image_width, image_height, classification_data)
            }
            result.append(classification_result)
        return result

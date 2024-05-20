import sys
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QHBoxLayout, QTabWidget, QPushButton, QLineEdit, QSpacerItem, QSizePolicy


from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen
from PyQt5.QtCore import QTimer, Qt
import cv2
from transformers import YolosImageProcessor, YolosForObjectDetection
import torch

import numpy as np
from PyQt5.QtCore import pyqtSignal
from PIL import Image 



import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication


import os
from datetime import datetime

from PDF import create_pdf


# Function to draw rectangles and labels on the frame
def draw_boxes(image, results, model):
    font = cv2.FONT_HERSHEY_SIMPLEX
    for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
        #if model.config.id2label[label.item()] == "person" :  # Assuming person label index is 1
        box = [round(i, 2) for i in box.tolist()]
        cv2.rectangle(image, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 255, 0), 2)
            
            # Add label and score above the rectangle
        label_text = f"Label: {model.config.id2label[label.item()]}"
        score_text = f"Score: {score.item():.2f}"
        cv2.putText(image, label_text, (int(box[0]), int(box[1]) - 10), font, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(image, score_text, (int(box[0]), int(box[1]) - 30), font, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            
    return image


def send_incident(nature, image_path, pdf_path, mail):
    sender = "mailtrap@demomailtrap.com"
    receiver = mail

    # Create a multipart message
    message = MIMEMultipart()
    message["Subject"] = f"Incident reported: {nature}"
    message["To"] = receiver
    message["From"] = sender

    # Add text to the email body
    body = f"An incident of type '{nature}' happened on DANGER AI. Please find the picture below."
    message.attach(MIMEText(body, "plain"))

    # Attach image to the email
    with open(image_path, "rb") as fp:
        img_data = fp.read()
    image = MIMEImage(img_data, name="incident_image.jpg")
    message.attach(image)

    with open(pdf_path, "rb") as pdf_file:
        pdf_data = pdf_file.read()
    pdf_attachment = MIMEApplication(pdf_data)
    pdf_attachment.add_header('Content-Disposition', 'attachment', filename="incident_report.pdf")
    message.attach(pdf_attachment)

    # Send the email
    with smtplib.SMTP("live.smtp.mailtrap.io", 587) as server:
        server.starttls()
        server.login("api", "20508a86ed68998dc54a0179fa499e9b")
        server.sendmail(sender, receiver, message.as_string())


def save_pixmap(pixmap,folder):
        
        # Ensure the incidents folder exists
        if not os.path.exists(folder):
            os.makedirs(folder)

        # Get the current date and time
        current_datetime = datetime.now()
        date_string = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")

        # Construct the file path
        file_path = os.path.join(folder, f"{date_string}.jpg")

        # Save the pixmap as an image
        pixmap.save(file_path, "JPG")

        return file_path




class CameraWidget(QWidget):
    def __init__(self, parent=None):
        super(CameraWidget, self).__init__(parent)
        self.image_label = QLabel()
        self.person_image_labels = []  # List to store person image labels
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
        self.primelay = QVBoxLayout()  # Create a QVBoxLayout for the primary layout
        self.layout = QHBoxLayout()  # Use QHBoxLayout for image layout
        self.layout.addWidget(self.image_label)

        hello_label = QLabel("Find on the video stream all the direct object recognition and on the right the last three persons recognized.\n In case of a cellphone you can find screenshots of the incident in the tab 'incident' ")
        hello_label.setStyleSheet("color: white; font-size: 24px;")

        hello_label.setAlignment(Qt.AlignCenter)
        self.primelay.addWidget(hello_label)  # Add the "Hello World" label to the primary layout

        # Add the image layout to the primary layout
        self.primelay.addLayout(self.layout)  
        
        self.setLayout(self.primelay)  # Set the primary layout as the widget's layout

        self.cap = cv2.VideoCapture(0)
        self.frame_width = 640
        self.frame_height = 480
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        self.processor = YolosImageProcessor.from_pretrained("hustvl/yolos-tiny")
        self.model = YolosForObjectDetection.from_pretrained('hustvl/yolos-tiny')
        self.timer.start(500)  # Update every 100 milliseconds
        self.previous_results = None  # Store previous results
        self.second_tab = None
        self.receiver = ""
        

    def update_frame(self):
        ret, frame = self.cap.read()
        frame_resized = cv2.resize(frame, (self.frame_width, self.frame_height))
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)  # Convert to RGB color space
        frame_pil = Image.fromarray(frame_rgb)
        inputs = self.processor(images=frame_pil, return_tensors="pt")
        outputs = self.model(**inputs)
        target_sizes = torch.tensor([frame_pil.size[::-1]])
        results = self.processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=0.9)[0]
        
        # Draw boxes and labels on the frame
        frame_with_boxes = draw_boxes(frame_rgb.copy(), results, self.model)
        image = QImage(frame_with_boxes, frame_with_boxes.shape[1], frame_with_boxes.shape[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)
        self.image_label.setPixmap(pixmap)

        # Check for new persons and display their images
        if self.previous_results is not None:
            for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
                if  self.model.config.id2label[label.item()] == "person" and (self.previous_results is None or label not in self.previous_results["labels"].tolist()):
                    person_image = frame_resized[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
                    person_image_rgb = cv2.cvtColor(person_image, cv2.COLOR_BGR2RGB)
                    person_image_pil = Image.fromarray(person_image_rgb)

                    # Resize person image to fit within a 200x200 pixel box
                    person_image_pil.thumbnail((200, 200), Image.LANCZOS)

                    person_image_qimage = QImage(person_image_pil.tobytes(), person_image_pil.size[0], person_image_pil.size[1], QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(person_image_qimage)
                    pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio)

                    save_pixmap(pixmap,"persons")
                    
                    # Update the QLabel with the pixmap image
                    label = QLabel()
                    label.setPixmap(pixmap)
                    label.setFixedSize(200, 200)
                    self.layout.addWidget(label)
                    self.person_image_labels.append(label)  # Append the new label

                    # Remove the first label if the count exceeds 3
                    if len(self.person_image_labels) > 3:
                        label_to_remove = self.person_image_labels.pop(0)
                        self.layout.removeWidget(label_to_remove)
                        label_to_remove.deleteLater()
                    break
                if  self.model.config.id2label[label.item()] == "cell phone" and (self.previous_results is None or label not in self.previous_results["labels"].tolist()):
                    if self.second_tab is not None:
                        # Capture the frame when a knife is detected
                        image_pil = Image.fromarray(frame_with_boxes)
                        image_qimage = QImage(image_pil.tobytes(), image_pil.size[0], image_pil.size[1], QImage.Format_RGB888)
                        pixmap = QPixmap.fromImage(image_qimage)
                        pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio)
                        
                        # Display the captured image on the second tab
                        self.second_tab.labeltxt.setText(self.model.config.id2label[label.item()] + "incident")
                        self.second_tab.label.setPixmap(pixmap)
                        self.second_tab.label.setFixedSize(400, 400)
                        self.second_tab.label.setScaledContents(True)
                        file_path = save_pixmap(pixmap,"incidents")
                        
                        with open("settings/mail.txt", "r") as file:
                            self.receiver = file.readline().strip()
                        #code to signal by mail the incident

                        pdf_path = create_pdf(self.model.config.id2label[label.item()], file_path)

                        send_incident(self.model.config.id2label[label.item()], file_path,pdf_path,  self.receiver)

                        






        self.previous_results = results

    def closeEvent(self, event):
        self.cap.release()


class SecondTab(QWidget):
    def __init__(self, parent=None):
        super(SecondTab, self).__init__(parent)
        layout = QVBoxLayout()
        
        # Add QLabel to display text above the image
        label = QLabel("Incident Tab: You can find here the last image of an incident producted on the camera : \n Cell phone ")
        label.setStyleSheet("color: white; font-size: 14px;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        self.labeltxt = QLabel()
        self.label = QLabel()
        layout.addWidget(self.label)
        layout.addWidget(self.labeltxt)
        self.setLayout(layout)



class ThirdTab(QWidget):
    def __init__(self, parent=None):
        super(ThirdTab, self).__init__(parent)
        layout = QVBoxLayout()
        
        # Add QLabel to display text above the text input field
        label = QLabel("Enter your E-mail address to send the incident alerts")
        label.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(label)
        
        # Add QLineEdit for text input
        self.text_input = QLineEdit()
        layout.addWidget(self.text_input)
        
        # Add QPushButton
        self.button = QPushButton("Confirm")
        self.button.clicked.connect(self.send_email)
        layout.addWidget(self.button)
        
        # Add spacer
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        label2 = QLabel("Enter your name/company for the incident reports")
        label2.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(label2)
        
        # Add QLineEdit for text input
        self.text_input2 = QLineEdit()
        layout.addWidget(self.text_input2)
        
        # Add QPushButton
        self.button2 = QPushButton("Confirm")
        self.button2.clicked.connect(self.send_info)
        layout.addWidget(self.button2)
        
        # Add spacer
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        self.setLayout(layout)
    

    def send_info(self):
        # Retrieve text from QLineEdit
        text = self.text_input2.text()
        with open('settings/info.txt', 'r', encoding='utf-8') as file: 
            lines = file.readlines()
        lines[0] = text + "\n"
        with open('settings/info.txt', 'w', encoding='utf-8') as file: 
            file.writelines(lines) 

    def send_email(self):
        # Retrieve text from QLineEdit
        text = self.text_input.text()
        with open('settings/mail.txt', 'r', encoding='utf-8') as file: 
            lines = file.readlines()
        lines[0] = text + "\n"
        with open('settings/mail.txt', 'w', encoding='utf-8') as file: 
            file.writelines(lines) 
            
        



if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet("QWidget { background-color: #13182e; color: white; }")
    app.setApplicationName("DANGER AI")
    
    tab_widget = QTabWidget()
    camera_widget = CameraWidget()
    second_tab = SecondTab()
    third_tab = ThirdTab()  # Create an instance of ThirdTab
    camera_widget.second_tab = second_tab
    
    tab_widget.addTab(camera_widget, "Live")
    tab_widget.addTab(second_tab, "Incidents")
    tab_widget.addTab(third_tab, "Réglages")

    tab_widget.setWindowTitle("DANGER AI")
    tab_widget.showMaximized()

    sys.exit(app.exec_())
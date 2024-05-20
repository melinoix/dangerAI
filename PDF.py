from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

import os
from datetime import datetime


def create_pdf(incident, image1):
    with open("settings/info.txt", "r") as file:
        name= file.readline().strip()

    # Create a PDF document
    current_datetime = datetime.now()
    date_string = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")

        # Construct the file path
    file_path = os.path.join("reports", f"{date_string}.pdf")

    doc = SimpleDocTemplate(file_path, pagesize=letter)
    story = []

    # Define styles for the text
    styles = getSampleStyleSheet()
    name_style = styles['Heading1']
    description_style = styles['Normal']

    # Add name at the top
    name_text = "<font size=20>%s</font>" % name
    name_paragraph = Paragraph(name_text, name_style)
    story.append(name_paragraph)
    story.append(Spacer(1, 20))

    description1 = "An incident of type " + incident +". Here is a general picture of the incident."
    # Add description 1
    description1_paragraph = Paragraph(description1, description_style)
    story.append(description1_paragraph)
    story.append(Spacer(1, 20))

    # Add first image
    story.append(Image(image1, width=400, height=300))
    story.append(Spacer(1, 20))

    description2 = "This document serves as a confidential notice regarding incident verification procedures. While our software is highly advanced and capable of detecting potential incidents with remarkable accuracy, it's imperative to emphasize that human verification remains essential. Despite our software's efficacy, the final determination of the veracity of any situation necessitates human judgment. Our technology significantly streamlines the process, yet for absolute certainty, human oversight is indispensable. This ensures that decisions are made with utmost accuracy and integrity, safeguarding against any potential errors or misunderstandings. Therefore, in all cases, human verification is indispensable to validate the authenticity of any detected incidents."

    # Add description 2
    description2_paragraph = Paragraph(description2, description_style)
    story.append(description2_paragraph)
    story.append(Spacer(1, 20))

    story.append(PageBreak())
    description3 = "Here are the last 5 persons that appeared on the camera."

    description3_paragraph = Paragraph(description3, description_style)
    story.append(description3_paragraph)
    story.append(Spacer(1, 20))

    # Add second image
    persons_folder = "persons"
    persons_images = [f for f in os.listdir(persons_folder) if os.path.isfile(os.path.join(persons_folder, f))]
    if persons_images:
        for i in range(1,6):
            last_image = sorted(persons_images)[-i]  # Get the last image
            last_image_path = os.path.join(persons_folder, last_image)
            # Add second image
            story.append(Image(last_image_path, width=100, height=75))
            story.append(Spacer(1, 20))

        
    # Build the PDF
    doc.build(story)
    return file_path
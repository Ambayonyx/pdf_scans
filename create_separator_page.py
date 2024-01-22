import io
import uuid
from argparse import ArgumentParser
from uuid import UUID

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib import utils

# import pypng
import pyqrcode

def create_id_text(id: UUID, side:str):
    return f'{id} : {side}'

def points_from_inch(inch: float) -> float:
    return inch * 72
def points_from_cm(cm: float) -> float:
    return points_from_inch(cm / 2.54)

def points_from_mm(mm: float) -> float:
    return points_from_cm(mm / 25.4)

def from_cm(*args):
    return (points_from_cm(a) for a in args)

def print_lines(canvas, left, top, distance, lines):
    for line in lines:
        canvas.drawString(*from_cm(left, top), line)
        top -= distance


def main(number_of_sheets: int):
    c = canvas.Canvas("data/output/content_pdf.pdf", pagesize=A4)

    for page_nr in range(number_of_sheets):
        page_id = uuid.uuid4()
        create_page(c, page_id, "FRONT", "Voor")
        create_page(c, page_id, "BACK", "Achter")

    c.save()


def create_page(c, page_id, side_en, side_local:str):
    # Define the layout
    left_margin = 2.0
    top_line = 26

    # Print Title
    c.setFillColor(colors.grey)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(*from_cm(left_margin, top_line), "Scheidingsvel voor enkelzijdige scan")
    top_line -= 2

    # Print FRONT/BACK
    c.setFillColor(colors.black)
    c.drawString(*from_cm(left_margin + 7, top_line), side_local.upper())
    c.setFont("Helvetica", 14)
    top_line -= 2

    # Print usage
    print_lines(canvas=c,
                left=left_margin,
                top=22,
                distance=1,
                lines=[
                    "Gebruik dit vel om tussen verschillende dubbelzijdige scans",
                    "te plaatsen. ",
                    "",
                    "Gebruik geen kopieën want ieder vel zorgt voor een unieke. ",
                    "identificering waarop het splitsen is gebaseerd.",
                ])

    # Print QR code
    id_text = create_id_text(page_id, side_en)
    positie = from_cm(21 / 2 - 3, 29 / 2 - 4)

    # Create the QR code
    code = pyqrcode.create(id_text)

    # put it as PNG in a memory buffer
    buffer = io.BytesIO()
    code.png(buffer)

    # read the buffer and write to canvas
    image = utils.ImageReader(buffer)
    c.drawImage(image, *positie,
                width=points_from_cm(3),
                height=points_from_cm(3))

    # print QR code in text
    print_lines(canvas=c,
                left=left_margin,
                top=8,
                distance=1,
                lines=[
                    f'QRCODE >{id_text}<'
                ])
    c.showPage()

if __name__ == "__main__":
    parser = ArgumentParser("create_separator_pages")
    parser.add_argument('--number', type=int, default=1)
    args = parser.parse_args()
    main(args.number)

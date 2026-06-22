import uuid
from argparse import ArgumentParser
from uuid import UUID
from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing

import qr_codes


def create_id_text(identifier: UUID, side: str) -> str:
    """Create an identifier text combining UUID and side designation.
    
    Args:
        identifier: The unique page identifier.
        side: The side designation (e.g., 'FRONT', 'BACK').
        
    Returns:
        Formatted string combining identifier and side.
    """
    return f'{identifier} : {side}'

def points_from_inch(inch: float) -> float:
    """Convert inches to points (1 inch = 72 points).
    
    Args:
        inch: Length in inches.
        
    Returns:
        Length converted to points.
    """
    return inch * 72
def points_from_cm(cm: float) -> float:
    """Convert centimeters to points.
    
    Args:
        cm: Length in centimeters.
        
    Returns:
        Length converted to points.
    """
    return points_from_inch(cm / 2.54)

def points_from_mm(mm: float) -> float:
    """Convert millimeters to points.
    
    Args:
        mm: Length in millimeters.
        
    Returns:
        Length converted to points.
    """
    return points_from_cm(mm / 25.4)

def from_cm(cm1: float, cm2: float) -> tuple[float, float]:
    """Convert two centimeter values to points.
    
    Args:
        cm1: First value in centimeters.
        cm2: Second value in centimeters.
        
    Returns:
        Tuple of converted values in points.
    """
    return points_from_cm(cm1), points_from_cm(cm2)

def print_lines(drawing_canvas: canvas.Canvas, left: int, top: int, distance: int, lines: list[str]) -> None:
    """Print multiple lines of text on canvas with specified spacing.
    
    Args:
        drawing_canvas: The Canvas object to draw on.
        left: Left position in centimeters.
        top: Top position in centimeters.
        distance: Vertical distance between lines in centimeters.
        lines: List of text strings to print.
    """
    for line in lines:
        x, y = from_cm(float(left), float(top))
        drawing_canvas.drawString(x, y, line)
        top -= distance


def main(number_of_sheets: int) -> None:
    """Generate separator PDF pages for single-sided scanning.
    
    Creates a PDF file with the specified number of separator sheets,
    each containing a unique QR code for document identification.
    
    Args:
        number_of_sheets: Number of separator pages to generate.
    """
    output_path = Path("data/output/content_pdf.pdf")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    c = canvas.Canvas(str(output_path), pagesize=A4)

    for _ in range(number_of_sheets):
        create_pages(c)

    c.save()

def create_pages(c: canvas.Canvas) -> None:
    """Create a pair of separator pages (front and back of same document).
    
    Args:
        c: The Canvas object to draw on.
    """
    page_identifier = uuid.uuid4()
    create_page(c, qr_codes.Side.FRONT, "Voor", identifier=page_identifier)
    create_page(c, qr_codes.Side.BACK, "Achter", identifier=page_identifier)


def _print_page_title(c: canvas.Canvas, left_margin: float) -> None:
    """Print the page title at the top.
    
    Args:
        c: The Canvas object to draw on.
        left_margin: Left margin in centimeters.
    """
    c.setFillColor(colors.grey)
    c.setFont("Helvetica-Bold", 24)
    x, y = from_cm(left_margin, 26)
    c.drawString(x, y, "Scheidingsvel voor enkelzijdige scan")


def _print_side_label(c: canvas.Canvas, left_margin: float, top_line: float, side_local: str) -> None:
    """Print the FRONT/BACK label.
    
    Args:
        c: The Canvas object to draw on.
        left_margin: Left margin in centimeters.
        top_line: Top position in centimeters.
        side_local: The side text to display (e.g., 'Voor', 'Achter').
    """
    c.setFillColor(colors.black)
    x, y = from_cm(left_margin + 7, top_line)
    c.drawString(x, y, side_local.upper())
    c.setFont("Helvetica", 14)


def _print_usage_instructions(c: canvas.Canvas, left_margin: float) -> None:
    """Print usage instructions text.
    
    Args:
        c: The Canvas object to draw on.
        left_margin: Left margin in centimeters.
    """
    print_lines(drawing_canvas=c,
                left=round(left_margin),
                top=22,
                distance=1,
                lines=[
                    "Gebruik dit vel om tussen verschillende dubbelzijdige scans",
                    "te plaatsen. ",
                    "",
                    "Gebruik geen kopieën want ieder vel zorgt voor een unieke. ",
                    "identificering waarop het splitsen is gebaseerd.",
                ])


def _render_and_draw_qr_code(c: canvas.Canvas, id_text: str, x: float, y: float) -> None:
    """Create, render and draw the QR code.
    
    Args:
        c: The Canvas object to draw on.
        id_text: The text content for the QR code.
        x: X coordinate for placement in points.
        y: Y coordinate for placement in points.
    """
    c.setFont("Helvetica", 7)
    target_size = points_from_cm(3)
    qr_code = qr.QrCodeWidget(id_text, barWidth=target_size)
    drawing = Drawing(target_size, target_size)
    drawing.add(qr_code)
    renderPDF.draw(drawing, c, x, y)


def _print_qr_code_label(c: canvas.Canvas, left_margin: float, id_text: str) -> None:
    """Print the QR code text representation.
    
    Args:
        c: The Canvas object to draw on.
        left_margin: Left margin in centimeters.
        id_text: The QR code content as text.
    """
    print_lines(drawing_canvas=c,
                left=int(left_margin),
                top=8,
                distance=1,
                lines=[f'QRCODE >{id_text}<'])


def create_page(c: canvas.Canvas, side_en: qr_codes.Side, side_local: str, identifier: uuid.UUID) -> None:
    """Create and render a single separator page with QR code.
    
    Generates a complete separator page containing a title, side designation,
    usage instructions, QR code, and text representation of the QR content.
    
    Args:
        c: The Canvas object to draw on.
        side_en: The side enumeration (FRONT or BACK).
        side_local: The localized side text (e.g., 'Voor', 'Achter').
        identifier: The unique page identifier.
    """
    left_margin = 2.0
    top_line = 24
    
    _print_page_title(c, left_margin)
    _print_side_label(c, left_margin, top_line, side_local)
    _print_usage_instructions(c, left_margin)
    
    x, y = from_cm(21 / 2 - 3, 29 / 2 - 4)
    id_text = str(qr_codes.QrCode(side_en, identifier=identifier))
    
    _render_and_draw_qr_code(c, id_text, x, y)
    _print_qr_code_label(c, left_margin, id_text)
    
    c.showPage()
    print(f"Created: {id_text}")

if __name__ == "__main__":
    parser = ArgumentParser("create_separator_pages")
    parser.add_argument('--number', type=int, default=1)
    args = parser.parse_args()
    main(args.number)

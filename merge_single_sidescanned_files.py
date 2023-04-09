import argparse
import logging
from pathlib import Path

from pypdf import PdfReader, PdfWriter

ERROR_FILE_NOT_FOUND = 1


def merge_single_sides_canned_files(front_pdf: str, back_pdf: str, merged_pdf: str,
                                    back_scanned_reverse: bool = False):
    front = PdfReader(front_pdf)
    back = PdfReader(back_pdf)

    if len(front.pages) != len(back.pages):
        logging.warning(f'Nr of pages not equal for front ({len(front.pages)} and back ({len(back.pages)}).')

    with open(front_pdf, "rb") as front_file, open(back_pdf, "rb") as back_file:
        pages_front = [(front_file, index) for index in range(len(front.pages))]
        pages_back = [(back_file, index) for index in range(len(back.pages))]
        if back_scanned_reverse:
            pages_back.reverse()
        pages_merged = list(zip(pages_front, pages_back))
        merger = PdfWriter()
        for page in pages_merged:
            reader = page[0][0]
            page_nr = page[0][1]
            merger.append(reader, pages=(page_nr, page_nr + 1))
            logging.debug(f'front {page_nr}, pages= {len(merger.pages)}')
            reader = page[1][0]
            page_nr = page[1][1]
            merger.append(reader, pages=(page_nr, page_nr + 1))
            logging.debug(f'back {page_nr}, pages= {len(merger.pages)}')

        with open(merged_pdf, "wb") as output_file:
            merger.write(output_file)

        merger.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--front', action='store',
                        required=True,
                        help='The PDF with the scans of the front side of the pages.')
    parser.add_argument('--back', action='store',
                        required=True,
                        help='The PDF with the scans of the back side of the pages.')
    parser.add_argument('--output', action='store',
                        required=True,
                        help='The PDF in which the result shall be stored')
    parser.add_argument('--back_reversed', action='store_true',
                        help='Use this option, when the back side pages have been scanned in the reverse order'
                             'From scanning perspective, this is the easiest.'
                             ' First scan the front side to a file, then rotate the stack and scan the back side to a file.')
    parser.add_argument('--folder', action='store',
                        help='When provided this folder is prepended to the input and output paths.')

    args = parser.parse_args()

    try:
        front = Path(args.front)
        back = Path(args.back)
        output = Path(args.output)
        if args.folder:
            folder = Path(args.folder)
            front = folder / front
            back = folder / back
            output = folder / output
        merge_single_sides_canned_files(front_pdf=front,
                                        back_pdf=back,
                                        merged_pdf=output,
                                        back_scanned_reverse=True)
    except FileNotFoundError as e:
        print(f'Required file does not exist or is not readable: {e.filename}')
        exit(ERROR_FILE_NOT_FOUND)

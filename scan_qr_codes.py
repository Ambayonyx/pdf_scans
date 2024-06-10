import argparse
import io
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import os
from typing import List, Dict, Any, Optional

import fitz  # pip install --upgrade pip; pip install --upgrade pymupdf
from pypdf import PdfReader, PdfWriter
from pyzbar.wrapper import ZBarSymbol
from tqdm import tqdm  # pip install tqdm
from pyzbar.pyzbar import decode
from PIL import Image

from loglevel import LogLevel


# ERRORS
class Errors(Enum):
    OK = 0,
    MISSING_FOLDER = 1

class PageType(Enum):
    SEPARATOR = 0
    DOCUMENT = 1

@dataclass
class Page:
    pass

@dataclass
class DocumentPage:
    sourcePath: Path
    index: int

@dataclass
class SeparatorPage(Page):
    id: str
    is_front: bool

@dataclass
class Document:
    path: Path
    pages: List[Page] = field(default_factory=list)



def print_documents(documents: List[Document]) -> None:
    for doc in documents:
        dp = str(doc.path)
        print(f'{dp}')
        print('-' * len(dp))

        for page_nr, p in enumerate(doc.pages):
            print(f"  {page_nr} {p}")


def collect_input_files(workdir: Path) -> List[Path]:
    logging.debug(f'Collecting PDF files in folder {workdir}.')
    pdf_files: List[Path] = []
    for each_path in os.listdir(workdir):
        if ".pdf" in each_path:
            pdf_files.append(os.path.join(workdir, each_path))
    logging.debug(f'Found {len(pdf_files)} PDF file(s).')
    return pdf_files


def get_seperation_page_id(pixmap: fitz.Pixmap) -> Optional[SeparatorPage]:
    page_info = None
    page_seperator_re = re.compile(r"(?P<uuid>[\dabcdef]{8}-[\dabcdef]{4}-[\dabcdef]{4}-[\dabcdef]{4}-[\dabcdef]{12}) : (?>Side.)?(?P<side>FRONT|BACK)")

    try:
        data = pixmap.tobytes("png", 100)
        stream_str = io.BytesIO(data)
        decodes = decode(Image.open(stream_str), symbols=[ZBarSymbol.QRCODE])

        # Decoded(data=b'018ce42b-6294-7b39-8865-6768ae05c816 : BACK', type='QRCODE',
        #         rect=Rect(left=320, top=1522, width=178, height=180),
        #         polygon=[Point(x=320, y=1701), Point(x=497, y=1702), Point(x=498, y=1523), Point(x=321, y=1522)],
        #         quality=1, orientation='UP')
        # a successful decode was made with a 180x180 and 290x290 images
        for decoded in decodes:
            text = decoded.data.decode()
            logging.debug(f'QR CODE found: (w;h;quality;orientation;txt) = ({decoded.rect.width};{decoded.rect.height};{decoded.quality};{decoded.orientation};{text}')
            matches = page_seperator_re.search(text)
            uuid = matches.group("uuid")
            side = matches.group("side")
            page_info = SeparatorPage(id=uuid, is_front=side == 'FRONT')
    except IndexError:
        pass
    except AttributeError:
        pass
    except Exception as ex:
        print(f"Exception was thrown {ex}")

    return page_info


def parse_pdf_files(pdf_files, debug_dir=None):
    logging.debug('Scanning PDF files.')

    input_documents: List[Document] = []

    for pdf_file in pdf_files:
        logging.debug(f'Parsing {pdf_file}.')

        input_document = Document(path=pdf_file)
        document_structure: List[PageType] = []
        doc = fitz.Document(pdf_file)

        logging.debug(f'Found {len(doc)} page(s).')
        for page_index in range(len(doc)):
            page_info = DocumentPage(sourcePath=pdf_file,
                                     index=page_index)
            page_images = doc.get_page_images(page_index)
            logging.debug(f'Page {page_index} contains {len(page_images)} image(s).')

            for img_index, img in enumerate(page_images):
                xref = img[0]
                # image = doc.extract_image(xref)
                pix = fitz.Pixmap(doc, xref)
                if debug_dir:
                    debug_image_file_name = f'debug_page_{page_index}_image_{img_index}.png'
                    debug_image_full_path = debug_dir / debug_image_file_name
                    logging.debug(f'Writing image to {debug_image_full_path}')
                    pix.save(debug_image_full_path)
                decoded_page = get_seperation_page_id(pix)
                if decoded_page:
                    page_info = decoded_page
                    break;

            document_structure.append(page_info)
        input_document.pages = document_structure
        input_documents.append(input_document)
    return input_documents


def all_separators_found(documents: List[Document]) -> bool:
    check_is_ok = True  # until proven otherwise
    separators: Dict[str, List[bool]] = {}

    for d in documents:
        for page in d.pages:
            if isinstance(page, SeparatorPage):
                id = page.id
                is_front = page.is_front

                if id in separators:
                    if is_front in separators[id]:
                        logging.error(f"Found multiple times: {id} with is_front{is_front}")
                        check_is_ok = False
                    else:
                        separators[id].append(is_front)
                else:
                    separators[id]=[is_front]
    for s_key, s_value in separators.items():
        if len(s_value) != 2:
            logging.error(f"Missing counterpart for {id} with is_front{is_front}")
            check_is_ok = False

    if len(separators) < 2:
        logging.error(f"Expecting at least 2 separator sheets")
        check_is_ok = False
    return check_is_ok


def all_documents_wrapped_in_separators(documents: List[Document]) -> bool:
    check_is_ok = True  # until proven otherwise

    for d in documents:
        if len(d.pages) < 2:
            logging.error(f"Expecting at least pages in a document ({d.path})")
            check_is_ok = False
            continue
        if not isinstance(d.pages[0], SeparatorPage) or not isinstance(d.pages[-1], SeparatorPage):
            logging.error(f"Expecting separator page as first and last page in a document ({d.path})")
            check_is_ok = False
            continue
    return check_is_ok


def merge_documents(documents: List[Document]) -> Dict[str, List[Page]]:
    """merge_documents of PDF documents into set of related pages, ignoring the separator pages.

    Every matching PDF input document pair (front & back) must have, for a 2 original document set:
    - SEP_A_front, doc_a_page_1, .... SEP_B_front, doc_b_page_1, SEP_C_front
    - SEP_C_front, doc_c_page_n, .... SEP_B_back, doc_b_page_n, SEP_A_back

    This means that:
    - all original documents must be wrapped in separators,
    - all front/back separator pairs must be found.

    :param documents: PDF documents with separators and Front and Back sides.
    :return: List of documents with pages where Front and Back are in the right order. The document will have as an
             ID the UUID of the separator page.
    """
    if not all_documents_wrapped_in_separators(documents):
        msg = "Not all documents were wrapped in separators"
        logging.error(msg)
        print(msg)

        return dict()
    logging.info("All documents wrapped in separators")

    if not all_separators_found(documents):
        msg = "Not all separator pages were found!""Not all documents were wrapped in separators"
        logging.error(msg)
        print(msg)
        return dict()
    logging.info("All separator pages found!")

    # make sure to reverse the documents starting with a BACK sheet
    # first split documents on first (separator) page is_front value
    forward_documents : List[Document] = []
    reverse_documents : List[Document] = []
    for doc in documents:
        if doc.pages[0].is_front:
            forward_documents.append(doc)
        else:
            reverse_documents.append(doc)

    # reverse the pages of the reverse documents
    for d in reverse_documents:
        d.pages = list(reversed(d.pages))

    # the first page of the forward and the reverse will contain the same id. one of the front and the other of the back
    forward_documents_map = {doc.pages[0].id: doc for doc in forward_documents}
    reverse_documents_map = {doc.pages[0].id: doc for doc in reverse_documents}

    merged_pages: Dict[str, List[Page]] = {}
    for sep_id in forward_documents_map:
        zipped = zip(forward_documents_map[sep_id].pages, reverse_documents_map[sep_id].pages)
        merged_pages[sep_id] = [page for pair in zipped for page in pair]
    return merged_pages

def split_documents(documents: List[Document]) -> Dict[str, List[Page]]:
    """split_documents of PDF documents into set of related pages, ignoring the separator pages.

    Every PDF input document is single_sided, either front or back. For a 2 original document set:
    - SEP_A_front, doc_a_page_1, .... SEP_B_front, doc_b_page_1, SEP_C_front

    This shows that:
    - all input documents must be wrapped in separators,

    :param documents: PDF documents with separators and Front or Back sides.
    :return: List of documents with pages. The document will have as an ID the UUID of the separator page.
    """
    if not all_documents_wrapped_in_separators(documents):
        msg = "Not all documents were wrapped in separators"
        logging.error(msg)
        print(msg)

        return dict()
    logging.info("All documents wrapped in separators")

    split_pages = {doc.pages[0].id: doc.pages for doc in documents}
    return split_pages

def create_documents_definitions(outputdir: Path, mergedpages: Dict[str, List[Page]]) -> Dict[Path, List[Page]]:
    documents: Dict[Path, List[Page]] = {}
    for id, pages in mergedpages.items():
        file_name = None
        collect_pages: List[Page] = []

        for page in pages:
            if isinstance(page, SeparatorPage):
                if len(collect_pages):
                    documents[file_name] = collect_pages
                    collect_pages = []
                file_name = outputdir / (page.id + ".pdf")
            elif isinstance(page, DocumentPage):
                collect_pages.append(page)

        if len(collect_pages):
            documents[file_name] = collect_pages

    return documents


def store_document(output_path: Path, pages: List[Page]) -> None:
    input_file_paths = list(set([page.sourcePath for page in pages]))

    merger = PdfWriter()
    try:
        readers: Dict[Path, Any] = {p: open(p, "rb") for p in input_file_paths}
        for page in pages:
            merger.append(readers[page.sourcePath], pages=(page.index, page.index + 1))

        with open(output_path, "wb") as output_file:
            merger.write(output_file)
    finally:
        for r in readers.values():
            r.close()

    merger.close()


def main():
    workdir = Path('data')
    default_input_dir = workdir / "input" / "with_qr" / "MultipleDocuments"
    default_output_dir = workdir / "output"
    default_loglevel = LogLevel('INFO')


    parser = argparse.ArgumentParser(prog='scan_qr_coded_documents.py')
    parser.add_argument('--input_dir', '-i', type=str,
                        default=str(default_input_dir),
                        help='Directory where the input documents will be taken from.')
    parser.add_argument('--output_dir', '-o', type=str,
                        default=str(default_output_dir),
                        help='Directory where the output documents will be placed.')
    parser.add_argument('--single_sided', '-s',
                        action='store_true',
                        help='Directory where the output documents will be placed.')
    parser.add_argument('--log_level', '-ll', type=str,
                        default=default_loglevel,
                        help='Directory where the output documents will be placed.')
    args = parser.parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    debug_output_dir = None

    try:
        log_level = LogLevel(args.log_level)
        if log_level == LogLevel.debug:
            debug_output_dir = output_dir
    except ValueError:
        log_level = default_loglevel
        msg = f'Invalid loglevel ({args.log_level}), falling back to default ({default_loglevel}).'
        print(msg)
        logging.warning(msg)

    logging.getLogger().setLevel(log_level)


    if not input_dir.exists():
        msg = f'Input directory does not exist: {input_dir}'
        print(msg)
        logging.error(msg)
        exit(Errors.MISSING_FOLDER)

    logging.debug(f'Input folder: {input_dir}')

    if not Path(output_dir).exists():
        msg = f'Output directory does not exist: {output_dir}'
        print(msg)
        logging.error(msg)
        exit(Errors.MISSING_FOLDER)
    logging.debug(f'Output folder: {output_dir}')


    pdf_files: List[Path] = collect_input_files(input_dir)
    input_documents: List[Document] = parse_pdf_files(pdf_files, debug_output_dir)
    print_documents(input_documents)

    # TODO: combine the paths again
    if args.single_sided:
        split_pages: Dict[str, List[Page]] = split_documents(input_documents)
        original_documents: Dict[Path, List[Page]] = create_documents_definitions(output_dir, split_pages)
        for new_path, pages in original_documents.items():
            store_document(new_path, pages)
    else:
        merged_pages: Dict[str, List[Page]] = merge_documents(input_documents)
        original_documents: Dict[Path, List[Page]] = create_documents_definitions(output_dir, merged_pages)

        for new_path, pages in original_documents.items():
            store_document(new_path, pages)


    print("Done!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, filename='example.log', encoding='utf-8',  filemode='w')
    main()
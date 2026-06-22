# pdf_scans
Scripts to handle pdf_scans.

## Table of Contents

- [pdf\_scans](#pdf_scans)
  - [Table of Contents](#table-of-contents)
  - [Create Separator Pages](#create-separator-pages)
  - [Merge Single Side Scanned Files](#merge-single-side-scanned-files)

## Create Separator Pages

Generate separator PDF pages for single-sided document scanning. Each separator page contains a unique QR code for document identification, making it easy to organize and track multiple scanned documents.

```
  usage: create_separator_page.py [-h] [--number NUMBER]

  options:
    -h, --help         show this help message and exit
    --number NUMBER    Number of separator pages to generate. (default: 1)
```

## Merge Single Side Scanned Files

```
  usage: merge_single_sidescanned_files.py [-h] [--front FRONT] [--back BACK]
                                           [--output OUTPUT] [--back_reversed]

  options:
    -h, --help       show this help message and exit
    --front FRONT    The PDF with the scans of the front side of the pages.
                     (default: None)
    --back BACK      The PDF with the scans of the back side of the pages.
                     (default: None)
    --output OUTPUT  The PDF in which the result shall be stored (default: None)
    --back_reversed  Use this option, when the back side pages have been scanned
                     in the reverse orderFrom scanning perspective, this is the
                     easiest. First scan the front side to a file, then rotate
                     the stack and scan the back side to a file. (default:
                     False)
    --folder FOLDER  When provided this folder is prepended to the input and output 
                     paths. (default: None)

  Process finished with exit code 0
```

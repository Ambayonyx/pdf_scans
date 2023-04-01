# pdf_scans
Scripts to handle pdf_scans.

## Merge single side scanned files

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

  Process finished with exit code 0
```

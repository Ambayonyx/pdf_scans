set shell := ["powershell", "-c"]


split:
    . .venv/Scripts/activate.ps1 ;\
    python scan_qr_codes.py --input_dir "//DS920/Public/scan/01_Maurice/Scanned" --output_dir "//ds920/public/scan/01_Maurice/Separated"
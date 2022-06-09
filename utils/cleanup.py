from pathlib import Path

def cleanup_generated_files():
    audios_path="assets/mp3/"
    images_path="assets/png"
    
    [f.unlink() for f in Path(audios_path).glob("*") if f.is_file()]
    [f.unlink() for f in Path(images_path).glob("*") if f.is_file()]
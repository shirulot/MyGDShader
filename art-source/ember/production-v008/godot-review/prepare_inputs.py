"""Copy the read-only official review inputs into this independent project."""
from hashlib import sha256
import json
from pathlib import Path
import shutil

from PIL import Image

BASE = Path(__file__).resolve().parent
SOURCE = BASE.parent / "official"
DESTINATION = BASE / "inputs"


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main() -> None:
    catalog_file = SOURCE / "catalog.json"
    catalog = json.loads(catalog_file.read_text(encoding="utf-8"))
    assert (catalog["tile_size"], catalog["columns"], catalog["rows"]) == (128,12,4)
    DESTINATION.mkdir(exist_ok=True)
    records = []
    for atlas in catalog["atlases"]:
        source = SOURCE / atlas["texture"]
        assert digest(source) == atlas["sha256"]
        assert Image.open(source).size == (1536,512)
        target = DESTINATION / source.name
        shutil.copyfile(source,target)
        records.append({"id":atlas["id"],"source":source.as_posix(),"destination":target.relative_to(BASE).as_posix(),"sha256":digest(target),"tiles":len(atlas["tiles"]),"new_sample_count":atlas["new_sample_count"],"reused_v007_count":atlas["reused_v007_count"]})
    shutil.copyfile(catalog_file,DESTINATION / "catalog.json")
    report={"status":"INPUTS_COPIED_UNMODIFIED","catalog_sha256":digest(catalog_file),"input_atlases":records,"original_source_modified":False,"no_original_import_sidecars":True}
    (BASE / "input-provenance.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"atlas_count":len(records)}))


if __name__ == "__main__":
    main()

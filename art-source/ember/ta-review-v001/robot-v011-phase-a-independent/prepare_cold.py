"""只复制固定小Godot工程进行最低限度资源加载，包原副本不受import写入。"""
from pathlib import Path
import shutil
OUT=Path(__file__).resolve().parent
COLD=OUT/"cold-project"
shutil.copytree(OUT/"package/godot-review",COLD,dirs_exist_ok=True)
project=COLD/"project.godot"
text=project.read_text(encoding="utf-8-sig")
text=text.replace("[application]",'[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="Ember TA Robot v011 Phase A Independent"',1)
project.write_text(text,encoding="utf-8")

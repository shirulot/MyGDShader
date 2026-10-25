# Learning Completion

给 Godot 内置 **GDScript** 编辑器补充候选提示。使用原生下拉列表，保留原生补全、快捷键和撤销行为。插件读取未保存的编辑器文本；不会修改或保存课程代码。

## 使用

在「项目 → 项目设置 → 插件」启用 **Learning Completion**。正常输入会沿用 Godot 的自动补全时机，也可以按 **Ctrl+Space** 主动请求补全（以编辑器中配置的代码补全快捷键为准）。

| 输入位置 | 补充内容 |
| --- | --- |
| `if event is InputEventMouseButton:` 内的 `event.` | `button_index`、`pressed`、`position` 及继承成员 |
| `var mouse := event as InputEventMouseButton` 后的 `mouse.` | 鼠标事件成员 |
| `MOUSE_BU` / `KEY_SP` | `MOUSE_BUTTON_LEFT` / `KEY_SPACE` 等全局常量 |
| `Node.PROCESS_MODE_` | 节点的处理模式常量 |
| `Vector2.` | `ZERO`、`ONE`、`UP` 等内置类型常量及静态方法 |
| `MouseButton.` / `Node.ProcessMode.` | 对应枚举的成员 |
| 当前作用域的 `const CUSTOM_LIMIT = 8` 后输入 `CUSTOM_` | 自定义常量名 |
| 已知类型的 `event.position.` | `Vector2` 成员 |

裸常量输入至少两个字符才追加候选；成员使用 `.` 触发。插件使用不区分大小写的前缀匹配，最终展示与插入由 Godot CodeEdit 负责。

## 支持范围与限制

- 从单行函数参数类型、显式变量类型、`as`、`NativeClass.new()`、内置类型构造和简单属性链推断类型。
- 支持独立的正向 `if name is Type:` / `elif name is Type:`；不会把该分支的类型推断泄漏到 `else`、分支外或下一个函数。
- 遇到重新赋值重新推断；无法确定类型时交给原生补全。忽略注释、普通字符串和三引号字符串。
- 复杂条件（如 `or`、`not`、复合 `and`）、提前返回后的类型收窄、多行函数签名、自定义脚本类、泛型容器、嵌套脚本类等仍由原生补全处理。这个插件不是完整语义分析器。
- 仅接入 `.gd` 的 CodeEdit。Shader 编辑器、代码诊断、函数参数说明和悬停文档仍使用 Godot 原生功能。
- 不使用网络服务或 AI，不运行用户脚本来推断结果。
- 关闭插件会断开监听；它不修改全局编辑器设置。

## 实现

- `plugin.gd`：通过 `ScriptEditorBase.get_base_editor()` 获取 CodeEdit；在原生 `code_completion_requested` 处理后合并、去重，再提交候选。
- `completion_provider.gd`：屏蔽非代码文本、跟踪缩进作用域、解析简单类型、生成候选。
- 原生类成员从运行中的 `ClassDB` 获取；全局枚举和内置类型来自 `api_index.json`。
- 索引由本机 **Godot 4.7.2 stable steam** 的 `--dump-extension-api` 生成，约 150 KB。升级 Godot 后可以重新生成。

官方接口：[CodeEdit](https://docs.godotengine.org/en/stable/classes/class_codeedit.html)、[ScriptEditorBase](https://docs.godotengine.org/en/stable/classes/class_scripteditorbase.html)、[ClassDB](https://docs.godotengine.org/en/stable/classes/class_classdb.html)。

## 更新索引和测试

在项目根目录运行 PowerShell：

```powershell
./addons/learning_completion/tools/build_index.ps1 -GodotPath 'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe'
./addons/learning_completion/tools/test.ps1 -GodotPath 'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe'
```

测试脚本会复制插件到独立的临时项目，通过实际 Godot CodeEdit 验证候选列表、插入文本、原生候选保留和启停清理；不操作当前课程编辑器。测试日志路径在结束时输出。

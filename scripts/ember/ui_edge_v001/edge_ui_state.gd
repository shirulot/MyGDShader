extends RefCounted
## UI 和采能站共用的状态语义。顺序与 scenes/m0/energy_station.gd 一致。
## 对接时传入真实状态；UI 不自行根据进度猜测危险状态。

enum StationState { SAFE, WARNING, BURST, COOLDOWN }

const TEXT_COLOR := Color("ece9d8")
const MUTED_COLOR := Color("829ba3")
const DIM_COLOR := Color("566b78")
const STRUCTURE_COLOR := Color("2b3e4b")
const BRASS_COLOR := Color("b77c4b")
const UNKNOWN_STATE := -1
const UNKNOWN_DEFINITION := {"label": "未知", "color": DIM_COLOR, "icon": "status_cooldown_32", "marker": "状态未知"}
const DEFINITIONS: Array[Dictionary] = [
	{"label": "安全", "color": Color("51c5c2"), "icon": "status_safe_32", "marker": "采集中"},
	{"label": "预警", "color": Color("e5a44b"), "icon": "status_warning_32", "marker": "预警"},
	{"label": "爆发", "color": Color("e65b4a"), "icon": "status_burst_32", "marker": "危险爆发"},
	{"label": "冷却", "color": Color("566b78"), "icon": "status_cooldown_32", "marker": "冷却中"},
]

static func normalize(value: int) -> int:
	# 非法值不能被夹成 SAFE，否则错误的状态会被显示为可采集。
	return value if value >= StationState.SAFE and value <= StationState.COOLDOWN else UNKNOWN_STATE

static func definition(value: int) -> Dictionary:
	var normalized := normalize(value)
	return DEFINITIONS[normalized] if normalized != UNKNOWN_STATE else UNKNOWN_DEFINITION

static func can_collect(value: int) -> bool:
	return value == StationState.SAFE or value == StationState.WARNING

static func safe_ratio(current: float, maximum: float) -> float:
	# NaN/INF 也不能进入尺寸计算，避免产生异常的裁切矩形。
	if not is_finite(current) or not is_finite(maximum) or maximum <= 0.0:
		return 0.0
	return clampf(current / maximum, 0.0, 1.0)

static func safe_value(value: float) -> float:
	return maxf(0.0, value) if is_finite(value) else 0.0

static func format_quantity(value: float) -> String:
	# 超大有限数不强转64位整数，避免展示负数/溢出；真实goal仍保持原值。
	var finite_value := safe_value(value)
	return format_scientific(finite_value) if finite_value >= 1.0e15 else str(int(finite_value))

static func format_scientific(value: float, decimal_places: int = 3) -> String:
	# Godot 的字符串格式不支持 %e，使用其支持的 %f/%d 手动组成科学记数。
	# 用对数差求尾数，避免 pow(10, exponent) 在极大值/极小值处溢出或下溢。
	var finite_value := safe_value(value)
	if finite_value == 0.0:
		return "0"
	var decimal_log := log(10.0)
	var logarithm := log(finite_value)
	var exponent := int(floorf(logarithm / decimal_log))
	var mantissa := exp(logarithm - float(exponent) * decimal_log)
	var places := clampi(decimal_places, 0, 3)
	var rounding_scale := pow(10.0, float(places))
	mantissa = roundf(mantissa * rounding_scale) / rounding_scale
	# 尾数四舍五入到10时进位，保持1 <= mantissa < 10。
	if mantissa >= 10.0:
		mantissa /= 10.0
		exponent += 1
	var mantissa_format := "%." + str(places) + "f"
	var mantissa_text := mantissa_format % mantissa
	return "%se%s%d" % [mantissa_text, "+" if exponent >= 0 else "", exponent]

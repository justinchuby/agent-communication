# 丁組共板

## 任務
狀：進行中
規：experiments/03-token-efficiency/task-description.md

## 設計決策

### 一：優先序之向
決：一為最尊。數小者先召，數大者後召。默值零。

### 二：誤處之策
決：聽者擲異，不止餘者。收異於列，全畢後擲首異。設error_handler回呼，則以之處異而不擲。

### 三：通配之持
決：不持通配。無「*」監聽，無模式匹配。簡為上。

### 四：異步之持
決：僅同步。不持async。純標準庫，無須asyncio。

### 五：聽者之限
決：各事件限，默十。逾則發MaxListenersExceededWarning。以max_listeners屬性可設之。設零則無限。

### 六：事件數據之式
決：以位置參數與關鍵字參數傳之。emit(event, *args, **kwargs)，聽者以同式受之。不設Event封裝。

### 七：聽者序之則
決：同優先者，先至者先召（先入先出）。以插入序號定之。

### 八：返值之處
決：emit()返所召聽者之數（整數）。聽者之返值棄之不用。

### 介面契約
```python
# 契約既定——非建築師許可不得改

ListenerFn = Callable[..., Any]
ErrorHandler = Callable[[str, Exception, ListenerFn], None]

class EventEmitterError(Exception): ...
class MaxListenersExceededWarning(UserWarning): ...

@dataclass(slots=True)
class Listener:
    fn: ListenerFn
    priority: int = 0       # 一為最尊，數小先召
    once: bool = False
    _seq: int = 0           # 先入先出序號

@dataclass(slots=True)
class Subscription:
    event: str
    listener: Listener
    _emitter: Any
    _cancelled: bool = False
    def cancel(self) -> None: ...

class EventEmitter:
    def __init__(self, max_listeners: int = 10, error_handler: ErrorHandler | None = None): ...
    def on(self, event: str, fn: ListenerFn, priority: int = 0) -> Subscription: ...
    def once(self, event: str, fn: ListenerFn, priority: int = 0) -> Subscription: ...
    def emit(self, event: str, *args: Any, **kwargs: Any) -> int: ...  # 返所召之數
    def off(self, event: str, fn: ListenerFn) -> bool: ...  # 返是否有削
    def remove_all_listeners(self, event: str | None = None) -> None: ...
    def listener_count(self, event: str) -> int: ...
    @property
    def max_listeners(self) -> int: ...
    @max_listeners.setter
    def max_listeners(self, value: int) -> None: ...
```
契約狀：畢

## 分工

| 務號 | 檔 | 主 | 狀 | 註 |
|------|-----|----|----|-----|
| 設計 | — | 建築師 | 畢 | 八歧盡決，介面既定 |
| 型 | types.py | 甲 | 可始 | types.py已有介面，甲可補充或直用 |
| 包初 | __init__.py | 甲 | 可始 | 匯出公開介面 |
| 發射器 | emitter.py | 乙 | 可始 | EventEmitter六法皆依契約實作 |
| 審 | 全部 | 審者 | 阻(實作) | 待甲乙畢 |
| 試 | test_emitter.py | 試者 | 阻(審) | 十五至二十試例 |

## 所得
<!-- 審者與試者以文言文記之 -->

## 度量
遣訊：1
問明：0

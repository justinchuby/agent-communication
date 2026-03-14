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
| 型 | types.py | 甲 | 畢 | 清除未用import，加__lt__排序 |
| 包初 | __init__.py | 甲 | 畢 | 匯出七公開符號 |
| 發射器 | emitter.py | 乙 | 畢 | EventEmitter六法皆依契約實作 |
| 審 | 全部 | 審者 | 畢(通) | 三檔皆合契約，無須改 |
| 試 | test_emitter.py | 試者 | 畢 | 十八試皆通，0.03秒 |

## 所得
### 審者所得

**types.py** — 通。型別名合契約。Listener以slots=True，加__lt__助排序，善。Subscription之cancel()冪等，防重取消。EventEmitterProtocol雖非契約所定，然有益於型檢。

**emitter.py** — 通。六法皆合契約。
- emit()先複列再遍之，防遍歷中改列之患。善。
- 誤處合決策二：有handler則呼之不擲；無則收異畢後擲首異。
- once聽者於全部遍畢後方削，序正確。
- _add_listener以sort維序，逾限則發warning。
- off()以is比fn，合事件發射器之慣例。
- 空事件清理得宜（off與_remove_listener皆pop空列）。

**__init__.py** — 通。七符號皆匯出，以__all__明之。

**微議（不須改）：**
- max_listeners設負值則同零（無限）。可也，然未明驗之。
- _add_listener每次sort，O(n log n)。可用bisect.insort改為O(n)。然常用規模下無礙。

**總判：通。代碼清潔，型標完備，契約盡合。**

## 度量
遣訊：2
問明：0

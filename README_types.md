## What are Types in Python?

Python code can be written using various built-in types that define their behavior and available operations:

- **Numeric Types**
  - `int`: whole numbers (e.g. `5`, `-100`)
  - `float`: decimal numbers (e.g. `3.14`, `-0.5`)
  - `complex`: numbers with real & imaginary parts (e.g. `2 + 3j`)

- **Boolean**
  - `bool`: truth values, `True` or `False`

- **Text**
  - `str`: immutable sequences of characters (e.g. `"hello"`)

- **Binary**
  - `bytes`: immutable byte sequences  
  - `bytearray`: mutable byte sequences  
  - `memoryview`: a view on another binary object

- **Sequences**
  - `list[T]`: mutable, ordered collections (e.g. `list[int]`)  
  - `tuple[T1, T2, …]`: immutable ordered collections (e.g. `tuple[int, str]`)  
  - `range`: immutable sequences of integers, typically used in loops

- **Mappings**
  - `dict[K, V]`: mutable key→value stores (e.g. `dict[str, float]`)

- **Sets**
  - `set[T]`: mutable, unordered unique items  
  - `frozenset[T]`: immutable sets of unique items

- **None**
  - `None`: the singleton “no value” object (its type is `NoneType`).  
    > _Note: `print()` always returns `None`. Functions return `None` unless an explicit `return` is provided._

---

### Example

x: int       = 3
y: float     = 1.0
frozen: bool = True
name: str    = "Rupert"


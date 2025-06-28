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

## What are Type Hints?

Type hints let you declare the expected types of variables, function parameters, and return values.

### When to Use Type Hints
- **Variables**
- **Function parameters**
- **Return values**

> **Note:** Inline type hints are preferred over repeating types in docstrings, which can lead to duplication and maintenance overhead. If you do include types in docstrings, they must match the inline annotations exactly.

---

### Examples

#### Correct
name: str = ""

def greet(name: str) -> str:
    """Return a personalized greeting."""
    return f"Hello, {name}!"

print(greet("Beatrice"))

#### Incorrect
name: str = ""

def greet(name: str) -> str:
    """
    Return a personalized greeting.

    Args:
        name (int):  ❌ wrong type here!

    Returns:
        bool:       ❌ wrong type here!
    """
    return f"Hello, {name}!"

print(greet("Beatrice"))

## Why Type Hint?

Correct type handling is necessary for the proper functioning of code.

Proper type hinting enables developers to:

- **Understand** the intended data structures and interfaces  
- **Maintain** and navigate the codebase more easily  
- **Refactor** with confidence, catching mismatches early  
- **Extend** the code and documentation without introducing errors  

Additionally, type hints unlock the use of static analysis tools (like MyPy), allowing you to catch type-related bugs before runtime and ship more robust code.

## Typing Using the `typing` Module

Most common types (e.g., `str`, `int`, `float`, `bool`, `bytes`, `list`, `dict`, `tuple`, `set`, `None`) are built-in in Python 3.10+. For more advanced or generic types, import from the `typing` module:

from typing import (
    Any,            # “escape hatch” for unknown types
    Union,         # still available, though often replaced by |
    Optional,      # same as Union[..., None]
    Callable,      # for callables with specific signatures
    TypeVar, Generic,  # for custom generics
    ClassVar,      # annotate class-level constants
    Literal, Final,  # exact values & constants
    TypedDict,     # dicts with fixed key types
    Protocol,      # structural/subtype interfaces
    NewType,       # distinct alias for an existing type
    TypeAlias,     # name a complex type
    Annotated,     # add metadata to existing types
    ParamSpec, Concatenate,  # for decorator/dependent signatures
    overload, cast, NoReturn,  # various mypy helpers
)

### Example
from typing import TypedDict, Literal

class User(TypedDict):
    id:     int
    name:   str
    active: bool

Status = Literal["pending", "active", "disabled"]

def find_user(uid: int) -> User | None:
    """
    Lookup a user by ID.
    Returns a `User` dict if found, or `None` otherwise.
    """
    if uid == 1:
        return {"id": 1, "name": "Alice", "active": True}
    return None

## Custom Types

You can use custom types whenever you’ve defined your own classes.

### Example
from dataclasses import dataclass
from hiero_sdk import CryptoGetAccountBalanceQuery

@dataclass
class AccountId:
    shard:  int
    realm:  int
    serial: int

def query_hbar_balance(account: AccountId) -> None:
    """
    Fetch and print the Hbar balance for the given AccountId.
    """
    balance = CryptoGetAccountBalanceQuery(account)
    print(f"Your Hbar balance is: {balance.hbars}")

if __name__ == "__main__":
    account = AccountId(0, 0, 200)
    query_hbar_balance(account)

def_query_hbar_balance function takes account as an argument, which is of custom type AccountId, then the function returns type None. It returns None because there is no return statement in the function, and it instead prints.

### Example 2
from dataclasses import dataclass
from hiero_sdk import AccountId
from hiero_sdk import CryptoGetAccountBalanceQuery

def build_balance_query(account: AccountId) -> CryptoGetAccountBalanceQuery:
    """
    Construct and return a CryptoGetAccountBalanceQuery for the given account.

    Args:
        account (AccountId): The Hedera account identifier.

    Returns:
        CryptoGetAccountBalanceQuery: A query object you can execute to fetch the balance.
    """
    return CryptoGetAccountBalanceQuery(account)

if __name__ == "__main__":
    account = AccountId(0, 0, 200)
    query = build_balance_query(acct)
    print(query)

## Installing and Using MyPy

Use MyPy to help check for correct typing in your code and its imports. You can adopt type hints gradually without impacting runtime. MyPy will not:

- Prevent or change the running of your code  

This makes MyPy safe to introduce at your own pace.

### Install MyPy

bash:
pip install mypy

Command to check type hinting with MyPy for program.py:
mypy path/to/program.py
E.g.
mypy src/hiero_sdk_python/tokens/token_info.py

Read about MyPy:
Mypy [general](https://mypy.readthedocs.io/en/stable/).

Mypy cheatsheet [cheatsheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html#cheat-sheet-py3).

## Configuring MyPy

By default, MyPy is a very strict type checker. This project includes a `mypy.ini` at `/mypy.ini` to enable gradual, module-by-module checking. You can customize it to suit your needs:

```ini
# Do not error on imports that lack type stubs
ignore_missing_imports = True

# Allow parameters to default to None without forcing X | None annotations
implicit_optional = True

# Suppress errors when calling functions without type annotations
allow_untyped_calls = True

For a full list of flags and options, see the MyPy command-line reference:  
[MyPy command-line reference](https://mypy.readthedocs.io/en/stable/command_line.html#command-line)

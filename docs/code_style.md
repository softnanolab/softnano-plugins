# SoftNano Python Code Style Guide

## Docstrings

Use Google-style docstrings with `Args:`, `Returns:`, and a multi-line description.

```python
def compute_energy(positions: list[np.ndarray], charges: list[float]) -> float:
    """Compute the electrostatic energy of a set of charged particles.

    Uses Coulomb's law to calculate pairwise interactions between
    all particles. Assumes vacuum permittivity.

    Args:
        positions: Cartesian coordinates of each particle.
            Expected Shape: (N, 3)
        charges: Charge of each particle in elementary charge units.
            Expected Shape: (N,)

    Returns:
        Total electrostatic energy in eV.
    """
```

### Rules

- First line is a concise summary (imperative mood).
- Leave a blank line between the summary and the extended description.
- `Args:` lists every parameter with a description indented on the next line.
- `Returns:` specifies the return datatype and meaning.

## Tensor / Array Shapes

Document expected shapes in `Args:` using `Expected Shape:` on a sub-line:

```python
Args:
    features: Input feature matrix.
        Expected Shape: (batch_size, seq_len, d_model)
    mask: Attention mask. True means the position is allowed.
        Expected Shape: (batch_size, seq_len)
```

## Return Type Documentation

- Always specify the return datatype in `Returns:`.
- If a function can return `None`, document both cases:

```python
Returns:
    The parsed config dict, or None if the file does not exist.
```

## Type Annotations (Python 3.12+)

### Use pipe notation for unions

```python
# Good
def get_name(user_id: int) -> str | None:
    ...

# Bad
def get_name(user_id: int) -> Optional[str]:
    ...
```

### Use lowercase builtins

```python
# Good
def process(items: list[int], mapping: dict[str, float]) -> tuple[int, ...]:
    ...

# Bad
from typing import List, Dict, Tuple
def process(items: List[int], mapping: Dict[str, float]) -> Tuple[int, ...]:
    ...
```

### Annotate all function arguments

Every function parameter must have a type annotation. Return types are also required.

```python
# Good
def train(model: nn.Module, epochs: int, lr: float = 1e-3) -> float:
    ...

# Bad
def train(model, epochs, lr=1e-3):
    ...
```

## Commented-Out Code

Commented-out code must not be left without context. If code is intentionally kept for future review, mark it with a `# TODO: review this code later` comment and wrap the block in `# ----` markers:

```python
# TODO: review this code later
# ----
# old_result = legacy_compute(data)
# if old_result.is_valid():
#     return old_result
# ----
```

If commented-out code does not have these markers, it should be deleted.

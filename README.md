# ppretty v.1.0

## About
Convert any python object to a human readable format.

## Installation
```sh
$ pip install ppretty
```

## Examples
Here's a basic example:
```python
from ppretty import ppretty


class MyClass(object):
    def __init__(self):
        self.a = range(10)

    b = 'static var'

    @property
    def _c(self):
        return 'protected property'

my_obj = MyClass()

print ppretty(my_obj)
print
print ppretty(my_obj, indent='    ', width=40, seq_length=10,
              show_protected=True, show_static=True, show_properties=True, show_address=True)
```
Output:
```
__main__.MyClass(a = [0, 1, ..., 8, 9])

__main__.MyClass at 0x1f6bda0L (
    _c = 'protected property',
    a = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    b = 'static var'
)
```

## License
BSD

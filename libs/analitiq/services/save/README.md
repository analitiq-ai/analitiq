Usage example

```python
from analitiq.services.save.save import Save


save_ = Save()
resp = save_.run("Save this for me please",{})
print(resp.content)
```
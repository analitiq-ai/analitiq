Usage example

```python
from analitiq.agents.save.save import Save


save_ = Save()
resp = save_.run("Save this for me please",{})
print(resp.content)
```
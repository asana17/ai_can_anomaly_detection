# can_log_loader

Reads a CAN log CSV so the rest of the pipeline works on typed frames, not raw
text.

```python
load_can_log(path)   # -> iterator of CanFrame(timestamp, can_id, data)
```

from pathlib import Path

test_file = Path("tests/test_async_step_loader.py")
print(f"Test file: {test_file}")
test_resolved = test_file.resolve()
print(f"Test file resolved: {test_resolved}")
step_path = test_resolved.parents[2] / "biurko standard.step"
print(f"Expected STEP path: {step_path}")
print(f"Exists: {step_path.exists()}")
if step_path.exists():
    data = step_path.read_bytes()
    print(f"Size: {len(data)}")
    print(f"Header correct: {data.startswith(b'ISO-10303-21')}")

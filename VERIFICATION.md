# Verification

Verified with compute job `e3a1d58c-93c`.

- Command: `bash /home/user/scripts/run.sh`
- Container execution: succeeded
- Exit code: 0
- Duration: 22.8 seconds
- Output artifact: `scoring/scores.json`

Final reproduced scaled scores:

- `sharpasp_sr`: 4 solved instances, exact count accuracy 1.0, largest solved count `2^14`.
- `enumeration_cap_1000`: 2 solved instances, exact count accuracy 0.5, largest completed count `2^8`.

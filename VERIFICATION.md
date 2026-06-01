# Verification

Verified with compute job `42bdeff0-173`.

- Command: `bash /home/user/scripts/run.sh`
- Container execution: succeeded
- Exit code: 0
- Duration: 60.1 seconds
- Output artifact: `scoring/scores.json`

Final reproduced scaled scores:

- `sharpasp_sr`: 6 solved instances, exact count accuracy 1.0, largest solved count `2^20`.
- `enumeration_cap_1000`: 2 solved instances, exact count accuracy 0.3333333333333333, largest completed count `2^8`.
- `enumeration_then_sharpasp_sr`: 6 solved instances, exact count accuracy 1.0, two instances completed by enumeration and four by sharpASP-sR fallback.

# Codex Heartbeat v4.1A — FIXED

This version corrects the Windows Task Scheduler error by using:

- cmd.exe /c wrapper  
- fully escaped quotes  
- absolute paths  
- safe update-or-create logic  

The heartbeat now reliably schedules itself on Windows.

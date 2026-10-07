# Keep the system and display awake while the end-to-end chain (given PID) is running.
param([int]$ChainPid)
Add-Type -Namespace Win32 -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);'
# ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
$flags = [uint32]2147483651
while (Get-Process -Id $ChainPid -ErrorAction SilentlyContinue) {
    [Win32.Power]::SetThreadExecutionState($flags) | Out-Null
    Start-Sleep -Seconds 30
}
[Win32.Power]::SetThreadExecutionState([uint32]2147483648) | Out-Null

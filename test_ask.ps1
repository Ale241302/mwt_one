$headers = @{
    "accept" = "application/json"
    "Authorization" = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYWRtaW4iLCJwZXJtaXNzaW9ucyI6WyJBU0tfS05PV0xFREdFX09QUyIsIkFTS19LTk9XTEVER0VfUFJPRFVDVFMiLCJBU0tfS05PV0xFREdFX1BSSUNJTkciLCJJTkRFWF9LTk9XTEVER0UiXX0.H5d54w_U__Hi_UQZimbom_b8Gim8hH-ivEpfUwPUryQ"
    "Content-Type" = "application/json"
}

$body = @{
    question = "que prodcutos tiene rana"
    session_id = "string"
    expediente_ref = 0
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri 'http://127.0.0.1:8001/api/knowledge/ask/' -Method Post -Headers $headers -Body $body
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Error $_.Exception.Message
}

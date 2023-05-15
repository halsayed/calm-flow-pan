$code = "@@{PROJECT_CODE}@@"
$ou_base = "@@{PROJECT_OU_BASE}@@"
$project_name = "@@{PROJECT_NAME}@@"


write-Host "Create new project group"
Write-Host "`n===================================================="
New-ADGroup `
   -Name "$code-users" `
   -SamAccountName "$code-users" `
   -GroupCategory Security `
   -GroupScope Global `
   -Path "$ou_base" `
   -Description "$project_name users" `
   -PassThru


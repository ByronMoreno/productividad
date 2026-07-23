# upload-secrets.ps1
# Script para subir secretos a GitHub usando la CLI gh

Write-Host "Iniciando subida de secretos a GitHub..."

# Solicitar interactivamente los datos sensibles para no exponerlos en el código de Git
$GH_PAT = Read-Host -Prompt "Ingresa tu GitHub Personal Access Token (GH_PAT)"
$SSH_PASSWORD = Read-Host -Prompt "Ingresa la contraseña de tu VPS (SSH_PASSWORD)"
$IP_VPS = "161.97.140.245"

if (-not $GH_PAT -or -not $SSH_PASSWORD) {
    Write-Error "El token GH_PAT y la contraseña SSH_PASSWORD son obligatorios para continuar."
    exit 1
}

# 1. Subir secretos del VPS y Token de GitHub
Write-Host "Subiendo GH_PAT..."
gh secret set GH_PAT --body $GH_PAT

Write-Host "Subiendo SSH_PASSWORD..."
gh secret set SSH_PASSWORD --body $SSH_PASSWORD

Write-Host "Subiendo IP_VPS..."
gh secret set IP_VPS --body $IP_VPS

# 2. Subir variables de entorno de producción
Write-Host "Subiendo variables de entorno del VPS..."
gh secret set FLASK_ENV --body "development"
gh secret set SECRET_KEY --body "clave_secreta_desarrollo_12345"
gh secret set POSTGRES_USER --body "bmoreno"
gh secret set POSTGRES_PASSWORD --body "seMoreno%"
gh secret set POSTGRES_DB --body "productividad"
gh secret set POSTGRES_HOST --body "dbproductividad"
gh secret set POSTGRES_PORT --body "5432"

# 3. Leer archivo .env y subir sus variables de forma dinámica (por ejemplo, OpenAI keys)
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -and -not $_.StartsWith("#")) {
            if ($_ -match "^(.*?)=(.*)$") {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                
                # Quitar comillas si el valor las tiene envueltas
                if ($value.StartsWith('"') -and $value.EndsWith('"')) {
                    $value = $value.Substring(1, $value.Length - 2)
                }
                if ($value.StartsWith("'") -and $value.EndsWith("'")) {
                    $value = $value.Substring(1, $value.Length - 2)
                }

                # Evitar resubir las que ya subimos explícitamente
                $exclude_keys = @("FLASK_ENV", "SECRET_KEY", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "POSTGRES_HOST", "POSTGRES_PORT", "GH_PAT", "SSH_PASSWORD", "IP_VPS")
                if ($exclude_keys -notcontains $key) {
                    Write-Host "Subiendo $key..."
                    gh secret set $key --body $value
                }
            }
        }
    }
}

Write-Host "¡Proceso de carga de secretos finalizado con éxito!"

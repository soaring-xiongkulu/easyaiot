# Fix ConfigParser.cpp bracket issues
$content = Get-Content src\ConfigParser.cpp
$fixedContent = @()

for ($i = 0; $i < $content.Length; $i++) {
    if ($i -eq 146) {
        $fixedContent += '                    config.alarmConfidenceThreshold = 0.5f;  // 默认值'
    } elseif ($i -eq 147) {
        $fixedContent += '                }'
    } elseif ($i -eq 150) {
        $fixedContent += '                    config.alarmCooldownTime = 30;  // 默认30秒'
    } elseif ($i -eq 151) {
        $fixedContent += '                }'
    } else {
        $fixedContent += $content[$i]
    }
}

$fixedContent | Set-Content src\ConfigParser.cpp -Encoding UTF8
Write-Host "File fixed successfully!"

$content = Get-Content src\ConfigParser.cpp
$fixedContent = @()

for ($i = 0; $i < $content.Length; $i++) {
    if ($i -eq 146) {
        $fixedContent += '                    config.alarmConfidenceThreshold = 0.5f;  // 默认值'
    } elseif ($i -eq 147) {
        $fixedContent += '                }'
    } elseif ($i -eq 150) {
        $fixedContent += '                    config.alarmCooldownTime = 30;  // 默认30秒'
    } elseif ($i -eq 151) {
        $fixedContent += '                }'
    } else {
        $fixedContent += $content[$i]
    }
}

$fixedContent | Set-Content src\ConfigParser.cpp -Encoding UTF8
Write-Host "File fixed successfully!"

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
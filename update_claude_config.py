#!/usr/bin/env python3
"""
Script per aggiornare la configurazione MCP di Claude Code
con il nuovo server Google Ads.
"""
import json
import os

# Path al file di configurazione
config_path = os.path.expanduser('~/.claude.json')

# Leggi la configurazione esistente
with open(config_path, 'r') as f:
    config = json.load(f)

# Aggiorna la configurazione del server google-ads
config['mcpServers']['google-ads'] = {
    'type': 'stdio',
    'command': '/Users/micheledeangelis/mcp-google-ads/.venv/bin/python',
    'args': ['/Users/micheledeangelis/mcp-google-ads/google_ads_mcp.py'],
    'env': {
        # Lascia vuote le credenziali - l'utente deve configurarle
        # Oppure usa variabili d'ambiente di sistema
        # 'GOOGLE_ADS_DEVELOPER_TOKEN': '',
        # 'GOOGLE_ADS_CLIENT_ID': '',
        # 'GOOGLE_ADS_CLIENT_SECRET': '',
        # 'GOOGLE_ADS_REFRESH_TOKEN': '',
        # 'GOOGLE_ADS_LOGIN_CUSTOMER_ID': ''  # Optional, for MCC accounts
    }
}

# Salva la configurazione aggiornata
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print('✅ Configurazione Google Ads MCP aggiornata con successo!')
print('')
print('📋 Server configurato:')
print('   - Nome: google-ads')
print('   - Command: /Users/micheledeangelis/mcp-google-ads/.venv/bin/python')
print('   - Script: /Users/micheledeangelis/mcp-google-ads/google_ads_mcp.py')
print('')
print('⚙️  PROSSIMO STEP - Configura le credenziali:')
print('')
print('1️⃣  Crea un file .env nella cartella mcp-google-ads:')
print('   cd /Users/micheledeangelis/mcp-google-ads')
print('   cp .env.example .env')
print('')
print('2️⃣  Modifica .env e aggiungi le tue credenziali Google Ads API:')
print('   - GOOGLE_ADS_DEVELOPER_TOKEN')
print('   - GOOGLE_ADS_CLIENT_ID')
print('   - GOOGLE_ADS_CLIENT_SECRET')
print('   - GOOGLE_ADS_REFRESH_TOKEN')
print('   - GOOGLE_ADS_LOGIN_CUSTOMER_ID (opzionale, per account MCC)')
print('')
print('3️⃣  OPPURE aggiungi le credenziali direttamente nel file .claude.json')
print('    nella sezione mcpServers -> google-ads -> env')
print('')
print('📚 Guida completa: /Users/micheledeangelis/mcp-google-ads/README.md')
print('')
print('🔄 Riavvia Claude Code per applicare le modifiche!')

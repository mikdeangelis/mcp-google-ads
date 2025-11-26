#!/usr/bin/env python3
"""
Rimuove google-ads dal progetto home per usare la config globale.
"""
import json

config_path = '/Users/micheledeangelis/.claude.json'

# Leggi config
with open(config_path, 'r') as f:
    config = json.load(f)

# Rimuovi google-ads dal progetto home (se esiste)
home_project = config['projects']['/Users/micheledeangelis']
if 'google-ads' in home_project.get('mcpServers', {}):
    print('🔧 Rimozione google-ads dal progetto home...')
    del home_project['mcpServers']['google-ads']
    print('✅ Rimosso!')
else:
    print('⚠️  google-ads non trovato nel progetto home')

# Verifica che sia configurato a livello globale
if 'google-ads' in config['mcpServers']:
    print('\n✅ google-ads configurato a livello GLOBALE:')
    print(f"   Command: {config['mcpServers']['google-ads']['command']}")
    print(f"   Script: {config['mcpServers']['google-ads']['args'][0]}")
else:
    print('\n❌ ERRORE: google-ads non trovato a livello globale!')

# Salva
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print('\n✅ Configurazione aggiornata!')
print('🔄 Riavvia Claude Code per applicare le modifiche.')

#!/usr/bin/env python3
"""
Google Ads OAuth2 Refresh Token Generator

Genera il refresh token necessario per configurare il Google Ads MCP.
Eseguire una sola volta durante il setup iniziale.

Prerequisiti:
- Client ID e Client Secret da Google Cloud Console
- Account Google con accesso a Google Ads

Uso:
    python generate_token.py
"""

from google_auth_oauthlib.flow import InstalledAppFlow

def main():
    print("\n" + "="*60)
    print("  Google Ads - Refresh Token Generator")
    print("="*60 + "\n")

    # Richiedi credenziali
    client_id = input("Inserisci il CLIENT_ID: ").strip()
    client_secret = input("Inserisci il CLIENT_SECRET: ").strip()

    if not client_id or not client_secret:
        print("\n❌ Errore: Client ID e Client Secret sono obbligatori")
        return

    print("\n⏳ Apertura browser per autorizzazione...")
    print("   (Autorizza l'accesso con l'account Google Ads)\n")

    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=["https://www.googleapis.com/auth/adwords"]
    )

    try:
        credentials = flow.run_local_server(port=8080)

        print("\n" + "="*60)
        print("  ✅ AUTORIZZAZIONE COMPLETATA")
        print("="*60)
        print(f"\nREFRESH_TOKEN:\n{credentials.refresh_token}")
        print("\n" + "-"*60)
        print("Copia il token qui sopra e aggiungilo al file .env:")
        print("GOOGLE_ADS_REFRESH_TOKEN=<il_tuo_token>")
        print("-"*60 + "\n")

    except Exception as e:
        print(f"\n❌ Errore durante l'autorizzazione: {e}")

if __name__ == "__main__":
    main()

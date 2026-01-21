"""
OAuth2 flow manager pour Gmail et autres providers
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)


class GmailOAuth2Manager:
    """
    Gestionnaire OAuth2 pour Gmail.

    Gère le flow d'authentification initial et le refresh des tokens.
    """

    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify'
    ]

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str = 'http://localhost:8080'):
        """
        Initialiser le manager OAuth2.

        Args:
            client_id: Google OAuth2 client ID
            client_secret: Google OAuth2 client secret
            redirect_uri: URI de redirection (default: localhost)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorization_url(self) -> str:
        """
        Générer l'URL d'autorisation pour l'utilisateur.

        Returns:
            URL pour l'authentification Google
        """
        client_config = {
            "installed": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uris": [self.redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }

        flow = InstalledAppFlow.from_client_config(
            client_config,
            scopes=self.SCOPES
        )

        # Get authorization URL
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent pour refresh token
        )

        return auth_url

    def exchange_code_for_token(self, authorization_code: str) -> Dict[str, Any]:
        """
        Échanger le code d'autorisation contre un access token.

        Args:
            authorization_code: Code reçu après authentification

        Returns:
            Dict avec les credentials:
            {
                "token": str,
                "refresh_token": str,
                "token_uri": str,
                "client_id": str,
                "client_secret": str,
                "scopes": List[str],
                "expiry": str (ISO format)
            }
        """
        client_config = {
            "installed": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uris": [self.redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }

        flow = InstalledAppFlow.from_client_config(
            client_config,
            scopes=self.SCOPES
        )

        # Exchange code
        flow.fetch_token(code=authorization_code)

        creds = flow.credentials

        return self._credentials_to_dict(creds)

    def interactive_auth_flow(self) -> Dict[str, Any]:
        """
        Flow d'authentification interactif (local server).

        Lance un serveur local pour recevoir le callback OAuth2.

        Returns:
            Dict avec les credentials
        """
        client_config = {
            "installed": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uris": [self.redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }

        flow = InstalledAppFlow.from_client_config(
            client_config,
            scopes=self.SCOPES
        )

        # Run local server
        creds = flow.run_local_server(
            port=8080,
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        return self._credentials_to_dict(creds)

    @staticmethod
    def _credentials_to_dict(creds: Credentials) -> Dict[str, Any]:
        """
        Convertir Credentials en dict pour stockage.

        Args:
            creds: Google Credentials object

        Returns:
            Dict sérialisable
        """
        return {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes,
            'expiry': creds.expiry.isoformat() if creds.expiry else None
        }

    @staticmethod
    def refresh_access_token(credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refresh un access token expiré.

        Args:
            credentials: Dict avec les credentials actuels

        Returns:
            Dict avec les nouveaux credentials

        Raises:
            Exception si le refresh échoue
        """
        creds_data = {
            'token': credentials.get('token'),
            'refresh_token': credentials.get('refresh_token'),
            'token_uri': credentials.get('token_uri', 'https://oauth2.googleapis.com/token'),
            'client_id': credentials.get('client_id'),
            'client_secret': credentials.get('client_secret'),
            'scopes': credentials.get('scopes', GmailOAuth2Manager.SCOPES)
        }

        if 'expiry' in credentials and credentials['expiry']:
            if isinstance(credentials['expiry'], str):
                creds_data['expiry'] = datetime.fromisoformat(credentials['expiry'])
            else:
                creds_data['expiry'] = credentials['expiry']

        creds = Credentials(**creds_data)

        if creds.expired and creds.refresh_token:
            logger.info("Refreshing expired token...")
            creds.refresh(Request())
            logger.info("Token refreshed successfully")

            return GmailOAuth2Manager._credentials_to_dict(creds)
        else:
            logger.info("Token still valid")
            return credentials


class MicrosoftOAuth2Manager:
    """
    Gestionnaire OAuth2 pour Microsoft/Outlook avec MSAL.

    Supporte les applications Public Client (desktop/mobile) et Confidential Client (web/backend).
    """

    SCOPES = [
        'https://graph.microsoft.com/Mail.Read',
        'https://graph.microsoft.com/Mail.ReadWrite'
    ]

    def __init__(
        self,
        client_id: str,
        client_secret: Optional[str] = None,
        tenant_id: str = 'common',
        redirect_uri: str = 'http://localhost:8080'
    ):
        """
        Initialiser le manager OAuth2 Microsoft.

        Args:
            client_id: Azure AD application client ID
            client_secret: Client secret (optional, for confidential apps)
            tenant_id: Tenant ID (default: 'common' for multi-tenant)
            redirect_uri: URI de redirection OAuth2
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.redirect_uri = redirect_uri
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"

    def get_authorization_url(self) -> str:
        """
        Générer l'URL d'autorisation Microsoft.

        Returns:
            URL pour l'authentification Azure AD
        """
        from msal import PublicClientApplication

        app = PublicClientApplication(
            self.client_id,
            authority=self.authority
        )

        # Get authorization URL
        flow = app.initiate_auth_code_flow(
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri
        )

        if 'auth_uri' not in flow:
            raise ValueError("Failed to create authorization URL")

        return flow['auth_uri']

    def exchange_code_for_token(
        self,
        authorization_code: str,
        flow_state: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Échanger le code d'autorisation contre un access token.

        Args:
            authorization_code: Code reçu après authentification
            flow_state: State du flow d'authentification (optional)

        Returns:
            Dict avec les credentials:
            {
                "token": str,
                "refresh_token": str,
                "client_id": str,
                "client_secret": str (optional),
                "tenant_id": str,
                "scopes": List[str],
                "expiry": str (ISO format)
            }
        """
        from msal import PublicClientApplication, ConfidentialClientApplication

        if self.client_secret:
            # Confidential client application
            app = ConfidentialClientApplication(
                self.client_id,
                authority=self.authority,
                client_credential=self.client_secret
            )
        else:
            # Public client application
            app = PublicClientApplication(
                self.client_id,
                authority=self.authority
            )

        # Acquire token by authorization code
        result = app.acquire_token_by_authorization_code(
            authorization_code,
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri
        )

        if 'access_token' not in result:
            error = result.get('error_description', 'Unknown error')
            raise ValueError(f"Failed to acquire token: {error}")

        return self._result_to_dict(result)

    def interactive_auth_flow(self) -> Dict[str, Any]:
        """
        Flow d'authentification interactif (device code flow).

        Lance un flow device code pour les applications sans navigateur.

        Returns:
            Dict avec les credentials
        """
        from msal import PublicClientApplication

        app = PublicClientApplication(
            self.client_id,
            authority=self.authority
        )

        # Initiate device flow
        flow = app.initiate_device_flow(scopes=self.SCOPES)

        if 'user_code' not in flow:
            raise ValueError("Failed to create device flow")

        # Display instructions to user
        print("\n" + "=" * 60)
        print("Microsoft OAuth2 - Device Code Flow")
        print("=" * 60)
        print(flow['message'])
        print("=" * 60)

        # Wait for user to complete authentication
        result = app.acquire_token_by_device_flow(flow)

        if 'access_token' not in result:
            error = result.get('error_description', 'Unknown error')
            raise ValueError(f"Authentication failed: {error}")

        print("\n✅ Authentification réussie!")

        return self._result_to_dict(result)

    def _result_to_dict(self, result: Dict) -> Dict[str, Any]:
        """
        Convertir le résultat MSAL en dict pour stockage.

        Args:
            result: Résultat de MSAL

        Returns:
            Dict sérialisable
        """
        # Calculate expiry
        expires_in = result.get('expires_in', 3600)
        expiry = datetime.utcnow() + timedelta(seconds=expires_in)

        credentials = {
            'token': result['access_token'],
            'refresh_token': result.get('refresh_token'),
            'client_id': self.client_id,
            'tenant_id': self.tenant_id,
            'scopes': result.get('scope', self.SCOPES),
            'expiry': expiry.isoformat()
        }

        # Add client_secret only if present (for confidential apps)
        if self.client_secret:
            credentials['client_secret'] = self.client_secret

        return credentials

    @staticmethod
    def refresh_access_token(credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refresh un access token expiré.

        Args:
            credentials: Dict avec les credentials actuels

        Returns:
            Dict avec les nouveaux credentials

        Raises:
            Exception si le refresh échoue
        """
        from msal import PublicClientApplication, ConfidentialClientApplication

        client_id = credentials.get('client_id')
        client_secret = credentials.get('client_secret')
        tenant_id = credentials.get('tenant_id', 'common')
        refresh_token = credentials.get('refresh_token')
        scopes = credentials.get('scopes', MicrosoftOAuth2Manager.SCOPES)

        if not refresh_token:
            raise ValueError("No refresh token available")

        authority = f"https://login.microsoftonline.com/{tenant_id}"

        if client_secret:
            app = ConfidentialClientApplication(
                client_id,
                authority=authority,
                client_credential=client_secret
            )
        else:
            app = PublicClientApplication(
                client_id,
                authority=authority
            )

        # Acquire token by refresh token
        result = app.acquire_token_by_refresh_token(
            refresh_token,
            scopes=scopes
        )

        if 'access_token' not in result:
            error = result.get('error_description', 'Unknown error')
            raise ValueError(f"Token refresh failed: {error}")

        logger.info("Microsoft token refreshed successfully")

        # Build updated credentials
        expires_in = result.get('expires_in', 3600)
        expiry = datetime.utcnow() + timedelta(seconds=expires_in)

        updated = {
            'token': result['access_token'],
            'refresh_token': result.get('refresh_token', refresh_token),
            'client_id': client_id,
            'tenant_id': tenant_id,
            'scopes': result.get('scope', scopes),
            'expiry': expiry.isoformat()
        }

        if client_secret:
            updated['client_secret'] = client_secret

        return updated

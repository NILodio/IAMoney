from pyngrok import ngrok, conf
import os
import time
from .app_logger import info, warning, error

class NgrokTunnel:
    def __init__(self, auth_token):
        self.auth_token = auth_token
        self.tunnel = None
        self.tunnel_url = None
        # Configure pyngrok to use system ngrok if available
        try:
            system_ngrok = '/usr/local/bin/ngrok'
            if os.path.exists(system_ngrok):
                conf.get_default().ngrok_path = system_ngrok
                info('Using system ngrok binary', {'path': system_ngrok})
        except Exception as e:
            warning('Could not configure system ngrok', {'error': str(e)})

    def create(self, port, max_retries=3):
        """Create an ngrok tunnel with retries and logging."""
        retries = max_retries
        while retries > 0:
            retries -= 1
            try:
                ngrok.set_auth_token(self.auth_token)
                self.kill_existing_tunnels()
                time.sleep(1)
                self.tunnel = ngrok.connect(port, bind_tls=True)
                self.tunnel_url = self.tunnel.public_url
                info('Ngrok tunnel created', {'url': self.tunnel_url})
                return self.tunnel_url
            except Exception as e:
                error('Failed to create Ngrok tunnel', {'error': str(e), 'retries_left': retries})
                self.kill_existing_tunnels()
                if retries > 0:
                    time.sleep(1)
        raise Exception('Failed to create Ngrok tunnel after multiple retries')

    def kill(self):
        """Kill the current tunnel and all ngrok processes."""
        try:
            if self.tunnel:
                ngrok.disconnect(self.tunnel.public_url)
                info('Ngrok tunnel killed')
                self.tunnel = None
                self.tunnel_url = None
            self.kill_existing_tunnels()
        except Exception as e:
            error('Failed to kill Ngrok tunnels', {'error': str(e)})

    @staticmethod
    def is_available():
        try:
            import pyngrok
            return True
        except ImportError:
            return False

    @staticmethod
    def kill_existing_tunnels():
        """Kill any existing ngrok processes (best effort)."""
        try:
            os.system('pkill -f ngrok 2>/dev/null')
            time.sleep(1)
        except Exception as e:
            warning('Failed to kill existing ngrok processes', {'error': str(e)})

    @staticmethod
    def register_shutdown_handler():
        import atexit
        def cleanup():
            try:
                os.system('pkill -f ngrok 2>/dev/null')
            except Exception:
                pass
        atexit.register(cleanup)

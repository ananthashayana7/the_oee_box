import logging
from backend.auth import admin_public_key
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature
import base64

logger = logging.getLogger("gatekeeper")

class CommandGatekeeper:
    def __init__(self):
        self.allowed_commands = ["START", "STOP", "RESET", "OPTIMIZE"]
        # Allow any machine in line1
        self.allowed_topic_prefix = "factory/line1/"

    def validate(self, command: str, target: str, signature: str = None) -> bool:
        if command not in self.allowed_commands:
            logger.warning(f"Command '{command}' denied: Not in allowlist")
            return False

        if not target.startswith(self.allowed_topic_prefix):
            logger.warning(f"Target '{target}' denied: Scope mismatch")
            return False

        if signature:
            try:
                # Mock Verification: Verify signature of 'command+target'
                # Client should sign: command + target
                message = (command + target).encode('utf-8')
                sig_bytes = base64.b64decode(signature)

                admin_public_key.verify(sig_bytes, message, ec.ECDSA(hashes.SHA256()))
                logger.info("Cryptographic Signature Verified")
            except Exception as e:
                logger.warning(f"Signature Verification Failed: {e}")
                return False

        return True

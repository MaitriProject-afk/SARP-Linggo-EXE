import os
import json
import hmac
import hashlib
import socket
import platform
from datetime import datetime, timedelta

SECRET_KEY = b"SARP_LINGGO_SECRET_HMAC_KEY_2026"

class LicenseManager:
    def __init__(self, storage_file="license.json"):
        self.storage_file = storage_file

    @staticmethod
    def get_local_hwid():
        """Generates a stable 4-character hex HWID based on Windows MachineGuid, MAC Address, and System Info."""
        machine_guid = ""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
            machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
        except Exception:
            pass

        import uuid
        mac_addr = str(uuid.getnode())
        raw_info = f"{machine_guid}-{mac_addr}-{socket.gethostname()}-{platform.node()}-{platform.processor()}"
        return hashlib.md5(raw_info.encode()).hexdigest()[:4].upper()

    @staticmethod
    def generate_token_raw(days=30, hwid="GLOB"):
        """
        Generates an offline HMAC signed license token.
        Format: SARP-[DAYS_HEX]-[HWID]-[HASH1]-[HASH2]
        """
        days_hex = f"{days:04X}"
        hwid_clean = hwid.strip().upper()[:4].zfill(4)
        payload = f"{days_hex}-{hwid_clean}"
        
        signature = hmac.new(SECRET_KEY, payload.encode('utf-8'), hashlib.sha256).hexdigest().upper()
        part1 = signature[:4]
        part2 = signature[4:8]
        
        return f"SARP-{days_hex}-{hwid_clean}-{part1}-{part2}"

    @classmethod
    def verify_token(cls, token_str):
        """
        Verifies token HMAC integrity and checks HWID matching.
        """
        try:
            parts = token_str.strip().upper().split('-')
            if len(parts) != 5 or parts[0] != "SARP":
                return False, "Invalid token format!", 0, ""

            days_hex, hwid_part, part1, part2 = parts[1], parts[2], parts[3], parts[4]
            days = int(days_hex, 16)
            
            payload = f"{days_hex}-{hwid_part}"
            expected_sig = hmac.new(SECRET_KEY, payload.encode('utf-8'), hashlib.sha256).hexdigest().upper()
            
            if expected_sig[:4] != part1 or expected_sig[4:8] != part2:
                return False, "Invalid signature! Token has been tampered with.", 0, ""

            current_hwid = cls.get_local_hwid()
            if hwid_part != current_hwid:
                return False, f"Token locked to HWID '{hwid_part}', but your device HWID is '{current_hwid}'!", days, hwid_part

            return True, "Token is valid!", days, hwid_part
        except Exception as e:
            return False, f"Verification error: {str(e)}", 0, ""

    def activate_token(self, token_str):
        valid, msg, days, hwid_part = self.verify_token(token_str)
        if not valid:
            return False, msg

        expiry_date = datetime.now() + timedelta(days=days)
        data = {
            "token": token_str,
            "hwid": hwid_part,
            "activated_at": datetime.now().isoformat(),
            "expires_at": expiry_date.isoformat(),
            "days": days
        }
        
        try:
            with open(self.storage_file, "w") as f:
                json.dump(data, f, indent=4)
            return True, f"Token activated successfully! Status: ACTIVE ({days} Days Remaining)"
        except Exception as e:
            return False, f"Failed to save license file: {str(e)}"

    def get_license_info(self):
        if not os.path.exists(self.storage_file):
            return {"active": False, "reason": "No license found"}
        
        try:
            with open(self.storage_file, "r") as f:
                data = json.load(f)

            expires_at = datetime.fromisoformat(data.get("expires_at"))
            now = datetime.now()
            
            if now > expires_at:
                return {"active": False, "reason": "License expired"}
                
            token_hwid = data.get("hwid", "")
            current_hwid = self.get_local_hwid()
            if token_hwid != current_hwid:
                return {"active": False, "reason": f"HWID mismatch (Locked to {token_hwid})"}

            remaining_days = (expires_at - now).days
            return {
                "active": True,
                "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S"),
                "remaining_days": remaining_days,
                "token": data.get("token"),
                "hwid": token_hwid
            }
        except Exception as e:
            return {"active": False, "reason": f"Corrupted license file: {str(e)}"}

    def is_active(self):
        info = self.get_license_info()
        return info.get("active", False)

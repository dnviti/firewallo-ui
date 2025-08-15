"""Security plugin interface for the Firewallo Plugin Framework."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel
from datetime import datetime, timedelta
from enum import Enum

from app.plugins.base import SecurityPluginError


class SecurityEventType(str, Enum):
    """Types of security events."""
    INTRUSION_ATTEMPT = "intrusion_attempt"
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHENTICATION_SUCCESS = "authentication_success"
    MALWARE_DETECTED = "malware_detected"
    POLICY_VIOLATION = "policy_violation"
    CERTIFICATE_EXPIRY = "certificate_expiry"
    CONFIGURATION_CHANGE = "configuration_change"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    BRUTE_FORCE = "brute_force"
    PORT_SCAN = "port_scan"
    DOS_ATTACK = "dos_attack"
    DATA_BREACH = "data_breach"


class ThreatLevel(str, Enum):
    """Threat severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class CertificateType(str, Enum):
    """Certificate types."""
    ROOT_CA = "root_ca"
    INTERMEDIATE_CA = "intermediate_ca"
    SERVER = "server"
    CLIENT = "client"
    CODE_SIGNING = "code_signing"
    EMAIL = "email"


class AuthMethod(str, Enum):
    """Authentication methods."""
    PASSWORD = "password"
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    HARDWARE_TOKEN = "hardware_token"
    BIOMETRIC = "biometric"
    CERTIFICATE = "certificate"


class PolicyAction(str, Enum):
    """Security policy actions."""
    ALLOW = "allow"
    DENY = "deny"
    AUDIT = "audit"
    REDIRECT = "redirect"
    QUARANTINE = "quarantine"
    ALERT = "alert"


class ScanType(str, Enum):
    """Types of security scans."""
    VULNERABILITY = "vulnerability"
    PORT = "port"
    MALWARE = "malware"
    COMPLIANCE = "compliance"
    CONFIGURATION = "configuration"


class CertificateCreate(BaseModel):
    """Model for creating a certificate."""
    name: str
    type: CertificateType
    common_name: str
    organization: Optional[str] = None
    organizational_unit: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    locality: Optional[str] = None
    email: Optional[str] = None
    validity_days: int = 365
    key_size: int = 2048
    algorithm: str = "RSA"
    san: List[str] = []  # Subject Alternative Names
    parent_ca_id: Optional[str] = None  # For signing
    description: Optional[str] = None
    auto_renew: bool = False
    renew_before_days: int = 30


class CertificateResponse(BaseModel):
    """Model for certificate response."""
    id: str
    name: str
    type: CertificateType
    common_name: str
    organization: Optional[str]
    organizational_unit: Optional[str]
    country: Optional[str]
    state: Optional[str]
    locality: Optional[str]
    email: Optional[str]
    serial_number: str
    fingerprint: str
    validity_days: int
    key_size: int
    algorithm: str
    san: List[str]
    parent_ca_id: Optional[str]
    description: Optional[str]
    auto_renew: bool
    renew_before_days: int
    created_at: datetime
    expires_at: datetime
    issuer: str
    subject: str
    public_key: str
    private_key_stored: bool
    status: str  # valid, expired, revoked


class CertificateUpdate(BaseModel):
    """Model for updating a certificate."""
    name: Optional[str] = None
    description: Optional[str] = None
    auto_renew: Optional[bool] = None
    renew_before_days: Optional[int] = None


class TwoFactorSetup(BaseModel):
    """Model for setting up two-factor authentication."""
    user_id: str
    method: AuthMethod
    phone_number: Optional[str] = None  # For SMS
    email: Optional[str] = None  # For email
    backup_codes_count: int = 10
    enforce: bool = False


class TwoFactorResponse(BaseModel):
    """Model for two-factor authentication response."""
    user_id: str
    method: AuthMethod
    enabled: bool
    configured_at: datetime
    last_used: Optional[datetime]
    backup_codes_remaining: int
    secret: Optional[str] = None  # For TOTP setup
    qr_code: Optional[str] = None  # For TOTP setup
    recovery_email: Optional[str]
    recovery_phone: Optional[str]


class SecurityPolicyCreate(BaseModel):
    """Model for creating a security policy."""
    name: str
    description: Optional[str] = None
    rules: List[Dict[str, Any]]
    action: PolicyAction
    priority: int = 100
    enabled: bool = True
    scope: Dict[str, Any] = {}  # Users, groups, IPs, etc.
    conditions: List[Dict[str, Any]] = []
    exceptions: List[Dict[str, Any]] = []
    schedule: Optional[Dict[str, Any]] = None  # Time-based activation
    logging: bool = True
    alert_on_violation: bool = False
    tags: List[str] = []


class SecurityPolicyResponse(BaseModel):
    """Model for security policy response."""
    id: str
    name: str
    description: Optional[str]
    rules: List[Dict[str, Any]]
    action: PolicyAction
    priority: int
    enabled: bool
    scope: Dict[str, Any]
    conditions: List[Dict[str, Any]]
    exceptions: List[Dict[str, Any]]
    schedule: Optional[Dict[str, Any]]
    logging: bool
    alert_on_violation: bool
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    last_evaluated: Optional[datetime]
    violation_count: int
    last_violation: Optional[datetime]


class SecurityPolicyUpdate(BaseModel):
    """Model for updating a security policy."""
    name: Optional[str] = None
    description: Optional[str] = None
    rules: Optional[List[Dict[str, Any]]] = None
    action: Optional[PolicyAction] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None
    scope: Optional[Dict[str, Any]] = None
    conditions: Optional[List[Dict[str, Any]]] = None
    exceptions: Optional[List[Dict[str, Any]]] = None
    schedule: Optional[Dict[str, Any]] = None
    logging: Optional[bool] = None
    alert_on_violation: Optional[bool] = None
    tags: Optional[List[str]] = None


class SecurityEvent(BaseModel):
    """Model for a security event."""
    id: str
    type: SecurityEventType
    threat_level: ThreatLevel
    timestamp: datetime
    source_ip: Optional[str]
    source_port: Optional[int]
    destination_ip: Optional[str]
    destination_port: Optional[int]
    user: Optional[str]
    process: Optional[str]
    details: Dict[str, Any]
    action_taken: Optional[str]
    blocked: bool
    alerted: bool
    policy_id: Optional[str]
    signature_id: Optional[str]
    raw_data: Optional[str]


class IntrusionSignature(BaseModel):
    """Model for intrusion detection signature."""
    id: str
    name: str
    pattern: str
    type: str  # regex, string, binary
    threat_level: ThreatLevel
    category: str
    description: Optional[str]
    enabled: bool
    action: PolicyAction
    created_at: datetime
    updated_at: datetime
    last_matched: Optional[datetime]
    match_count: int


class SecurityScanRequest(BaseModel):
    """Model for requesting a security scan."""
    scan_type: ScanType
    targets: List[str]  # IPs, hosts, or paths
    depth: str = "normal"  # quick, normal, deep
    schedule: Optional[str] = None  # Cron expression
    notifications: List[str] = []
    options: Dict[str, Any] = {}


class SecurityScanResult(BaseModel):
    """Model for security scan results."""
    id: str
    scan_type: ScanType
    started_at: datetime
    completed_at: Optional[datetime]
    status: str  # running, completed, failed
    targets: List[str]
    findings: List[Dict[str, Any]]
    vulnerabilities_found: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    report_url: Optional[str]
    remediation_suggestions: List[Dict[str, Any]]


class AuditLogEntry(BaseModel):
    """Model for audit log entry."""
    id: str
    timestamp: datetime
    user: Optional[str]
    ip_address: Optional[str]
    action: str
    resource: str
    resource_id: Optional[str]
    result: str  # success, failure
    details: Dict[str, Any]
    session_id: Optional[str]
    user_agent: Optional[str]


class SecurityStatistics(BaseModel):
    """Model for security statistics."""
    total_events_24h: int
    critical_events_24h: int
    blocked_attempts_24h: int
    active_policies: int
    enabled_signatures: int
    certificates_total: int
    certificates_expiring_soon: int
    two_factor_users: int
    last_scan: Optional[datetime]
    vulnerabilities_open: int
    compliance_score: float
    threat_level: ThreatLevel
    top_threats: List[Dict[str, Any]]
    top_sources: List[Dict[str, Any]]
    last_updated: datetime


class SecurityPluginInterface(ABC):
    """Interface that all security plugins must implement."""

    @abstractmethod
    async def create_certificate(self, cert_data: CertificateCreate) -> CertificateResponse:
        """Create a new certificate.

        Args:
            cert_data: Certificate configuration.

        Returns:
            CertificateResponse: Created certificate.

        Raises:
            SecurityPluginError: If certificate creation fails.
        """
        pass

    @abstractmethod
    async def list_certificates(self, **filters) -> List[CertificateResponse]:
        """List certificates with optional filtering.

        Args:
            **filters: Optional filters.

        Returns:
            List[CertificateResponse]: List of certificates.
        """
        pass

    @abstractmethod
    async def get_certificate(self, cert_id: str) -> Optional[CertificateResponse]:
        """Get a specific certificate by ID.

        Args:
            cert_id: ID of the certificate to retrieve.

        Returns:
            Optional[CertificateResponse]: Certificate if found.
        """
        pass

    @abstractmethod
    async def revoke_certificate(self, cert_id: str, reason: str) -> bool:
        """Revoke a certificate.

        Args:
            cert_id: ID of the certificate to revoke.
            reason: Revocation reason.

        Returns:
            bool: True if revocation was successful.
        """
        pass

    @abstractmethod
    async def setup_two_factor(self, setup_data: TwoFactorSetup) -> TwoFactorResponse:
        """Setup two-factor authentication for a user.

        Args:
            setup_data: Two-factor setup configuration.

        Returns:
            TwoFactorResponse: Two-factor setup details.
        """
        pass

    @abstractmethod
    async def verify_two_factor(self, user_id: str, code: str) -> bool:
        """Verify a two-factor authentication code.

        Args:
            user_id: User ID.
            code: Authentication code.

        Returns:
            bool: True if code is valid.
        """
        pass

    @abstractmethod
    async def create_policy(self, policy_data: SecurityPolicyCreate) -> SecurityPolicyResponse:
        """Create a new security policy.

        Args:
            policy_data: Policy configuration.

        Returns:
            SecurityPolicyResponse: Created policy.
        """
        pass

    @abstractmethod
    async def list_policies(self, **filters) -> List[SecurityPolicyResponse]:
        """List security policies with optional filtering.

        Args:
            **filters: Optional filters.

        Returns:
            List[SecurityPolicyResponse]: List of policies.
        """
        pass

    @abstractmethod
    async def get_policy(self, policy_id: str) -> Optional[SecurityPolicyResponse]:
        """Get a specific security policy by ID.

        Args:
            policy_id: ID of the policy to retrieve.

        Returns:
            Optional[SecurityPolicyResponse]: Policy if found.
        """
        pass

    @abstractmethod
    async def update_policy(self, policy_id: str, update_data: SecurityPolicyUpdate) -> Optional[SecurityPolicyResponse]:
        """Update a security policy.

        Args:
            policy_id: ID of the policy to update.
            update_data: Update data.

        Returns:
            Optional[SecurityPolicyResponse]: Updated policy.
        """
        pass

    @abstractmethod
    async def list_security_events(self, start_time: Optional[datetime] = None,
                                  end_time: Optional[datetime] = None,
                                  **filters) -> List[SecurityEvent]:
        """List security events with optional filtering.

        Args:
            start_time: Start of time range.
            end_time: End of time range.
            **filters: Additional filters.

        Returns:
            List[SecurityEvent]: List of security events.
        """
        pass

    @abstractmethod
    async def start_security_scan(self, scan_request: SecurityScanRequest) -> str:
        """Start a security scan.

        Args:
            scan_request: Scan configuration.

        Returns:
            str: Scan ID.
        """
        pass

    @abstractmethod
    async def get_scan_results(self, scan_id: str) -> Optional[SecurityScanResult]:
        """Get security scan results.

        Args:
            scan_id: ID of the scan.

        Returns:
            Optional[SecurityScanResult]: Scan results if available.
        """
        pass

    @abstractmethod
    async def get_audit_logs(self, start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None,
                           **filters) -> List[AuditLogEntry]:
        """Get audit logs with optional filtering.

        Args:
            start_time: Start of time range.
            end_time: End of time range.
            **filters: Additional filters.

        Returns:
            List[AuditLogEntry]: List of audit log entries.
        """
        pass

    @abstractmethod
    async def get_statistics(self) -> SecurityStatistics:
        """Get security statistics.

        Returns:
            SecurityStatistics: Current security statistics.
        """
        pass

    # Optional methods with default implementations
    async def export_certificate(self, cert_id: str, format: str = "pem") -> str:
        """Export a certificate in specified format.

        Args:
            cert_id: ID of the certificate to export.
            format: Export format (pem, der, p12).

        Returns:
            str: Exported certificate data.
        """
        cert = await self.get_certificate(cert_id)
        if not cert:
            raise SecurityPluginError(f"Certificate {cert_id} not found")

        if format == "pem":
            return cert.public_key
        else:
            raise NotImplementedError(f"Export format {format} not implemented")

    async def renew_certificate(self, cert_id: str) -> CertificateResponse:
        """Renew a certificate.

        Args:
            cert_id: ID of the certificate to renew.

        Returns:
            CertificateResponse: Renewed certificate.
        """
        cert = await self.get_certificate(cert_id)
        if not cert:
            raise SecurityPluginError(f"Certificate {cert_id} not found")

        # Create new certificate with same details
        new_cert_data = CertificateCreate(
            name=f"{cert.name}_renewed",
            type=cert.type,
            common_name=cert.common_name,
            organization=cert.organization,
            organizational_unit=cert.organizational_unit,
            country=cert.country,
            state=cert.state,
            locality=cert.locality,
            email=cert.email,
            validity_days=cert.validity_days,
            key_size=cert.key_size,
            algorithm=cert.algorithm,
            san=cert.san,
            parent_ca_id=cert.parent_ca_id,
            description=f"Renewed from {cert.id}",
            auto_renew=cert.auto_renew,
            renew_before_days=cert.renew_before_days
        )

        return await self.create_certificate(new_cert_data)

    async def generate_backup_codes(self, user_id: str, count: int = 10) -> List[str]:
        """Generate backup codes for two-factor authentication.

        Args:
            user_id: User ID.
            count: Number of codes to generate.

        Returns:
            List[str]: Generated backup codes.
        """
        import secrets
        import string

        codes = []
        for _ in range(count):
            code = ''.join(secrets.choice(string.digits) for _ in range(8))
            codes.append(f"{code[:4]}-{code[4:]}")

        return codes

    async def enable_intrusion_detection(self, signatures: List[str]) -> bool:
        """Enable intrusion detection with specific signatures.

        Args:
            signatures: List of signature IDs to enable.

        Returns:
            bool: True if enabled successfully.
        """
        # Default implementation
        for sig_id in signatures:
            # Would update signature status in actual implementation
            pass
        return True

    async def quarantine_threat(self, threat_id: str, duration: Optional[timedelta] = None) -> bool:
        """Quarantine a detected threat.

        Args:
            threat_id: ID of the threat.
            duration: Optional quarantine duration.

        Returns:
            bool: True if quarantined successfully.
        """
        # Default implementation would isolate the threat
        return True

    async def apply_security_updates(self) -> Dict[str, Any]:
        """Apply available security updates.

        Returns:
            Dict[str, Any]: Update results.
        """
        return {
            "updates_available": 0,
            "updates_applied": 0,
            "status": "up_to_date",
            "last_check": datetime.utcnow()
        }

    async def test_policy(self, policy_id: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test a security policy against sample data.

        Args:
            policy_id: ID of the policy to test.
            test_data: Test data to evaluate against policy.

        Returns:
            Dict[str, Any]: Test results.
        """
        policy = await self.get_policy(policy_id)
        if not policy:
            raise SecurityPluginError(f"Policy {policy_id} not found")

        # Simplified test implementation
        return {
            "policy_id": policy_id,
            "policy_name": policy.name,
            "action": policy.action,
            "would_trigger": True,  # Would evaluate rules in real implementation
            "test_time": datetime.utcnow(),
            "test_data": test_data
        }

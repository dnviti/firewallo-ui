"""Monitoring plugin interface for the Firewallo Plugin Framework."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel
from datetime import datetime, timedelta
from enum import Enum

from app.plugins.base import MonitoringPluginError


class MetricType(str, Enum):
    """Types of metrics."""
    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    BOOLEAN = "boolean"
    STRING = "string"


class MetricUnit(str, Enum):
    """Metric units."""
    BYTES = "bytes"
    KILOBYTES = "kilobytes"
    MEGABYTES = "megabytes"
    GIGABYTES = "gigabytes"
    BITS = "bits"
    PERCENT = "percent"
    COUNT = "count"
    SECONDS = "seconds"
    MILLISECONDS = "milliseconds"
    REQUESTS = "requests"
    PACKETS = "packets"
    CONNECTIONS = "connections"
    TEMPERATURE = "celsius"
    NONE = "none"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, Enum):
    """Alert status."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SILENCED = "silenced"


class MonitoringTargetType(str, Enum):
    """Types of monitoring targets."""
    HOST = "host"
    SERVICE = "service"
    CONTAINER = "container"
    NETWORK = "network"
    APPLICATION = "application"
    DATABASE = "database"
    CUSTOM = "custom"


class MetricCreate(BaseModel):
    """Model for creating a metric."""
    name: str
    type: MetricType
    value: Union[float, int, bool, str]
    unit: MetricUnit = MetricUnit.NONE
    labels: Dict[str, str] = {}
    description: Optional[str] = None
    timestamp: Optional[datetime] = None
    aggregation_method: Optional[str] = None  # avg, sum, min, max, last
    retention_days: int = 30
    tags: List[str] = []


class MetricResponse(BaseModel):
    """Model for metric response."""
    id: str
    name: str
    type: MetricType
    value: Union[float, int, bool, str]
    unit: MetricUnit
    labels: Dict[str, str]
    description: Optional[str]
    timestamp: datetime
    aggregation_method: Optional[str]
    retention_days: int
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    source: str  # Which target/collector this came from


class MetricQuery(BaseModel):
    """Model for querying metrics."""
    metric_names: Optional[List[str]] = None
    labels: Optional[Dict[str, str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    interval: Optional[str] = None  # e.g., "5m", "1h", "1d"
    aggregation: Optional[str] = None  # avg, sum, min, max
    group_by: Optional[List[str]] = None
    limit: int = 1000


class MetricSeriesResponse(BaseModel):
    """Model for time series metric data."""
    metric_name: str
    labels: Dict[str, str]
    unit: MetricUnit
    data_points: List[Dict[str, Any]]  # [{"timestamp": ..., "value": ...}]
    start_time: datetime
    end_time: datetime
    interval: str
    aggregation: Optional[str]
    total_points: int


class AlertRuleCreate(BaseModel):
    """Model for creating an alert rule."""
    name: str
    condition: str  # Expression like "cpu_usage > 80"
    severity: AlertSeverity
    metric_name: str
    threshold_value: Optional[float] = None
    comparison_operator: Optional[str] = None  # >, <, >=, <=, ==, !=
    duration: Optional[str] = None  # How long condition must be true (e.g., "5m")
    frequency: str = "1m"  # How often to check
    enabled: bool = True
    description: Optional[str] = None
    notification_channels: List[str] = []
    labels: Dict[str, str] = {}
    annotations: Dict[str, str] = {}
    cooldown_period: Optional[str] = None  # Prevent alert spam


class AlertRuleResponse(BaseModel):
    """Model for alert rule response."""
    id: str
    name: str
    condition: str
    severity: AlertSeverity
    metric_name: str
    threshold_value: Optional[float]
    comparison_operator: Optional[str]
    duration: Optional[str]
    frequency: str
    enabled: bool
    description: Optional[str]
    notification_channels: List[str]
    labels: Dict[str, str]
    annotations: Dict[str, str]
    cooldown_period: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_evaluation: Optional[datetime]
    evaluation_count: int
    trigger_count: int


class AlertRuleUpdate(BaseModel):
    """Model for updating an alert rule."""
    name: Optional[str] = None
    condition: Optional[str] = None
    severity: Optional[AlertSeverity] = None
    threshold_value: Optional[float] = None
    comparison_operator: Optional[str] = None
    duration: Optional[str] = None
    frequency: Optional[str] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None
    notification_channels: Optional[List[str]] = None
    labels: Optional[Dict[str, str]] = None
    annotations: Optional[Dict[str, str]] = None
    cooldown_period: Optional[str] = None


class AlertEvent(BaseModel):
    """Model for an alert event."""
    id: str
    rule_id: str
    rule_name: str
    severity: AlertSeverity
    status: AlertStatus
    metric_name: str
    metric_value: Union[float, int, bool, str]
    threshold_value: Optional[float]
    condition: str
    message: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    silenced_until: Optional[datetime] = None
    notification_sent: bool = False
    notification_channels: List[str] = []


class MonitoringTargetCreate(BaseModel):
    """Model for creating a monitoring target."""
    name: str
    type: MonitoringTargetType
    address: str  # IP, hostname, or identifier
    port: Optional[int] = None
    enabled: bool = True
    check_interval: str = "1m"
    timeout: str = "10s"
    retry_count: int = 3
    description: Optional[str] = None
    labels: Dict[str, str] = {}
    custom_config: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, str]] = None  # Should be encrypted


class MonitoringTargetResponse(BaseModel):
    """Model for monitoring target response."""
    id: str
    name: str
    type: MonitoringTargetType
    address: str
    port: Optional[int]
    enabled: bool
    check_interval: str
    timeout: str
    retry_count: int
    description: Optional[str]
    labels: Dict[str, str]
    custom_config: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    last_check: Optional[datetime]
    status: str  # up, down, unknown
    status_message: Optional[str]
    uptime_percentage: float
    response_time_ms: Optional[float]


class MonitoringTargetUpdate(BaseModel):
    """Model for updating a monitoring target."""
    name: Optional[str] = None
    address: Optional[str] = None
    port: Optional[int] = None
    enabled: Optional[bool] = None
    check_interval: Optional[str] = None
    timeout: Optional[str] = None
    retry_count: Optional[int] = None
    description: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    custom_config: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, str]] = None


class DashboardCreate(BaseModel):
    """Model for creating a dashboard."""
    name: str
    description: Optional[str] = None
    layout: Dict[str, Any]  # Dashboard layout configuration
    panels: List[Dict[str, Any]]  # Panel configurations
    refresh_interval: str = "30s"
    time_range: str = "1h"  # Default time range
    variables: Dict[str, Any] = {}  # Dashboard variables
    tags: List[str] = []
    shared: bool = False
    owner: Optional[str] = None


class DashboardResponse(BaseModel):
    """Model for dashboard response."""
    id: str
    name: str
    description: Optional[str]
    layout: Dict[str, Any]
    panels: List[Dict[str, Any]]
    refresh_interval: str
    time_range: str
    variables: Dict[str, Any]
    tags: List[str]
    shared: bool
    owner: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_viewed: Optional[datetime]
    view_count: int


class MonitoringStatistics(BaseModel):
    """Model for monitoring statistics."""
    total_metrics: int
    active_metrics: int
    total_alerts: int
    active_alerts: int
    critical_alerts: int
    total_targets: int
    active_targets: int
    down_targets: int
    total_dashboards: int
    metrics_ingestion_rate: float  # metrics per second
    alert_evaluation_rate: float  # evaluations per second
    storage_used_bytes: int
    oldest_metric: Optional[datetime]
    newest_metric: Optional[datetime]
    last_updated: datetime


class MonitoringPluginInterface(ABC):
    """Interface that all monitoring plugins must implement."""

    @abstractmethod
    async def create_metric(self, metric_data: MetricCreate) -> MetricResponse:
        """Create/record a new metric.

        Args:
            metric_data: Metric data.

        Returns:
            MetricResponse: Created metric information.

        Raises:
            MonitoringPluginError: If metric creation fails.
        """
        pass

    @abstractmethod
    async def query_metrics(self, query: MetricQuery) -> List[MetricSeriesResponse]:
        """Query metrics with filters and aggregations.

        Args:
            query: Query parameters.

        Returns:
            List[MetricSeriesResponse]: Time series data for matching metrics.
        """
        pass

    @abstractmethod
    async def delete_metrics(self, metric_name: str, before_date: Optional[datetime] = None) -> bool:
        """Delete metrics.

        Args:
            metric_name: Name of the metric to delete.
            before_date: Optional date to delete metrics before.

        Returns:
            bool: True if deletion was successful.
        """
        pass

    @abstractmethod
    async def create_alert_rule(self, rule_data: AlertRuleCreate) -> AlertRuleResponse:
        """Create a new alert rule.

        Args:
            rule_data: Alert rule configuration.

        Returns:
            AlertRuleResponse: Created alert rule.

        Raises:
            MonitoringPluginError: If rule creation fails.
        """
        pass

    @abstractmethod
    async def delete_alert_rule(self, rule_id: str) -> bool:
        """Delete an alert rule.

        Args:
            rule_id: ID of the rule to delete.

        Returns:
            bool: True if deletion was successful.
        """
        pass

    @abstractmethod
    async def list_alert_rules(self, **filters) -> List[AlertRuleResponse]:
        """List alert rules with optional filtering.

        Args:
            **filters: Optional filters (enabled, severity, etc.).

        Returns:
            List[AlertRuleResponse]: List of alert rules.
        """
        pass

    @abstractmethod
    async def get_alert_rule(self, rule_id: str) -> Optional[AlertRuleResponse]:
        """Get a specific alert rule by ID.

        Args:
            rule_id: ID of the rule to retrieve.

        Returns:
            Optional[AlertRuleResponse]: Alert rule if found.
        """
        pass

    @abstractmethod
    async def update_alert_rule(self, rule_id: str, update_data: AlertRuleUpdate) -> Optional[AlertRuleResponse]:
        """Update an alert rule.

        Args:
            rule_id: ID of the rule to update.
            update_data: Update data.

        Returns:
            Optional[AlertRuleResponse]: Updated alert rule.
        """
        pass

    @abstractmethod
    async def list_alerts(self, status: Optional[AlertStatus] = None, **filters) -> List[AlertEvent]:
        """List alert events with optional filtering.

        Args:
            status: Optional status filter.
            **filters: Additional filters.

        Returns:
            List[AlertEvent]: List of alert events.
        """
        pass

    @abstractmethod
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert.

        Args:
            alert_id: ID of the alert to acknowledge.
            acknowledged_by: User acknowledging the alert.

        Returns:
            bool: True if acknowledgment was successful.
        """
        pass

    @abstractmethod
    async def create_target(self, target_data: MonitoringTargetCreate) -> MonitoringTargetResponse:
        """Create a new monitoring target.

        Args:
            target_data: Target configuration.

        Returns:
            MonitoringTargetResponse: Created target.
        """
        pass

    @abstractmethod
    async def delete_target(self, target_id: str) -> bool:
        """Delete a monitoring target.

        Args:
            target_id: ID of the target to delete.

        Returns:
            bool: True if deletion was successful.
        """
        pass

    @abstractmethod
    async def list_targets(self, type: Optional[MonitoringTargetType] = None, **filters) -> List[MonitoringTargetResponse]:
        """List monitoring targets with optional filtering.

        Args:
            type: Optional target type filter.
            **filters: Additional filters.

        Returns:
            List[MonitoringTargetResponse]: List of targets.
        """
        pass

    @abstractmethod
    async def get_target(self, target_id: str) -> Optional[MonitoringTargetResponse]:
        """Get a specific monitoring target by ID.

        Args:
            target_id: ID of the target to retrieve.

        Returns:
            Optional[MonitoringTargetResponse]: Target if found.
        """
        pass

    @abstractmethod
    async def update_target(self, target_id: str, update_data: MonitoringTargetUpdate) -> Optional[MonitoringTargetResponse]:
        """Update a monitoring target.

        Args:
            target_id: ID of the target to update.
            update_data: Update data.

        Returns:
            Optional[MonitoringTargetResponse]: Updated target.
        """
        pass

    @abstractmethod
    async def check_target_health(self, target_id: str) -> Dict[str, Any]:
        """Check health of a specific target.

        Args:
            target_id: ID of the target to check.

        Returns:
            Dict[str, Any]: Health check results.
        """
        pass

    @abstractmethod
    async def get_statistics(self) -> MonitoringStatistics:
        """Get monitoring system statistics.

        Returns:
            MonitoringStatistics: Current statistics.
        """
        pass

    # Optional methods with default implementations
    async def create_dashboard(self, dashboard_data: DashboardCreate) -> DashboardResponse:
        """Create a new dashboard.

        Args:
            dashboard_data: Dashboard configuration.

        Returns:
            DashboardResponse: Created dashboard.
        """
        raise NotImplementedError("Dashboard functionality not implemented")

    async def list_dashboards(self, **filters) -> List[DashboardResponse]:
        """List dashboards with optional filtering.

        Args:
            **filters: Optional filters.

        Returns:
            List[DashboardResponse]: List of dashboards.
        """
        raise NotImplementedError("Dashboard functionality not implemented")

    async def get_dashboard(self, dashboard_id: str) -> Optional[DashboardResponse]:
        """Get a specific dashboard by ID.

        Args:
            dashboard_id: ID of the dashboard to retrieve.

        Returns:
            Optional[DashboardResponse]: Dashboard if found.
        """
        raise NotImplementedError("Dashboard functionality not implemented")

    async def export_metrics(self, format: str = "json", **filters) -> str:
        """Export metrics in specified format.

        Args:
            format: Export format (json, csv, prometheus).
            **filters: Filters for metrics to export.

        Returns:
            str: Exported metrics data.
        """
        metrics = await self.query_metrics(MetricQuery(**filters))

        if format == "json":
            import json
            return json.dumps([m.dict() for m in metrics], default=str)
        elif format == "csv":
            import csv
            import io
            output = io.StringIO()
            if metrics:
                writer = csv.DictWriter(output, fieldnames=metrics[0].dict().keys())
                writer.writeheader()
                for metric in metrics:
                    writer.writerow(metric.dict())
            return output.getvalue()
        else:
            raise MonitoringPluginError(f"Unsupported export format: {format}")

    async def silence_alert(self, alert_id: str, duration: timedelta, silenced_by: str) -> bool:
        """Silence an alert for a specified duration.

        Args:
            alert_id: ID of the alert to silence.
            duration: How long to silence the alert.
            silenced_by: User silencing the alert.

        Returns:
            bool: True if silencing was successful.
        """
        # Default implementation
        alerts = await self.list_alerts()
        for alert in alerts:
            if alert.id == alert_id:
                alert.status = AlertStatus.SILENCED
                alert.silenced_until = datetime.utcnow() + duration
                return True
        return False

    async def test_alert_rule(self, rule_id: str) -> Dict[str, Any]:
        """Test an alert rule to see if it would trigger.

        Args:
            rule_id: ID of the rule to test.

        Returns:
            Dict[str, Any]: Test results.
        """
        rule = await self.get_alert_rule(rule_id)
        if not rule:
            raise MonitoringPluginError(f"Alert rule {rule_id} not found")

        # Query recent metrics
        query = MetricQuery(
            metric_names=[rule.metric_name],
            start_time=datetime.utcnow() - timedelta(minutes=5),
            end_time=datetime.utcnow()
        )
        metrics = await self.query_metrics(query)

        return {
            "rule_id": rule_id,
            "rule_name": rule.name,
            "would_trigger": len(metrics) > 0,  # Simplified
            "current_metrics": metrics,
            "test_time": datetime.utcnow()
        }

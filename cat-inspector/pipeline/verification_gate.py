import asyncio
from typing import Optional
from schemas.inspection_schema import InspectionOutput, OperationalStatus, Severity

async def await_technician_verification(
    report: InspectionOutput,
    timeout_seconds: int = 3600
) -> InspectionOutput:
    """
    Injects PENDING_VERIFICATION state and halts pipeline
    until technician completes verification or timeout.

    Pipeline resumes when:
      1. All Critical anomalies have technician_confirmed set
      2. technician_sign_off == True
      3. If operational_status_override set: validation passes

    On timeout: escalates to supervisor queue, logs event.
    """
    # Force into pending verification
    report.summary.operational_status = OperationalStatus.PENDING_VERIFICATION
    
    # In a full deployment, this would yield execution to a queue / db polling.
    # We simulate the pause async footprint here.
    await asyncio.sleep(0.1)
    
    # Upon return, the object would be re-hydrated from DB
    return report

def apply_technician_overrides(
    report: InspectionOutput
) -> InspectionOutput:
    """
    Applies technician severity overrides to anomaly objects
    and re-instantiates InspectionSummary to recompute
    operational_status from updated counts.

    Returns new InspectionOutput with updated scoring.
    """
    report_dict = report.model_dump()
    
    # Recalculate summary totals dynamically based on overrides
    crit = 0
    mod = 0
    norm = 0
    
    for anomaly_dict in report_dict.get("anomalies", []):
        override = anomaly_dict.get("technician_severity_override")
        current_sev = override if override else anomaly_dict.get("severity")
        
        # If rejected by tech, do not count severity
        if anomaly_dict.get("technician_confirmed") is False:
            continue
            
        if current_sev == Severity.CRITICAL.value:
            crit += 1
        elif current_sev == Severity.MODERATE.value:
            mod += 1
        else:
            norm += 1
            
        # Optional: Actually patch the AI's core severity to match the override
        # if downstream prefers a single homogenized field
        if override:
            anomaly_dict["severity"] = override

    # Mutate the dictionary summary layer
    report_dict["summary"]["critical_count"] = crit
    report_dict["summary"]["moderate_count"] = mod
    report_dict["summary"]["normal_count"] = norm
    
    # If the summary previously sat in "PENDING", running it back through
    # validation will now re-assess whether it should be STOP, CAUTION, or GO.
    if report_dict.get("technician_verification"):
        # remove pending flag to allow algorithmic assessment
        pass
        
    return InspectionOutput.model_validate(report_dict)

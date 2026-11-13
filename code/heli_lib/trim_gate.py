"""Pure fail-closed development validation gate for native JSBSim hover trim."""


def decide(records):
    if not records:
        return "UNRESOLVED"
    screened = [r for r in records if r["status"] == "POST_TRIM_SCREENED"]
    if any(r["screen"]["status"] == "PASS_CANDIDATE" for r in screened):
        return "TRIM_CANDIDATE_NOT_VALIDATED"
    if any(r["status"] == "BACKEND_ERROR" for r in records):
        return "UNRESOLVED"
    return "NO_STABLE_HOVER_IN_BOUNDED_NATIVE_TRIM_TRIALS"

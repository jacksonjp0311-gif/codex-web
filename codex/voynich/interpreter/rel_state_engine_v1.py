def rel_state(packet):
    prefix = packet["prefix"]
    core   = packet["core"]
    bench  = packet["bench"]
    suffix = packet["suffix"]

    roles = []
    state = {"depth":0,"phase":0,"flow":0}

    # Prefix
    if prefix == "qo":
        roles.append("REL_ROUTE_INGEST")
    elif prefix == "q":
        roles.append("REL_ROUTE")

    # Core (gallows)
    if core:
        for g in ["k","t","p","f"]:
            if g in core:
                roles.append(f"REL_GALLOWS_{g.upper()}")
                state["phase"] += 1

    # Bench
    if bench:
        roles.append(f"REL_BENCH_{bench}")

    # Suffix/state
    if suffix:
        if suffix == "y":
            roles.append("REL_TERM_Y")
            state["flow"] = +1
        if suffix == "dy":
            roles.append("REL_TERM_DY")
            state["flow"] = +1
            state["phase"] += 1
        if "ai" in suffix:
            roles.append("REL_EXTEND")
            state["depth"] = suffix.count("i")

    return {"roles":roles,"state":state}

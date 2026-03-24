def resolve_selected_vars(output_columns=None):
    """Return the list of AVAILABLE_VARIABLES entries matching the selected keys.
    If output_columns is None, returns the default set. Preserves registry order."""
    if output_columns is None:
        return [v for v in AVAILABLE_VARIABLES if v["default"]]
    selected_set = set(output_columns)
    return [v for v in AVAILABLE_VARIABLES if v["key"] in selected_set]


def build_data_requests(selected_vars):
    """Build Pulse SEDataRequest list from selected variable definitions."""
    data_requests = []
    for var in selected_vars:
        unit = PULSE_UNIT_MAP.get(var.get("pulse_unit")) if var.get("pulse_unit") else None
        kwargs = {}
        if unit is not None:
            kwargs["unit"] = unit

        if var["request_type"] == "physiology":
            data_requests.append(SEDataRequest.create_physiology_request(var["pulse_name"], **kwargs))
        elif var["request_type"] == "mechanical_ventilator":
            data_requests.append(SEDataRequest.create_mechanical_ventilator_request(var["pulse_name"], **kwargs))
        elif var["request_type"] == "compartment_substance":
            data_requests.append(
                SEDataRequest.create_liquid_compartment_substance_request(
                    var["compartment"], var["pulse_name"], var["property"], **kwargs
                )
            )
    return data_requests

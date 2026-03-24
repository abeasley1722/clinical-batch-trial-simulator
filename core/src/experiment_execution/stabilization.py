def _extract_batch_patient_weight(patient_json, patient_name, initial_blood_volume_ml):
    """Extract patient weight in kg for batch worker.

    Tries in order:
    1. patient_json state file (CurrentPatient.Weight)
    2. patient_json patient definition (Weight)
    3. Read from state file on disk
    4. Fallback: estimate from blood volume
    """
    weight_kg = None

    # 1. Patient JSON (state file or patient definition)
    if patient_json:
        # State file format: CurrentPatient.Weight.ScalarMass
        if "CurrentPatient" in patient_json:
            weight_data = patient_json.get("CurrentPatient", {}).get("Weight", {}).get("ScalarMass", {})
        else:
            # Patient definition format: Weight.ScalarMass
            weight_data = patient_json.get("Weight", {}).get("ScalarMass", {})

        if weight_data:
            value = weight_data.get("Value")
            unit = weight_data.get("Unit", "lb")
            if value:
                if unit == "kg":
                    weight_kg = value
                else:  # Default to lb
                    weight_kg = value * 0.453592

    # 2. Read from state file on disk
    elif patient_name:
        try:
            import json as json_module
            state_path = f"./states/{patient_name}" if not os.path.isabs(patient_name) else patient_name
            if os.path.exists(state_path):
                with open(state_path, 'r') as f:
                    state_data = json_module.load(f)
                weight_data = state_data.get("CurrentPatient", {}).get("Weight", {}).get("ScalarMass", {})
                if weight_data:
                    value = weight_data.get("Value")
                    unit = weight_data.get("Unit", "lb")
                    if value:
                        if unit == "kg":
                            weight_kg = value
                        else:
                            weight_kg = value * 0.453592
        except Exception:
            pass  # Fall through to estimation

    # 3. Fallback: estimate from blood volume
    if weight_kg is None or weight_kg < 20:
        weight_kg = initial_blood_volume_ml / 70.0
        if weight_kg < 20:
            weight_kg = 70.0  # Default adult weight

    return weight_kg

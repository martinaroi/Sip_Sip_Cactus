def evaluate_moisture(plant, moisture):
    """Evaluate moisture level against plant's threshold"""
    threshold = plant.moisture_threshold
    
    # Calculate boundary values
    danger_low_upper_bound = threshold * 0.6
    warning_low_upper_bound = threshold * 0.8
    optimal_upper_bound = threshold * 1.2
    warning_high_upper_bound = threshold * 1.4
    
    # Evaluate moisture level
    if moisture < danger_low_upper_bound:
        return {
            "status": "Danger",
            "detail": "Critically Dry - needs immediate watering!",
            "color": "red",
            "icon": " 🆘🐫"
        }
    elif moisture < warning_low_upper_bound:
        return {
            "status": "Warning",
            "detail": "Getting dry - consider watering soon",
            "color": "orange",
            "icon": "🔥"
        }
    elif moisture <= optimal_upper_bound:
        return {
            "status": "Optimal",
            "detail": "Perfect hydration!",
            "color": "green",
            "icon": "✨🌱✨"
        }
    elif moisture <= warning_high_upper_bound:
        return {
            "status": "Warning",
            "detail": "Too wet - reduce watering",
            "color": "orange",
            "icon": "💦"
        }
    else:
        return {
            "status": "Danger",
            "detail": "Waterlogged - check drainage immediately!",
            "color": "red",
            "icon": "🆘🌊"
        }
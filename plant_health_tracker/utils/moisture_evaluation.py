def evaluate_moisture(plant, moisture):
    """Evaluate moisture level against plant's threshold"""
    threshold = plant.moisture_threshold

    danger_low_upper_bound = threshold * 0.6
    warning_low_upper_bound = threshold * 0.8
    optimal_upper_bound = threshold * 1.2
    warning_high_upper_bound = threshold * 1.4
    
    # Evaluate moisture level
    if moisture < danger_low_upper_bound:
        return ("😱 SOS! Dangerously dry - needs immediate watering!", "red")
    elif moisture < warning_low_upper_bound:
        return ("🤔 Warning: Getting dry - consider watering soon", "orange")
    elif moisture <= optimal_upper_bound:
        return ("🥳 Optimal moisture level - perfect hydration!", "green")
    elif moisture <= warning_high_upper_bound:
        return ("😬 Warning: Too wet - reduce watering", "orange")
    else:
        return ("🆘 Danger: Waterlogged - check drainage immediately!", "red")
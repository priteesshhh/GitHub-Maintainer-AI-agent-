    def _fix_speed_property(self, block: str) -> Optional[CodeFix]:
        """Fixes a Speed property implementation."""
        # Example old code:
        # public float Speed { get; set; }
        # or
        # public float Speed { get { return _speed; } set { _speed = value; } }
        
        new_code = '''public float Speed
    {
        get { return _speed; }
        set
        {
            // Validate speed value
            if (float.IsNaN(value) || float.IsInfinity(value))
            {
                Logger.LogWarning("Invalid speed value received");
                _speed = 0f;
                return;
            }
            
            // Handle very small values
            if (Math.Abs(value) <= 0.01f)
            {
                _speed = 0f;
                DisplayedSpeed = "Stopped";
                Logger.LogDebug("Speed below threshold, marked as stopped");
            }
            else
            {
                _speed = value;
                DisplayedSpeed = $"{_speed:F1} MPH";
                Logger.LogDebug($"Speed updated to {DisplayedSpeed}");
            }
        }
    }
    
    private float _speed;
    public string DisplayedSpeed { get; private set; }'''
        
        return CodeFix(
            file_path="",
            old_code=block,
            new_code=new_code,
            description="Enhanced Speed property with validation and proper display formatting"
        )
    
    def _fix_speed_method(self, block: str) -> Optional[CodeFix]:
        """Fixes a speed calculation method."""
        if "GetSpeed" in block:
            new_code = '''public float GetSpeed()
    {
        try
        {
            // Calculate raw speed
            float speed = CalculateRawSpeed();
            
            // Validate calculation
            if (float.IsNaN(speed) || float.IsInfinity(speed))
            {
                Logger.LogWarning("Speed calculation returned invalid value");
                return 0f;
            }
            
            // Handle very small values
            if (Math.Abs(speed) <= 0.01f)
            {
                Logger.LogDebug("Speed below threshold, returning 0");
                return 0f;
            }
            
            Logger.LogDebug($"Calculated speed: {speed:F1} MPH");
            return speed;
        }
        catch (Exception ex)
        {
            Logger.LogError($"Error calculating speed: {ex.Message}");
            return 0f;
        }
    }'''
        else:
            new_code = '''private void UpdateSpeed(float newSpeed)
    {
        try
        {
            // Validate input
            if (float.IsNaN(newSpeed) || float.IsInfinity(newSpeed))
            {
                Logger.LogWarning("Invalid speed value provided");
                Speed = 0f;
                return;
            }
            
            // Update speed with proper validation
            Speed = Math.Abs(newSpeed) <= 0.01f ? 0f : newSpeed;
            
            // Update status if needed
            if (Speed == 0f && Status != VehicleStatus.Stopped)
            {
                Status = VehicleStatus.Stopped;
                Logger.LogInformation("Vehicle has stopped");
            }
            else if (Speed > 0f && Status == VehicleStatus.Stopped)
            {
                Status = VehicleStatus.Moving;
                Logger.LogInformation($"Vehicle is moving at {Speed:F1} MPH");
            }
        }
        catch (Exception ex)
        {
            Logger.LogError($"Error updating speed: {ex.Message}");
            Speed = 0f;
        }
    }'''
        
        return CodeFix(
            file_path="",
            old_code=block,
            new_code=new_code,
            description="Enhanced speed calculation with proper validation and error handling"
        )
    
    def _fix_speed_comparison(self, block: str) -> Optional[CodeFix]:
        """Fixes speed comparison code."""
        # Handle simple zero comparisons
        if re.search(r'if\s*\(\s*speed\s*==\s*0', block):
            new_code = '''// Check if vehicle is effectively stopped
if (Math.Abs(speed) <= 0.01f)
{
    speed = 0f;  // Explicitly set to zero
    Status = VehicleStatus.Stopped;
    DisplayedSpeed = "Stopped";
    Logger.LogDebug("Vehicle speed below threshold, marked as stopped");
}'''
        # Handle threshold comparisons
        elif re.search(r'if\s*\(\s*speed\s*[<>]=?\s*', block):
            new_code = '''// Check speed against threshold
if (Math.Abs(speed) <= 0.01f)
{
    speed = 0f;
    Status = VehicleStatus.Stopped;
    DisplayedSpeed = "Stopped";
    Logger.LogDebug("Vehicle stopped");
}
else if (speed < MinSpeed)
{
    Logger.LogWarning($"Speed {speed:F1} MPH is below minimum threshold {MinSpeed} MPH");
    speed = MinSpeed;
    DisplayedSpeed = $"{speed:F1} MPH";
}
else
{
    DisplayedSpeed = $"{speed:F1} MPH";
    Logger.LogDebug($"Speed updated to {DisplayedSpeed}");
}'''
        else:
            return None
        
        return CodeFix(
            file_path="",
            old_code=block,
            new_code=new_code,
            description="Improved speed comparison with proper thresholds and status updates"
        )
    
    def _fix_speed_general(self, block: str) -> Optional[CodeFix]:
        """Fixes general speed-related code."""
        # Handle speed assignments
        if re.search(r'speed\s*=\s*[^;]+;', block):
            new_code = '''// Update speed with validation
try
{
    float newSpeed = CalculateSpeed();
    
    // Validate calculation
    if (float.IsNaN(newSpeed) || float.IsInfinity(newSpeed))
    {
        Logger.LogWarning("Speed calculation returned invalid value");
        newSpeed = 0f;
    }
    
    // Apply speed with proper threshold handling
    speed = Math.Abs(newSpeed) <= 0.01f ? 0f : newSpeed;
    
    // Update display
    DisplayedSpeed = speed == 0f ? "Stopped" : $"{speed:F1} MPH";
    Logger.LogDebug($"Speed updated to {DisplayedSpeed}");
}
catch (Exception ex)
{
    Logger.LogError($"Error updating speed: {ex.Message}");
    speed = 0f;
    DisplayedSpeed = "Error";
}'''
            
            return CodeFix(
                file_path="",
                old_code=block,
                new_code=new_code,
                description="Added comprehensive speed validation and error handling"
            )
        
        return None

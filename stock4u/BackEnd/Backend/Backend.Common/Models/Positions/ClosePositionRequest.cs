namespace Backend.Common.Models.Positions;

public class ClosePositionRequest
{
    public string UserId { get; set; } = null!;
    
    public string PositionId { get; set; } = null!;
    
    public decimal ClosePrice { get; set; }
    
    public DateTime CloseTime { get; set; }
    
    public decimal SharesCount { get; set; }
}
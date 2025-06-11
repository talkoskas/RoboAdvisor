namespace Backend.Common.Models.Positions;

public class EditStopLimitRequest
{
    public string UserId { get; set; } = null!;

    public string PositionId { get; set; } = null!;

    public decimal StopLimitPrice { get; set; }
}
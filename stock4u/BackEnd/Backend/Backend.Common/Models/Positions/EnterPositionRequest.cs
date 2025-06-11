namespace Backend.Common.Models.Positions;

public class EnterPositionRequest
{
    public string UserId { get; set; } = null!;

    public Position Position { get; set; } = null!;
}
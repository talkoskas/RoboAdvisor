using MongoDB.Bson.Serialization.Attributes;

namespace Backend.Common.Models.Positions;

[BsonIgnoreExtraElements]
public class UserPositionHistory
{
    public string UserId { get; set; } = null!;

    public ClosedPosition ClosedPosition { get; set; } = null!;
}
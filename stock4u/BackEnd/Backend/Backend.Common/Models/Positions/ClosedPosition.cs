using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace Backend.Common.Models.Positions;

public class ClosedPosition : Position
{
    public decimal ExitPrice { get; set; }
    
    public DateTime ExitTime { get; set; }
    
    [BsonRepresentation(BsonType.String)]
    public PositionFeedback PositionFeedback { get; set; }

}
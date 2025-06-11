using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace Backend.Common.Models.Positions;

public class Position
{
    public string PositionId { get; set; } = null!;

    public string ShareSymbol { get; set; } = null!;
    
    public string ShareCategory { get; set; } = null!;

    public decimal EntryPrice { get; set; }

    public decimal SharesCount { get; set; }

    [BsonRepresentation(BsonType.String)]
    public PositionType PositionType { get; set; }
    
    public DateTime EntryTime { get; set; }

    public decimal StopLimitPrice { get; set; }
}
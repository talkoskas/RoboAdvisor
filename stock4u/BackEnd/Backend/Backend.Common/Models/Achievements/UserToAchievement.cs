using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace Backend.Common.Models.Achievements;

[BsonIgnoreExtraElements]
public class UserToAchievement
{
    public string UserId { get; set; } = null!;

    [BsonRepresentation(BsonType.String)]
    public AchievementType AchievementType { get; set; }

    public DateTime AchievedTime { get; set; }
}
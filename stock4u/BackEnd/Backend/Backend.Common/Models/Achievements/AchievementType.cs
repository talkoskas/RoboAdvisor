using System.Text.Json.Serialization;

namespace Backend.Common.Models.Achievements;

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum AchievementType
{
    FirstLongPosition,
    FirstShortPosition,
    FivePercentageGain,
    FirstPositionClose,
    TenPositions,
    TenPercentageProfit,
    PositiveFeedback
}
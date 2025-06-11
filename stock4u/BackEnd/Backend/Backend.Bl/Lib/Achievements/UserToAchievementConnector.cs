using Backend.Bl.Interfaces;
using Backend.Common.Interfaces.Positions;
using Backend.Common.Models.Achievements;
using Backend.Common.Models.Positions;
using Backend.InvestingAdvisor.Lib.Utils;

namespace Backend.Bl.Lib.Achievements;

public class UserToAchievementConnector(IPositionsRetriever positionsRetriever, IPositionsHandler positionsHandler)
    : IUserToAchievementConnector
{
    private const int InitialUserBalance = 1000000;

    public async Task<List<AchievementType>> GetUserNewAchievementsAsync(string userId,
        List<AchievementType> currentAchievements)
    {
        var newUserAchievements = new List<AchievementType>();
        var achievementsToCheck =
            Enum.GetValues(typeof(AchievementType)).Cast<AchievementType>().Except(currentAchievements);
        foreach (var achievementType in achievementsToCheck)
        {
            if (await HasAchievedAsync(userId, achievementType))
            {
                newUserAchievements.Add(achievementType);
            }
        }

        return newUserAchievements;
    }

    private async Task<bool> HasAchievedAsync(string userId, AchievementType achievementType)
    {
        var userPositions = await positionsRetriever.GetUserPositionsByIdAsync(userId);
        var userPositionsHistory = await positionsRetriever.GetUserPositionsHistoryAsync(userId);

        return achievementType switch
        {
            AchievementType.FirstLongPosition =>
                HasEnteredFirstPosition(PositionType.Long, userPositions.Positions,userPositionsHistory),
            AchievementType.FirstShortPosition =>
                HasEnteredFirstPosition(PositionType.Short, userPositions.Positions, userPositionsHistory),
            AchievementType.FivePercentageGain =>
                await HasGainedFivePercentageInPositionAsync(userPositions.Positions, userPositionsHistory),
            AchievementType.FirstPositionClose => HasClosedFirstPosition(userPositionsHistory),
            AchievementType.TenPositions => HasEnteredTenPositions(userPositions.Positions, userPositionsHistory),
            AchievementType.TenPercentageProfit => await HasGainedTenPercentageProfitAsync(userPositions),
            AchievementType.PositiveFeedback => HasPositiveFeedback(userPositionsHistory),
            _ => throw new ArgumentOutOfRangeException(nameof(achievementType), achievementType, null)
        };
    }

    private static bool HasEnteredFirstPosition(PositionType positionType,
        List<Position> userPositions, List<UserPositionHistory> userPositionsHistory)
    {
        return userPositions.Any(position => position.PositionType == positionType) ||
               userPositionsHistory.Any(position => position.ClosedPosition.PositionType == positionType);
    }

    private static bool HasClosedFirstPosition(List<UserPositionHistory> userPositionsHistory)
    {
        return userPositionsHistory.Any();
    }

    private static bool HasEnteredTenPositions(List<Position> userPositions,
        List<UserPositionHistory> userPositionsHistory)
    {
        return userPositions.Count + userPositionsHistory.Count >= 10;
    }

    private async Task<bool> HasGainedTenPercentageProfitAsync(UserPositions userPositions)
    {
        var userNetWorth = await positionsHandler.CalculateUserNetWorth(userPositions);
        var percentageGain = StatisticsCalculator.CalculateChangePercentage(InitialUserBalance, userNetWorth);
        return percentageGain >= 10;
    }

    private static bool HasPositiveFeedback(List<UserPositionHistory> userPositionsHistory)
    {
        return userPositionsHistory.Any(position =>
            position.ClosedPosition.PositionFeedback == PositionFeedback.Positive);
    }

    private async Task<bool> HasGainedFivePercentageInPositionAsync(List<Position> userPositions,
        List<UserPositionHistory> userPositionsHistory)
    {
        var allPositions = userPositions.Union(userPositionsHistory.Select(position => position.ClosedPosition));
        foreach (var userPosition in allPositions)
        {
            if (await positionsHandler.CalculatePositionChangePercentage(userPosition) > 5)
            {
                return true;
            }
        }

        return false;
    }
}
using Backend.Common.Interfaces.Achievements;
using Backend.Common.Interfaces.Positions;
using Backend.Common.Interfaces.Stocks;
using Backend.Common.Models.Achievements;
using Backend.Common.Models.Positions;
using Backend.InvestingAdvisor.Lib.Utils;

namespace Backend.Bl.Lib;

public class PositionsHandler(
    IPositionsRetriever positionsRetriever,
    IPositionsUpdater positionsUpdater,
    IStockPriceRetriever stockPriceRetriever,
    IAchievementsRetriever achievementsRetriever) : IPositionsHandler
{
    public async Task<UserInvestmentStatus> GetUserInvestmentStatusAsync(string userId)
    {
        var userPositions = await positionsRetriever.GetUserPositionsByIdAsync(userId);
        var achievements = await GetUserAchievementsAsync(userId);
        var userInvestmentStatus = await CreateUserInvestmentStatusAsync(userPositions, achievements);

        return userInvestmentStatus;
    }

    public async Task<List<UserInvestmentStatus>> GetTopTenUsersAsync()
    {
        var allUsersPositions = await positionsRetriever.GetAllUserPositionsAsync();
        var allUsersStatus = new List<UserInvestmentStatus>();
        foreach (var userPositions in allUsersPositions)
        {
            var userAchievements = await GetUserAchievementsAsync(userPositions.UserId);
            var userInvestmentStatus = await CreateUserInvestmentStatusAsync(userPositions, userAchievements);
            allUsersStatus.Add(userInvestmentStatus);
        }

        return allUsersStatus.OrderByDescending(status => status.AchievementsPoints).Take(10).ToList();
    }

    public async Task<IEnumerable<ClosedPosition>> GetUserPositionsHistoryAsync(string userId)
    {
        var userPositionsHistory = await positionsRetriever.GetUserPositionsHistoryAsync(userId);
        return userPositionsHistory.Select(position => position.ClosedPosition);
    }

    public async Task EnterPositionAsync(EnterPositionRequest enterPositionRequest)
    {
        await positionsUpdater.EnterPositionAsync(enterPositionRequest.UserId, enterPositionRequest.Position);
    }

    public async Task EditStopLimitAsync(EditStopLimitRequest editStopLimitRequest)
    {
        await positionsUpdater.EditStopLimitAsync(editStopLimitRequest.UserId, editStopLimitRequest.PositionId, editStopLimitRequest.StopLimitPrice);
    }

    public async Task ClosePositionAsync(ClosePositionRequest closePositionRequest)
    {
        await positionsUpdater.ClosePositionAsync(closePositionRequest.UserId, closePositionRequest.PositionId,
            closePositionRequest.ClosePrice, closePositionRequest.CloseTime, closePositionRequest.SharesCount);
    }

    private async Task<List<Achievement>> GetUserAchievementsAsync(string userId)
    {
        var userToAchievements = await achievementsRetriever.GetUserAchievementsAsync(userId);
        var achievements = await achievementsRetriever.GetAchievementsByTypesAsync(userToAchievements
            .Select(userToAchievement => userToAchievement.AchievementType)
            .ToList());
        return achievements;
    }

    private async Task<UserInvestmentStatus> CreateUserInvestmentStatusAsync(UserPositions userPositions, List<Achievement> achievements)
    {
        var userInvestmentStatus = new UserInvestmentStatus
        {
            UserId = userPositions.UserId,
            RiskLevel = userPositions.RiskLevel,
            AccountBalance = userPositions.AccountBalance,
            Positions = userPositions.Positions,
            TotalWorth = await CalculateUserNetWorth(userPositions),
            AchievementsPoints = achievements.Sum(achievement => achievement.PointsNumber),
            AchievementsCount = achievements.Count
        };
        return userInvestmentStatus;
    }

    public async Task<decimal> CalculateUserNetWorth(UserPositions userPositions)
    {
        var totalNetWorth = userPositions.AccountBalance;
        foreach (var position in userPositions.Positions)
        {
            var realTimeStock = await stockPriceRetriever.GetRealTimeStockAsync(position.ShareSymbol);
            var currentInvestment = realTimeStock.CurrentPrice * position.SharesCount;
            var balanceToAdd = position.PositionType == PositionType.Long ? currentInvestment : -currentInvestment;
            totalNetWorth += balanceToAdd;
        }

        return totalNetWorth;
    }

    public async Task<decimal> CalculatePositionChangePercentage(Position position)
    {
        var realTimeStock = await stockPriceRetriever.GetRealTimeStockAsync(position.ShareSymbol);
        var changePercentage =
            StatisticsCalculator.CalculateChangePercentage(position.EntryPrice, realTimeStock.CurrentPrice);
        return position.PositionType == PositionType.Long ? changePercentage : -changePercentage;
    }
}
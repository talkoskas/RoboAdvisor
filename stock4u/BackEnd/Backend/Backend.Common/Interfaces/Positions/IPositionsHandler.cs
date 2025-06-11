using Backend.Common.Models.Positions;

namespace Backend.Common.Interfaces.Positions;

public interface IPositionsHandler
{
    Task<UserInvestmentStatus> GetUserInvestmentStatusAsync(string userId);

    Task<List<UserInvestmentStatus>> GetTopTenUsersAsync();

    Task<IEnumerable<ClosedPosition>> GetUserPositionsHistoryAsync(string userId);

    Task EnterPositionAsync(EnterPositionRequest enterPositionRequest);

    Task EditStopLimitAsync(EditStopLimitRequest editStopLimitRequest);

    Task ClosePositionAsync(ClosePositionRequest closePositionRequest);

    Task<decimal> CalculateUserNetWorth(UserPositions userPositions);

    Task<decimal> CalculatePositionChangePercentage(Position position);
}
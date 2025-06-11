using Backend.Common.Models.Positions;

namespace Backend.Common.Interfaces.Positions;

public interface IPositionsRetriever
{
    Task<UserPositions> GetUserPositionsByIdAsync(string userId);
    
    Task<List<UserPositions>> GetAllUserPositionsAsync();

    Task<List<UserPositionHistory>> GetUserPositionsHistoryAsync(string userId);

    Task<List<UserPositionHistory>> GetNonFeedbackedClosedPositions();
}
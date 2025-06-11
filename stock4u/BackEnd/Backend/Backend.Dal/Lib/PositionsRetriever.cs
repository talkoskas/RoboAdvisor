using Backend.Common.Interfaces.Positions;
using Backend.Common.Models.Positions;
using Backend.Dal.Configuration;
using Backend.Dal.Interfaces;
using Microsoft.Extensions.Logging;
using MongoDB.Driver;
using MongoDB.Driver.Linq;

namespace Backend.Dal.Lib;

public class PositionsRetriever(
    IMongoHandler mongoHandler,
    MongoConfiguration mongoConfiguration,
    ILogger<PositionsRetriever> logger) : IPositionsRetriever
{
    private readonly IMongoCollection<UserPositions> _userInvestmentStatusCollection =
        mongoHandler.GetCollection<UserPositions>(mongoConfiguration.UserPositionsCollectionName);

    private readonly IMongoCollection<UserPositionHistory> _userPositionsHistoryCollection =
        mongoHandler.GetCollection<UserPositionHistory>(mongoConfiguration.UserPositionsHistoryCollectionName);

    public async Task<UserPositions> GetUserPositionsByIdAsync(string userId)
    {
        UserPositions userPositions;
        try
        {
            userPositions = await _userInvestmentStatusCollection.AsQueryable()
                .SingleOrDefaultAsync(positions => positions.UserId == userId);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting user {userId} investment status", userId);
            throw;
        }

        return userPositions;
    }

    public async Task<List<UserPositions>> GetAllUserPositionsAsync()
    {
        List<UserPositions> userPositions;
        try
        {
            userPositions = await _userInvestmentStatusCollection.AsQueryable().ToListAsync();
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting users positions");
            throw;
        }

        return userPositions;
    }

    public async Task<List<UserPositionHistory>> GetUserPositionsHistoryAsync(string userId)
    {
        List<UserPositionHistory> userPositionsHistory;
        try
        {
            userPositionsHistory = await _userPositionsHistoryCollection.AsQueryable()
                .Where(position => position.UserId == userId).ToListAsync();
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting user {userId} positions history", userId);
            throw;
        }

        return userPositionsHistory;
    }

    public async Task<List<UserPositionHistory>> GetNonFeedbackedClosedPositions()
    {
        List<UserPositionHistory> userPositionsHistory;
        try
        {
            userPositionsHistory = await _userPositionsHistoryCollection.AsQueryable()
                .Where(position => position.ClosedPosition.PositionFeedback == PositionFeedback.NoFeedback).ToListAsync();
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error getting non feedbacked positions");
            throw;
        }

        return userPositionsHistory;
    }
}
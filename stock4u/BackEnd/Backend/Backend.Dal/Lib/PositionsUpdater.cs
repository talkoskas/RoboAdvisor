using Backend.Common.Interfaces.Positions;
using Backend.Common.Models.Positions;
using Backend.Dal.Configuration;
using Backend.Dal.Interfaces;
using Microsoft.Extensions.Logging;
using MongoDB.Driver;
using MongoDB.Driver.Linq;

namespace Backend.Dal.Lib;

public class PositionsUpdater(
    IMongoHandler mongoHandler,
    MongoConfiguration mongoConfiguration,
    ILogger<PositionsUpdater> logger) : IPositionsUpdater
{
    private readonly IMongoCollection<UserPositions> _userPositionsCollection =
        mongoHandler.GetCollection<UserPositions>(mongoConfiguration.UserPositionsCollectionName);

    private readonly IMongoCollection<UserPositionHistory> _userPositionsHistoryCollection =
        mongoHandler.GetCollection<UserPositionHistory>(mongoConfiguration.UserPositionsHistoryCollectionName);

    public async Task EnterPositionAsync(string userId, Position position)
    {
        var filter = Builders<UserPositions>.Filter.Eq(up => up.UserId, userId);
        var totalPrice = position.EntryPrice * position.SharesCount;
        var balanceToAdd = position.PositionType == PositionType.Long ? -totalPrice : totalPrice;
        var update = Builders<UserPositions>.Update
            .Push(up => up.Positions, position)
            .Inc(up => up.AccountBalance, balanceToAdd);

        try
        {
            await _userPositionsCollection.UpdateOneAsync(filter, update);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error entering position {@position} for user {userId}", position, userId);
            throw;
        }
    }

    public async Task EditStopLimitAsync(string userId, string positionId, decimal stopLimitPrice)
    {
        var filter = Builders<UserPositions>.Filter.And(Builders<UserPositions>.Filter.Eq(up => up.UserId, userId),
    Builders<UserPositions>.Filter.ElemMatch(up => up.Positions, pos => pos.PositionId == positionId));
        var update = Builders<UserPositions>.Update.Set("Positions.$.StopLimitPrice", stopLimitPrice);

        try
        {
            await _userPositionsCollection.UpdateOneAsync(filter, update);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error entering position {@position} for user {userId}", positionId, userId);
            throw;
        }
    }

    public async Task ClosePositionAsync(string userId, string positionId, decimal closePrice, DateTime closeTime,
        decimal sharesCountToClose)
    {
        var filter = Builders<UserPositions>.Filter.Eq(up => up.UserId, userId);
        var totalPrice = sharesCountToClose * closePrice;
        var currentUser = await _userPositionsCollection.AsQueryable().SingleAsync(user => user.UserId == userId);
        var currentPosition = currentUser.Positions.Single(position => position.PositionId == positionId);
        var update = Builders<UserPositions>.Update.Inc(up => up.AccountBalance, totalPrice);

        if (currentPosition.SharesCount == sharesCountToClose)
        {
            update = update
                .PullFilter(up => up.Positions, p => p.PositionId == positionId);
        }
        else
        {
            filter = Builders<UserPositions>.Filter.And(filter,
                Builders<UserPositions>.Filter.ElemMatch(up => up.Positions, pos => pos.PositionId == positionId));
            update = update.Set("Positions.$.SharesCount", currentPosition.SharesCount - sharesCountToClose);
        }

        try
        {
            await _userPositionsCollection.UpdateOneAsync(filter, update);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error closing position {position} for user {userId}", positionId, userId);
            throw;
        }

        var positionHistory = new UserPositionHistory
        {
            UserId = userId,
            ClosedPosition = new ClosedPosition
            {
                PositionId = positionId,
                ShareSymbol = currentPosition.ShareSymbol,
                ShareCategory = currentPosition.ShareCategory,
                EntryPrice = currentPosition.EntryPrice,
                PositionType = currentPosition.PositionType,
                EntryTime = currentPosition.EntryTime,
                ExitPrice = closePrice,
                ExitTime = closeTime,
                SharesCount = sharesCountToClose,
                PositionFeedback = PositionFeedback.NoFeedback,
                StopLimitPrice = currentPosition.StopLimitPrice
            }
        };

        try
        {
            // todo: update if exists (user closed some shares of same position)?
            await _userPositionsHistoryCollection.InsertOneAsync(positionHistory);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error inserting position {positionId} history for user {userId}", positionId,
                userId);
            throw;
        }
    }

    public async Task SetPositionFeedbackAsync(UserPositionHistory position, PositionFeedback feedback)
    {
        var filter =
            Builders<UserPositionHistory>.Filter.And(
                Builders<UserPositionHistory>.Filter.Eq(p => p.UserId, position.UserId),
                Builders<UserPositionHistory>.Filter.Eq(p => p.ClosedPosition.PositionId,
                    position.ClosedPosition.PositionId),
                Builders<UserPositionHistory>.Filter.Eq(p => p.ClosedPosition.ExitTime,
                    position.ClosedPosition.ExitTime));
        var update = Builders<UserPositionHistory>.Update.Set(p => p.ClosedPosition.PositionFeedback, feedback);

        try
        {
            await _userPositionsHistoryCollection.UpdateOneAsync(filter, update);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error updating position {positionId} feedback for user {userId}",
                position.ClosedPosition.PositionId, position.UserId);
            throw;
        }
    }
}
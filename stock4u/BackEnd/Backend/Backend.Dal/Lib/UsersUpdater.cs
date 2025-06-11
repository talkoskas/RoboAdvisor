using System.ComponentModel.DataAnnotations;
using Backend.Common.Interfaces.Users;
using Backend.Common.Models.Positions;
using Backend.Common.Models.Users;
using Backend.Dal.Configuration;
using Backend.Dal.Interfaces;
using Microsoft.Extensions.Logging;
using MongoDB.Driver;

namespace Backend.Dal.Lib;

public class UsersUpdater(
    IMongoHandler mongoHandler,
    MongoConfiguration mongoConfiguration,
    ILogger<UsersUpdater> logger) : IUsersUpdater
{
    private readonly IMongoCollection<Users> _usersCollection =
        mongoHandler.GetCollection<Users>(mongoConfiguration.UsersCollectionName);

    private readonly IMongoCollection<UserPositions> _userPositionsHistoryCollection =
        mongoHandler.GetCollection<UserPositions>(mongoConfiguration.UserPositionsCollectionName);        

    public async Task RegisterAsync(RegisterUserRequest registerUserRequest)
    {
        var existingUser = await _usersCollection.Find(u => u.UserId == registerUserRequest.UserId).FirstOrDefaultAsync();
        if (existingUser != null)
        {
            logger.LogError("A user with username: {username} already exists.", registerUserRequest.UserId);
            throw new Exception("A user with username: " + registerUserRequest.UserId + " already exists.");
        }
        Users newUser = new Users {
            Email = registerUserRequest.Email,
            UserId = registerUserRequest.UserId,
            Password = registerUserRequest.Password,
            FirstName = registerUserRequest.FirstName,
            LastName = registerUserRequest.LastName,
            RiskLevel = registerUserRequest.RiskLevel
        };
        await _usersCollection.InsertOneAsync(newUser);

        UserPositions newUserPositions = new UserPositions {
            UserId = registerUserRequest.UserId,
            AccountBalance = 1000000,
            RiskLevel = registerUserRequest.RiskLevel,
            Positions = []
        };

        await _userPositionsHistoryCollection.InsertOneAsync(newUserPositions);
    }
}

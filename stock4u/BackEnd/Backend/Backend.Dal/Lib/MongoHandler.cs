using Backend.Dal.Configuration;
using Backend.Dal.Interfaces;
using MongoDB.Driver;

namespace Backend.Dal.Lib;

public class MongoHandler(MongoConfiguration mongoConfiguration) : IMongoHandler
{
    private readonly IMongoDatabase _mongoDatabase =
        new MongoClient(mongoConfiguration.ConnectionString).GetDatabase(mongoConfiguration.DbName);

    public IMongoCollection<T> GetCollection<T>(string collectionName)
    {
        return _mongoDatabase.GetCollection<T>(collectionName);
    }
}
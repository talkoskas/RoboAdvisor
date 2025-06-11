using MongoDB.Driver;

namespace Backend.Dal.Interfaces;

public interface IMongoHandler
{
    IMongoCollection<T> GetCollection<T>(string collectionName);
}
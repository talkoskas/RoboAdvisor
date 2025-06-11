using Backend.Common.Interfaces.Achievements;
using Backend.Common.Interfaces.InvestingAdvisor;
using Backend.Common.Models.Achievements;
using Backend.Common.Models.InvestingAdvisor;
using Backend.Dal.Configuration;
using Backend.Dal.Interfaces;
using Microsoft.Extensions.Logging;
using MongoDB.Bson;
using MongoDB.Driver;

namespace Backend.Dal.Lib;

public class RecommendedStocksUpdater(
    IMongoHandler mongoHandler,
    MongoConfiguration mongoConfiguration,
    ILogger<ReccommendedStocksRetriever> logger) : IRecommendedStocksUpdater
{
    private readonly IMongoCollection<RecommendedStocks> _recommendedStocks =
        mongoHandler.GetCollection<RecommendedStocks>(mongoConfiguration.RecommendedStocks);
    
    public async Task AddRecommendedStockAsync(string symbol, RiskLevel riskLevel)
    {
        var recommendedStock = new RecommendedStocks
        {
            Symbol = symbol,
            RiskLevel = riskLevel
        };
        var filter = Builders<RecommendedStocks>.Filter.Eq(stocks => stocks.Symbol, symbol);
        var options = new ReplaceOptions { IsUpsert = true };
        
        try
        {
            await _recommendedStocks.ReplaceOneAsync(filter, recommendedStock, options);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Error inserting symbol risk to recommended stocks {symbol} {riskLevel}", symbol, riskLevel);
            throw;
        }
    }
}